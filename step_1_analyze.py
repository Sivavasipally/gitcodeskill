#!/usr/bin/env python3
"""
Step 1: Clone & Analyze Repository
Clones/pulls repo, detects tech stack, builds code index, extracts configs.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

try:
    import pathspec
    HAS_PATHSPEC = True
except ImportError:
    HAS_PATHSPEC = False

# ── Cross-platform helpers ──────────────────────────────────────────────────────

def to_posix_rel(path: Path, base: Path) -> str:
    """Return a forward-slash relative path string, safe on Windows and Linux."""
    return path.relative_to(base).as_posix()


# ── Constants ──────────────────────────────────────────────────────────────────

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "build", "dist", "target",
    "venv", ".venv", ".idea", ".vscode", "coverage", ".nyc_output",
    ".gradle", ".m2", "out", "bin", "obj",
}

LANGUAGE_EXTENSIONS = {
    ".java": "Java", ".kt": "Kotlin", ".scala": "Scala",
    ".py": "Python",
    ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".cpp": "C++", ".c": "C", ".cs": "C#",
    ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".less": "LESS",
    ".sql": "SQL", ".sh": "Shell", ".yaml": "YAML", ".yml": "YAML",
    ".json": "JSON", ".xml": "XML", ".proto": "Protobuf",
}

FRAMEWORK_INDICATORS = {
    "Spring Boot": ["pom.xml", "build.gradle", "src/main/resources/application.yml",
                    "src/main/resources/application.properties"],
    "React": ["package.json"],  # refined below by content
    "Angular": ["angular.json"],
    "Vue": ["vue.config.js"],
    "NestJS": ["nest-cli.json"],
    "FastAPI": ["main.py"],  # refined by content
    "Django": ["manage.py"],
    "Flask": ["app.py"],  # refined by content
    "Next.js": ["next.config.js"],
    "Nuxt.js": ["nuxt.config.js"],
    "Svelte": ["svelte.config.js"],
    "Express": ["package.json"],  # refined by content
    "Cargo (Rust)": ["Cargo.toml"],
    "Go Module": ["go.mod"],
    "Gradle": ["build.gradle", "gradlew"],
    "Maven": ["pom.xml"],
    "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
    "npm": ["package.json"],
    "yarn": ["yarn.lock"],
    "pnpm": ["pnpm-lock.yaml"],
}

BUILD_TOOL_FILES = {
    "Maven": ["pom.xml"],
    "Gradle": ["build.gradle", "gradlew"],
    "npm": ["package.json"],
    "yarn": ["yarn.lock"],
    "pnpm": ["pnpm-lock.yaml"],
    "pip": ["requirements.txt", "setup.py"],
    "poetry": ["pyproject.toml"],
    "Cargo": ["Cargo.toml"],
    "Make": ["Makefile"],
    "Docker": ["Dockerfile"],
    "docker-compose": ["docker-compose.yml", "docker-compose.yaml"],
}

ARCH_PATTERNS = {
    "Microservices": ["docker-compose.yml", "kubernetes", "k8s", "helm"],
    "Monorepo": ["lerna.json", "nx.json", "turbo.json", "packages/"],
    "Micro-frontends": ["packages/", "apps/"],
    "API Gateway": ["gateway", "proxy", "nginx.conf"],
    "Event-Driven": ["kafka", "rabbitmq", "event", "message-broker"],
    "MVC": ["controllers/", "models/", "views/"],
    "Layered": ["service/", "repository/", "domain/"],
}

CONFIG_FILES = [
    "application.yml", "application.yaml", "application.properties",
    "appsettings.json", "appsettings.Development.json",
    ".env", ".env.example", ".env.local",
    "config.yml", "config.yaml", "config.json",
    "settings.py", "settings.py",
    "webpack.config.js", "vite.config.js", "vite.config.ts",
    "tsconfig.json", "jest.config.js", "jest.config.ts",
    "Dockerfile", "docker-compose.yml",
]

TEST_FRAMEWORKS = {
    "JUnit": ["*Test.java", "*Tests.java", "src/test/"],
    "pytest": ["test_*.py", "*_test.py", "tests/"],
    "Jest": ["*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts"],
    "Cypress": ["cypress/"],
    "Playwright": ["playwright.config.js", "playwright.config.ts"],
    "TestNG": ["testng.xml"],
    "Mocha": ["*.spec.js", "test/"],
    "RSpec": ["*_spec.rb", "spec/"],
}


# ── Git operations ──────────────────────────────────────────────────────────────

def build_auth_url(url: str, username: str, password: str) -> str:
    """Inject credentials into git URL."""
    if "://" in url:
        scheme, rest = url.split("://", 1)
        return f"{scheme}://{username}:{password}@{rest}"
    return url


def clone_or_pull(repo_url: str, username: str, password: str,
                  workspace: Path, branch: str = "main") -> tuple:
    """Clone or pull repository. Returns (repo_path, log_lines)."""
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = workspace / repo_name
    auth_url = build_auth_url(repo_url, username, password)
    logs = []

    workspace.mkdir(parents=True, exist_ok=True)

    if repo_path.exists() and (repo_path / ".git").exists():
        logs.append(f"Repository exists at {repo_path}, pulling latest...")
        result = subprocess.run(
            ["git", "-C", str(repo_path), "pull", "--ff-only"],
            capture_output=True, text=True, timeout=300
        )
        logs.append(result.stdout.strip())
        if result.returncode != 0:
            logs.append(f"[WARN] Pull failed: {result.stderr.strip()}")
    else:
        logs.append(f"Cloning {repo_url} into {repo_path}...")
        result = subprocess.run(
            ["git", "clone", "--branch", branch, "--depth", "50", auth_url, str(repo_path)],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            # Try without branch
            result = subprocess.run(
                ["git", "clone", "--depth", "50", auth_url, str(repo_path)],
                capture_output=True, text=True, timeout=300
            )
        if result.returncode != 0:
            raise RuntimeError(f"Clone failed: {result.stderr.strip()}")
        logs.append(result.stdout.strip() or "Cloned successfully.")

    return repo_path, logs


def get_git_metadata(repo_path: Path) -> dict:
    def run_git(*args):
        r = subprocess.run(["git", "-C", str(repo_path)] + list(args),
                           capture_output=True, text=True, timeout=30)
        return r.stdout.strip()

    commits_raw = run_git("log", "--oneline", "-10")
    commits = [c for c in commits_raw.split("\n") if c]

    branches_raw = run_git("branch", "-a")
    branches = [b.strip().lstrip("* ") for b in branches_raw.split("\n") if b.strip()]

    remotes_raw = run_git("remote", "-v")
    remotes = list({line.split()[0] for line in remotes_raw.split("\n") if line.strip()})

    current_branch = run_git("rev-parse", "--abbrev-ref", "HEAD")

    return {
        "current_branch": current_branch,
        "recent_commits": commits,
        "branches": branches[:20],
        "remotes": remotes,
    }


# ── File walker ─────────────────────────────────────────────────────────────────

def load_gitignore_spec(repo_path: Path):
    if not HAS_PATHSPEC:
        return None
    gitignore = repo_path / ".gitignore"
    if not gitignore.exists():
        return None
    with open(gitignore, encoding="utf-8", errors="ignore") as f:
        return pathspec.PathSpec.from_lines("gitwildmatch", f)


def should_skip(path: Path, base: Path, spec) -> bool:
    for part in path.relative_to(base).parts:
        if part in SKIP_DIRS:
            return True
    if spec:
        try:
            # pathspec requires forward-slash paths on all platforms
            rel = to_posix_rel(path, base)
            if spec.match_file(rel):
                return True
        except Exception:
            pass
    return False


def walk_files(repo_path: Path):
    spec = load_gitignore_spec(repo_path)
    for root, dirs, files in os.walk(repo_path):
        root_path = Path(root)
        # Prune skip dirs in-place
        dirs[:] = [d for d in dirs
                   if d not in SKIP_DIRS
                   and not should_skip(root_path / d, repo_path, spec)]
        for fname in files:
            fpath = root_path / fname
            if not should_skip(fpath, repo_path, spec):
                yield fpath


# ── Tech stack detection ────────────────────────────────────────────────────────

def detect_languages(repo_path: Path, all_files: list) -> dict:
    counts = defaultdict(int)
    for fp in all_files:
        lang = LANGUAGE_EXTENSIONS.get(fp.suffix.lower())
        if lang:
            counts[lang] += 1
    total = sum(counts.values()) or 1
    return {lang: {"count": cnt, "percent": round(cnt / total * 100, 1)}
            for lang, cnt in sorted(counts.items(), key=lambda x: -x[1])}


def detect_frameworks(repo_path: Path, all_files: list) -> list:
    file_set = {to_posix_rel(fp, repo_path) for fp in all_files}
    file_names = {fp.name for fp in all_files}
    found = []

    for fw, indicators in FRAMEWORK_INDICATORS.items():
        for ind in indicators:
            if ind in file_names or ind in file_set:
                # Refine package.json frameworks
                if ind == "package.json" and fw in ("React", "Express", "npm"):
                    pkg = repo_path / "package.json"
                    if pkg.exists():
                        try:
                            content = pkg.read_text(encoding="utf-8", errors="ignore")
                            if fw == "React" and '"react"' in content:
                                found.append(fw)
                            elif fw == "Express" and '"express"' in content:
                                found.append(fw)
                            elif fw == "npm":
                                found.append(fw)
                        except Exception:
                            pass
                    break
                # Refine FastAPI/Flask
                elif ind == "main.py" and fw == "FastAPI":
                    try:
                        content = (repo_path / "main.py").read_text(encoding="utf-8", errors="ignore")
                        if "fastapi" in content.lower():
                            found.append(fw)
                    except Exception:
                        pass
                    break
                elif ind == "app.py" and fw == "Flask":
                    try:
                        content = (repo_path / "app.py").read_text(encoding="utf-8", errors="ignore")
                        if "flask" in content.lower():
                            found.append(fw)
                    except Exception:
                        pass
                    break
                else:
                    found.append(fw)
                    break

    return list(dict.fromkeys(found))  # deduplicate preserving order


def detect_build_tools(repo_path: Path, all_files: list) -> list:
    file_names = {fp.name for fp in all_files}
    found = []
    for tool, indicators in BUILD_TOOL_FILES.items():
        for ind in indicators:
            if ind in file_names:
                found.append(tool)
                break
    return list(dict.fromkeys(found))


def detect_architecture(repo_path: Path, all_files: list) -> list:
    file_set = {to_posix_rel(fp, repo_path).lower() for fp in all_files}
    dir_set = set()
    for fp in all_files:
        for part in fp.relative_to(repo_path).parts[:-1]:
            dir_set.add(part.lower())

    patterns = []
    for pattern, signals in ARCH_PATTERNS.items():
        for sig in signals:
            # Strip both slash variants so patterns match on Windows and Linux
            sig_l = sig.lower().rstrip("/").rstrip("\\")
            if (sig_l in dir_set or
                    any(sig_l in f for f in file_set)):
                patterns.append(pattern)
                break

    # Heuristic: multiple service directories suggest microservices
    service_dirs = [d for d in dir_set if any(
        d.endswith(x) for x in ["-service", "-api", "-gateway", "service", "microservice"]
    )]
    if len(service_dirs) >= 3 and "Microservices" not in patterns:
        patterns.append("Microservices")

    return list(dict.fromkeys(patterns)) if patterns else ["Monolith"]


def detect_tests(repo_path: Path, all_files: list) -> dict:
    file_names = {fp.name for fp in all_files}
    dir_parts = set()
    for fp in all_files:
        for part in fp.relative_to(repo_path).parts:
            dir_parts.add(part.lower())

    found = {}
    test_file_count = 0

    for fw, patterns in TEST_FRAMEWORKS.items():
        for pat in patterns:
            if pat.endswith("/"):
                if pat.rstrip("/").lower() in dir_parts:
                    found[fw] = pat.rstrip("/")
                    break
            else:
                for fn in file_names:
                    if re.match(pat.replace("*", ".*").replace(".", "\\."), fn):
                        found[fw] = pat
                        break

    # Count test files
    test_markers = ["test", "spec", "__tests__"]
    for fp in all_files:
        rel = to_posix_rel(fp, repo_path).lower()
        if any(m in rel for m in test_markers):
            test_file_count += 1

    return {"frameworks": found, "test_file_count": test_file_count}


# ── Code indexing ───────────────────────────────────────────────────────────────

JAVA_PATTERNS = {
    "classes": re.compile(r"(?:public\s+)?(?:abstract\s+)?(?:final\s+)?(?:class|interface|enum)\s+(\w+)"),
    "methods": re.compile(r"(?:public|protected|private|static|final|synchronized|\s)+\s+\w[\w<>,\[\]]*\s+(\w+)\s*\("),
    "endpoints": re.compile(r'@(?:RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'),
    "entities": re.compile(r"@(?:Entity|Table)\s"),
}

PYTHON_PATTERNS = {
    "classes": re.compile(r"^class\s+(\w+)", re.MULTILINE),
    "functions": re.compile(r"^def\s+(\w+)\s*\(", re.MULTILINE),
    "flask_routes": re.compile(r'@(?:app|bp|blueprint)\.route\s*\(\s*["\']([^"\']+)["\']'),
    "fastapi_routes": re.compile(r'@(?:app|router)\.\s*(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'),
}

JS_TS_PATTERNS = {
    "classes": re.compile(r"(?:^|\s)class\s+(\w+)"),
    "functions": re.compile(r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(|(\w+)\s*:\s*(?:async\s*)?\()"),
    "express_routes": re.compile(r'(?:app|router)\.\s*(?:get|post|put|delete|patch|use)\s*\(\s*["\']([^"\']+)["\']'),
    "interfaces": re.compile(r"(?:^|\s)interface\s+(\w+)"),
}


def read_file_safe(fp: Path, max_bytes: int = 500_000) -> str:
    try:
        with open(fp, "rb") as f:
            raw = f.read(max_bytes)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def index_java_file(fp: Path, content: str, rel_path: str, index: dict) -> None:
    for m in JAVA_PATTERNS["classes"].finditer(content):
        index["classes"].append({"name": m.group(1), "file": rel_path,
                                  "line": content[:m.start()].count("\n") + 1})
    for m in JAVA_PATTERNS["endpoints"].finditer(content):
        index["api_endpoints"].append({"path": m.group(1), "file": rel_path,
                                        "line": content[:m.start()].count("\n") + 1})
    if JAVA_PATTERNS["entities"].search(content):
        # Find class name near @Entity
        for m in re.finditer(r"@(?:Entity|Table)[\s\S]{0,200}?class\s+(\w+)", content):
            index["db_entities"].append({"name": m.group(1), "file": rel_path})


def index_python_file(fp: Path, content: str, rel_path: str, index: dict) -> None:
    for m in PYTHON_PATTERNS["classes"].finditer(content):
        index["classes"].append({"name": m.group(1), "file": rel_path,
                                  "line": content[:m.start()].count("\n") + 1})
    for m in PYTHON_PATTERNS["functions"].finditer(content):
        index["functions"].append({"name": m.group(1), "file": rel_path,
                                    "line": content[:m.start()].count("\n") + 1})
    for m in PYTHON_PATTERNS["flask_routes"].finditer(content):
        index["api_endpoints"].append({"path": m.group(1), "file": rel_path})
    for m in PYTHON_PATTERNS["fastapi_routes"].finditer(content):
        index["api_endpoints"].append({"path": m.group(1), "file": rel_path})


def index_js_ts_file(fp: Path, content: str, rel_path: str, index: dict) -> None:
    for m in JS_TS_PATTERNS["classes"].finditer(content):
        index["classes"].append({"name": m.group(1), "file": rel_path,
                                  "line": content[:m.start()].count("\n") + 1})
    for m in JS_TS_PATTERNS["interfaces"].finditer(content):
        index["interfaces"].append({"name": m.group(1), "file": rel_path})
    for m in JS_TS_PATTERNS["functions"].finditer(content):
        name = m.group(1) or m.group(2) or m.group(3)
        if name and len(name) > 1:
            index["functions"].append({"name": name, "file": rel_path,
                                        "line": content[:m.start()].count("\n") + 1})
    for m in JS_TS_PATTERNS["express_routes"].finditer(content):
        index["api_endpoints"].append({"path": m.group(1), "file": rel_path})


def build_code_index(repo_path: Path, all_files: list) -> dict:
    index = defaultdict(list)
    index["classes"] = []
    index["functions"] = []
    index["api_endpoints"] = []
    index["db_entities"] = []
    index["interfaces"] = []

    for fp in all_files:
        ext = fp.suffix.lower()
        rel = to_posix_rel(fp, repo_path)
        content = read_file_safe(fp)
        if not content:
            continue

        if ext == ".java":
            index_java_file(fp, content, rel, index)
        elif ext == ".py":
            index_python_file(fp, content, rel, index)
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            index_js_ts_file(fp, content, rel, index)

    return dict(index)


# ── Config extraction ───────────────────────────────────────────────────────────

def extract_configs(repo_path: Path, all_files: list) -> dict:
    configs = {}
    env_vars = []
    file_names = {fp.name: fp for fp in all_files}

    for cfg_name in CONFIG_FILES:
        if cfg_name in file_names:
            fp = file_names[cfg_name]
            rel = to_posix_rel(fp, repo_path)
            content = read_file_safe(fp, max_bytes=10_000)
            configs[rel] = content[:2000] if len(content) > 2000 else content

            # Extract .env vars
            if fp.name.startswith(".env"):
                for line in content.split("\n"):
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key = line.split("=", 1)[0].strip()
                        env_vars.append(key)

    return {"config_files": configs, "env_variables": list(set(env_vars))}


# ── Directory tree ──────────────────────────────────────────────────────────────

def build_dir_tree(repo_path: Path, max_depth: int = 3) -> dict:
    def recurse(path: Path, depth: int) -> dict:
        if depth > max_depth:
            return {}
        node = {"type": "dir", "children": {}}
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return node
        for entry in entries:
            if entry.name in SKIP_DIRS or entry.name.startswith("."):
                continue
            if entry.is_dir():
                node["children"][entry.name] = recurse(entry, depth + 1)
            else:
                node["children"][entry.name] = {"type": "file"}
        return node

    return recurse(repo_path, 1)


# ── Main analysis ───────────────────────────────────────────────────────────────

def analyze(repo_path: Path, logs: list) -> dict:
    logs.append("Scanning repository files...")
    all_files = list(walk_files(repo_path))
    logs.append(f"Found {len(all_files)} files.")

    logs.append("Detecting languages...")
    languages = detect_languages(repo_path, all_files)

    logs.append("Detecting frameworks...")
    frameworks = detect_frameworks(repo_path, all_files)

    logs.append("Detecting build tools...")
    build_tools = detect_build_tools(repo_path, all_files)

    logs.append("Detecting architecture patterns...")
    architecture = detect_architecture(repo_path, all_files)

    logs.append("Building code index...")
    code_index = build_code_index(repo_path, all_files)

    logs.append("Extracting configurations...")
    configs = extract_configs(repo_path, all_files)

    logs.append("Detecting test setup...")
    tests = detect_tests(repo_path, all_files)

    logs.append("Generating directory tree...")
    dir_tree = build_dir_tree(repo_path)

    logs.append("Fetching git metadata...")
    try:
        git_meta = get_git_metadata(repo_path)
    except Exception as e:
        git_meta = {"error": str(e)}

    report = {
        "repo_path": str(repo_path),
        "total_files": len(all_files),
        "languages": languages,
        "frameworks": frameworks,
        "build_tools": build_tools,
        "architecture": architecture,
        "code_index": code_index,
        "configurations": configs,
        "tests": tests,
        "directory_tree": dir_tree,
        "git": git_meta,
        "stats": {
            "total_classes": len(code_index.get("classes", [])),
            "total_functions": len(code_index.get("functions", [])),
            "total_api_endpoints": len(code_index.get("api_endpoints", [])),
            "total_db_entities": len(code_index.get("db_entities", [])),
            "total_interfaces": len(code_index.get("interfaces", [])),
            "test_files": tests.get("test_file_count", 0),
        },
    }
    return report


def remove_repo(repo_path: Path, logs: list) -> None:
    """Remove a cloned repository directory from local disk."""
    import shutil
    try:
        shutil.rmtree(repo_path)
        logs.append(f"[CLEANUP] Removed local clone: {repo_path}")
    except Exception as e:
        logs.append(f"[WARN] Could not remove {repo_path}: {e}")


def analyze_single(
    repo_url: str,
    username: str,
    password: str,
    branch: str,
    workspace: Path,
    cleanup: bool = True,
    local_path: str = None,
) -> dict:
    """Clone (or use local path), analyze, optionally remove. Returns report dict."""
    logs = []
    if local_path:
        repo_path = Path(local_path)
        if not repo_path.exists():
            raise FileNotFoundError(f"Path not found: {repo_path}")
        logs.append(f"Analyzing local path: {repo_path}")
    else:
        repo_path, clone_logs = clone_or_pull(repo_url, username, password, workspace, branch)
        logs.extend(clone_logs)

    report = analyze(repo_path, logs)
    report["logs"] = logs

    if cleanup and not local_path:
        remove_repo(repo_path, logs)

    return report


def multi_repo_scan(
    repos: list,
    username: str,
    password: str,
    branch: str,
    workspace: Path,
    output_path: Path,
    cleanup: bool = True,
) -> dict:
    """
    Iterate repos list, clone→analyze→remove each repo.

    repos: list of dicts with at least { "clone_url": str, "name": str }
    Returns aggregated multi_analysis_report dict.
    """
    results = []
    total = len(repos)
    failed = []

    for idx, repo in enumerate(repos, 1):
        repo_url = repo.get("clone_url", "")
        repo_name = repo.get("name", repo_url.split("/")[-1].replace(".git", ""))
        repo_branch = repo.get("default_branch", branch)

        print(f"\n[{idx}/{total}] Processing: {repo_name} ({repo_url})")

        try:
            report = analyze_single(
                repo_url=repo_url,
                username=username,
                password=password,
                branch=repo_branch,
                workspace=workspace,
                cleanup=cleanup,
            )
            report["repo_name"] = repo_name
            report["repo_url"] = repo_url
            results.append(report)
            print(f"  [OK] Files: {report['total_files']}, "
                  f"Classes: {report['stats']['total_classes']}, "
                  f"Functions: {report['stats']['total_functions']}, "
                  f"Endpoints: {report['stats']['total_api_endpoints']}")
        except Exception as e:
            print(f"  [ERROR] {e}", file=sys.stderr)
            failed.append({"repo_name": repo_name, "repo_url": repo_url, "error": str(e)})

    # Aggregate totals
    agg = {
        "scan_type": "multi_repo",
        "total_repos_attempted": total,
        "total_repos_succeeded": len(results),
        "total_repos_failed": len(failed),
        "failed_repos": failed,
        "repos": results,
        "aggregate_stats": {
            "total_files": sum(r.get("total_files", 0) for r in results),
            "total_classes": sum(r.get("stats", {}).get("total_classes", 0) for r in results),
            "total_functions": sum(r.get("stats", {}).get("total_functions", 0) for r in results),
            "total_api_endpoints": sum(r.get("stats", {}).get("total_api_endpoints", 0) for r in results),
            "total_db_entities": sum(r.get("stats", {}).get("total_db_entities", 0) for r in results),
            "test_files": sum(r.get("stats", {}).get("test_files", 0) for r in results),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)

    print(f"\n[OK] Multi-repo scan complete.")
    print(f"     Repos: {len(results)} succeeded, {len(failed)} failed.")
    print(f"     Report saved to {output_path}")

    return agg


def resolve_repo_path(path: Path, logs: list) -> Path:
    """
    If `path` has no .git directory, check whether it contains exactly one
    subdirectory that IS a git repo and use that instead.  This handles the
    common mistake of supplying the workspace/clone-parent folder rather than
    the actual repo root.
    """
    if (path / ".git").exists():
        return path  # already a repo root

    git_subdirs = [
        d for d in path.iterdir()
        if d.is_dir() and (d / ".git").exists()
    ]
    if len(git_subdirs) == 1:
        logs.append(
            f"[INFO] '{path}' is not a git repo root. "
            f"Auto-selected subfolder: {git_subdirs[0]}"
        )
        return git_subdirs[0]
    elif len(git_subdirs) > 1:
        logs.append(
            f"[WARN] Multiple git repos found inside '{path}'. "
            f"Using first: {git_subdirs[0]}. "
            f"Pass the exact repo subfolder path to avoid ambiguity."
        )
        return git_subdirs[0]

    # No .git found at all — proceed with original path; analysis will return
    # whatever files are there (may legitimately be a non-git codebase).
    return path


def main():
    from step_0_setup import load_config

    parser = argparse.ArgumentParser(description="Clone & analyze a Git repository (Bitbucket or GitHub)")
    parser.add_argument("--repo-url", help="Repository URL (overrides config)")
    parser.add_argument("--username", help="Git username (overrides config)")
    parser.add_argument("--password", help="Git password / token (overrides config)")
    parser.add_argument("--branch", default=None, help="Branch to clone")
    parser.add_argument("--workspace-dir", help="Workspace directory")
    parser.add_argument("--output", default="analysis_report.json", help="Output JSON path")
    parser.add_argument("--local-path", help="Skip clone, analyze existing local path (repo root or workspace dir)")

    # ── Multi-repo scan ──────────────────────────────────────────────────────────
    parser.add_argument(
        "--multi-repo", action="store_true",
        help="Scan multiple repos (GitHub owner or Bitbucket project key(s))"
    )
    parser.add_argument(
        "--github-owner",
        help="GitHub user/org whose repos to scan (--multi-repo mode)"
    )
    parser.add_argument(
        "--project-keys", nargs="+",
        help="Bitbucket project key(s) to scan (--multi-repo mode)"
    )
    parser.add_argument(
        "--no-cleanup", action="store_true",
        help="Keep cloned repos on disk after analysis (default: remove them)"
    )
    parser.add_argument(
        "--multi-output", default="multi_analysis_report.json",
        help="Output JSON path for multi-repo scan"
    )

    args = parser.parse_args()

    config = load_config()
    # Support both new unified keys and old bitbucket-specific keys for backward compat
    repo_url = (args.repo_url or
                config.get("repo_url", config.get("bitbucket_url", "")))
    username = (args.username or
                config.get("git_username", config.get("bitbucket_username", "")))
    password = (args.password or
                config.get("git_password", config.get("bitbucket_password", "")))
    branch = (args.branch or
              config.get("git_branch", config.get("bitbucket_branch", "main")))
    workspace = Path(args.workspace_dir or config.get("workspace_dir", str(Path.home() / "dev-workspace")))

    # ── Multi-repo mode ──────────────────────────────────────────────────────────
    if args.multi_repo:
        from repo_discovery import discover_repos
        project_keys = args.project_keys or config.get("project_keys", [])
        github_owner = args.github_owner or config.get("github_owner", "")
        try:
            repos = discover_repos(
                config,
                project_keys=project_keys if project_keys else None,
                github_owner=github_owner if github_owner else None,
            )
        except Exception as e:
            print(f"[ERROR] Failed to discover repos: {e}", file=sys.stderr)
            sys.exit(1)

        if not repos:
            print("[WARN] No repositories found. Check project keys / owner name.", file=sys.stderr)
            sys.exit(0)

        print(f"[INFO] Discovered {len(repos)} repositories. Starting scan...")

        multi_repo_scan(
            repos=repos,
            username=username,
            password=password,
            branch=branch,
            workspace=workspace,
            output_path=Path(args.multi_output),
            cleanup=not args.no_cleanup,
        )
        return

    # ── Single-repo mode (original behaviour) ───────────────────────────────────
    logs = []

    if args.local_path:
        repo_path = Path(args.local_path)
        if not repo_path.exists():
            print(f"[ERROR] Path not found: {repo_path}", file=sys.stderr)
            sys.exit(1)
        repo_path = resolve_repo_path(repo_path, logs)
        logs.append(f"Analyzing local path: {repo_path}")
    else:
        if not repo_url:
            print("[ERROR] Repository URL required. Run step_0_setup.py first.", file=sys.stderr)
            sys.exit(1)
        repo_path, clone_logs = clone_or_pull(repo_url, username, password, workspace, branch)
        logs.extend(clone_logs)

    report = analyze(repo_path, logs)
    report["logs"] = logs

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Analysis report saved to {output_path}")
    print(f"     Files: {report['total_files']}, "
          f"Classes: {report['stats']['total_classes']}, "
          f"Functions: {report['stats']['total_functions']}, "
          f"API Endpoints: {report['stats']['total_api_endpoints']}")


if __name__ == "__main__":
    main()
