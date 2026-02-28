#!/usr/bin/env python3
"""
Claude.md Initializer for Multiple Repositories
=================================================
Scans a directory of cloned repositories, detects each repo's tech stack,
and generates a tailored CLAUDE.md file for each one.

Usage:
    python claude_md_initializer.py --repos-dir /path/to/repos
    python claude_md_initializer.py --repos-dir /path/to/repos --dry-run
    python claude_md_initializer.py --repos-dir /path/to/repos --force
    python claude_md_initializer.py --repos-dir /path/to/repos --root-claude-md
"""

import os
import json
import argparse
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────────────────────
# Configuration & Constants
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Tech-stack detection rules: filename/pattern → technology tag
DETECTION_RULES: dict[str, list[str]] = {
    # ── JavaScript / TypeScript ──
    "package.json":           ["node"],
    "tsconfig.json":          ["typescript"],
    "next.config.js":         ["nextjs"],
    "next.config.mjs":        ["nextjs"],
    "next.config.ts":         ["nextjs"],
    "nuxt.config.ts":         ["nuxt", "vue"],
    "nuxt.config.js":         ["nuxt", "vue"],
    "angular.json":           ["angular"],
    "vite.config.ts":         ["vite"],
    "vite.config.js":         ["vite"],
    "webpack.config.js":      ["webpack"],
    "tailwind.config.js":     ["tailwind"],
    "tailwind.config.ts":     ["tailwind"],
    ".eslintrc.js":           ["eslint"],
    ".eslintrc.json":         ["eslint"],
    "jest.config.js":         ["jest"],
    "jest.config.ts":         ["jest"],
    "vitest.config.ts":       ["vitest"],
    "playwright.config.ts":   ["playwright"],
    "cypress.json":           ["cypress"],
    "cypress.config.ts":      ["cypress"],

    # ── Python ──
    "requirements.txt":       ["python"],
    "pyproject.toml":         ["python"],
    "setup.py":               ["python"],
    "Pipfile":                ["python", "pipenv"],
    "poetry.lock":            ["python", "poetry"],
    "manage.py":              ["python", "django"],
    "app.py":                 ["python", "flask"],

    # ── Java / JVM ──
    "pom.xml":                ["java", "maven"],
    "build.gradle":           ["java", "gradle"],
    "build.gradle.kts":       ["kotlin", "gradle"],

    # ── .NET ──
    "*.csproj":               ["dotnet", "csharp"],
    "*.sln":                  ["dotnet"],

    # ── Go ──
    "go.mod":                 ["golang"],
    "go.sum":                 ["golang"],

    # ── Rust ──
    "Cargo.toml":             ["rust"],

    # ── Ruby ──
    "Gemfile":                ["ruby"],
    "Rakefile":               ["ruby"],
    "config.ru":              ["ruby", "rack"],

    # ── PHP ──
    "composer.json":          ["php"],
    "artisan":                ["php", "laravel"],

    # ── Infrastructure / DevOps ──
    "Dockerfile":             ["docker"],
    "docker-compose.yml":     ["docker", "docker-compose"],
    "docker-compose.yaml":    ["docker", "docker-compose"],
    "Jenkinsfile":            ["jenkins"],
    ".github/workflows":      ["github-actions"],
    "Makefile":               ["make"],
    "Terraform":              ["terraform"],
    "main.tf":                ["terraform"],
    "helm":                   ["helm"],
    "Chart.yaml":             ["helm"],
    "serverless.yml":         ["serverless"],
    "serverless.yaml":        ["serverless"],
    "k8s":                    ["kubernetes"],
    "kubernetes":             ["kubernetes"],

    # ── Database / Migrations ──
    "flyway":                 ["flyway"],
    "liquibase":              ["liquibase"],
    "prisma":                 ["prisma"],
    "drizzle.config.ts":      ["drizzle"],
    "alembic.ini":            ["alembic", "sqlalchemy"],

    # ── AI / ML ──
    "langchain":              ["langchain"],
    "chromadb":               ["chromadb"],
    "notebooks":              ["jupyter"],
    ".ipynb":                 ["jupyter"],
}

# Additional detection from package.json dependencies
PACKAGE_JSON_DETECTIONS: dict[str, list[str]] = {
    "react":                  ["react"],
    "react-dom":              ["react"],
    "vue":                    ["vue"],
    "svelte":                 ["svelte"],
    "@angular/core":          ["angular"],
    "express":                ["express"],
    "fastify":                ["fastify"],
    "nestjs":                 ["nestjs"],
    "@nestjs/core":           ["nestjs"],
    "prisma":                 ["prisma"],
    "drizzle-orm":            ["drizzle"],
    "mongoose":               ["mongodb", "mongoose"],
    "langchain":              ["langchain"],
    "zustand":                ["zustand"],
    "redux":                  ["redux"],
    "@reduxjs/toolkit":       ["redux"],
    "react-query":            ["react-query"],
    "@tanstack/react-query":  ["react-query"],
    "tailwindcss":            ["tailwind"],
    "shadcn":                 ["shadcn"],
    "storybook":              ["storybook"],
}

# Additional detection from requirements.txt / pyproject.toml
PYTHON_DETECTIONS: dict[str, list[str]] = {
    "django":                 ["django"],
    "flask":                  ["flask"],
    "fastapi":                ["fastapi"],
    "langchain":              ["langchain"],
    "chromadb":               ["chromadb"],
    "faiss":                  ["faiss"],
    "pandas":                 ["pandas"],
    "numpy":                  ["numpy"],
    "scikit-learn":           ["sklearn"],
    "torch":                  ["pytorch"],
    "tensorflow":             ["tensorflow"],
    "transformers":           ["huggingface"],
    "sqlalchemy":             ["sqlalchemy"],
    "alembic":                ["alembic"],
    "celery":                 ["celery"],
    "pytest":                 ["pytest"],
    "streamlit":              ["streamlit"],
    "gradio":                 ["gradio"],
}

# Spring Boot detection from pom.xml / build.gradle
JAVA_DETECTIONS: dict[str, list[str]] = {
    "spring-boot":            ["spring-boot"],
    "spring-cloud":           ["spring-cloud"],
    "spring-security":        ["spring-security"],
    "spring-data":            ["spring-data"],
    "mybatis":                ["mybatis"],
    "kafka":                  ["kafka"],
    "flyway":                 ["flyway"],
    "liquibase":              ["liquibase"],
    "junit":                  ["junit"],
    "mockito":                ["mockito"],
}


# ─────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────

@dataclass
class RepoInfo:
    """Holds detected information about a repository."""
    name: str
    path: Path
    tech_tags: set = field(default_factory=set)
    primary_language: str = "unknown"
    framework: str = "unknown"
    has_tests: bool = False
    has_docker: bool = False
    has_ci: bool = False
    has_db_migrations: bool = False
    folder_structure: list = field(default_factory=list)
    build_commands: dict = field(default_factory=dict)
    description: str = ""


# ─────────────────────────────────────────────────────────────
# Detection Logic
# ─────────────────────────────────────────────────────────────

def detect_tech_stack(repo_path: Path) -> RepoInfo:
    """Scan a repository and detect its tech stack."""
    info = RepoInfo(name=repo_path.name, path=repo_path)

    # 1) File/directory-based detection
    for pattern, tags in DETECTION_RULES.items():
        if pattern.startswith("*"):
            # Glob pattern (e.g., *.csproj)
            if list(repo_path.glob(pattern)):
                info.tech_tags.update(tags)
        else:
            target = repo_path / pattern
            if target.exists():
                info.tech_tags.update(tags)

    # 2) Deep-scan package.json
    pkg_json = repo_path / "package.json"
    if pkg_json.exists():
        _scan_package_json(pkg_json, info)

    # 3) Deep-scan Python deps
    req_txt = repo_path / "requirements.txt"
    if req_txt.exists():
        _scan_requirements_txt(req_txt, info)

    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        _scan_pyproject_toml(pyproject, info)

    # 4) Deep-scan Java/Gradle/Maven
    pom = repo_path / "pom.xml"
    if pom.exists():
        _scan_pom_xml(pom, info)

    build_gradle = repo_path / "build.gradle"
    if not build_gradle.exists():
        build_gradle = repo_path / "build.gradle.kts"
    if build_gradle.exists():
        _scan_build_gradle(build_gradle, info)

    # 5) Detect test directories
    test_dirs = ["test", "tests", "__tests__", "spec", "src/test", "src/tests"]
    info.has_tests = any((repo_path / d).is_dir() for d in test_dirs)

    # 6) Infer primary language & framework
    info.primary_language = _infer_primary_language(info.tech_tags)
    info.framework = _infer_framework(info.tech_tags)
    info.has_docker = "docker" in info.tech_tags
    info.has_ci = "github-actions" in info.tech_tags or "jenkins" in info.tech_tags
    info.has_db_migrations = bool(info.tech_tags & {"flyway", "alembic", "prisma", "drizzle", "liquibase"})

    # 7) Capture top-level folder structure
    info.folder_structure = _get_folder_structure(repo_path)

    # 8) Infer build commands
    info.build_commands = _infer_build_commands(info)

    # 9) Try reading existing description (README first line, etc.)
    info.description = _read_description(repo_path)

    return info


def _scan_package_json(path: Path, info: RepoInfo):
    """Parse package.json and detect frontend/backend frameworks."""
    try:
        with open(path) as f:
            data = json.load(f)

        all_deps = {}
        all_deps.update(data.get("dependencies", {}))
        all_deps.update(data.get("devDependencies", {}))

        for dep, tags in PACKAGE_JSON_DETECTIONS.items():
            if dep in all_deps:
                info.tech_tags.update(tags)

        # Capture scripts for build commands
        scripts = data.get("scripts", {})
        if "dev" in scripts:
            info.build_commands["dev"] = f"npm run dev"
        if "build" in scripts:
            info.build_commands["build"] = f"npm run build"
        if "test" in scripts:
            info.build_commands["test"] = f"npm run test"
            info.has_tests = True
        if "lint" in scripts:
            info.build_commands["lint"] = f"npm run lint"
        if "start" in scripts:
            info.build_commands["start"] = f"npm start"

        # Description
        if data.get("description"):
            info.description = data["description"]

    except (json.JSONDecodeError, IOError):
        pass


def _scan_requirements_txt(path: Path, info: RepoInfo):
    """Parse requirements.txt for Python library detection."""
    try:
        content = path.read_text().lower()
        for lib, tags in PYTHON_DETECTIONS.items():
            if lib.lower() in content:
                info.tech_tags.update(tags)
    except IOError:
        pass


def _scan_pyproject_toml(path: Path, info: RepoInfo):
    """Simple scan of pyproject.toml for dependency detection."""
    try:
        content = path.read_text().lower()
        for lib, tags in PYTHON_DETECTIONS.items():
            if lib.lower() in content:
                info.tech_tags.update(tags)
    except IOError:
        pass


def _scan_pom_xml(path: Path, info: RepoInfo):
    """Simple text-based scan of pom.xml."""
    try:
        content = path.read_text().lower()
        for lib, tags in JAVA_DETECTIONS.items():
            if lib.lower() in content:
                info.tech_tags.update(tags)
    except IOError:
        pass


def _scan_build_gradle(path: Path, info: RepoInfo):
    """Simple text-based scan of build.gradle(.kts)."""
    try:
        content = path.read_text().lower()
        for lib, tags in JAVA_DETECTIONS.items():
            if lib.lower() in content:
                info.tech_tags.update(tags)
    except IOError:
        pass


def _infer_primary_language(tags: set) -> str:
    """Determine the primary programming language."""
    lang_priority = [
        ({"typescript"},  "TypeScript"),
        ({"react", "node"}, "JavaScript/TypeScript"),
        ({"node"},        "JavaScript"),
        ({"python"},      "Python"),
        ({"java"},        "Java"),
        ({"kotlin"},      "Kotlin"),
        ({"golang"},      "Go"),
        ({"rust"},        "Rust"),
        ({"ruby"},        "Ruby"),
        ({"php"},         "PHP"),
        ({"dotnet", "csharp"}, "C#"),
        ({"dotnet"},      ".NET"),
        ({"terraform"},   "HCL (Terraform)"),
    ]
    for required, language in lang_priority:
        if required & tags:
            return language
    return "Unknown"


def _infer_framework(tags: set) -> str:
    """Determine the primary framework."""
    fw_priority = [
        ({"nextjs"},        "Next.js"),
        ({"nuxt"},          "Nuxt.js"),
        ({"angular"},       "Angular"),
        ({"react"},         "React"),
        ({"vue"},           "Vue.js"),
        ({"svelte"},        "Svelte"),
        ({"nestjs"},        "NestJS"),
        ({"express"},       "Express.js"),
        ({"fastify"},       "Fastify"),
        ({"spring-boot"},   "Spring Boot"),
        ({"django"},        "Django"),
        ({"flask"},         "Flask"),
        ({"fastapi"},       "FastAPI"),
        ({"streamlit"},     "Streamlit"),
        ({"laravel"},       "Laravel"),
        ({"ruby", "rack"},  "Ruby on Rails / Rack"),
    ]
    for required, fw in fw_priority:
        if required & tags:
            return fw
    return "N/A"


def _get_folder_structure(repo_path: Path, max_depth: int = 2) -> list[str]:
    """Get top-level folder structure (up to max_depth)."""
    folders = []
    try:
        for item in sorted(repo_path.iterdir()):
            if item.name.startswith(".") or item.name in ("node_modules", "__pycache__", ".git", "venv", ".venv", "dist", "build", "target"):
                continue
            if item.is_dir():
                folders.append(f"{item.name}/")
                if max_depth > 1:
                    for sub in sorted(item.iterdir()):
                        if sub.name.startswith(".") or sub.name in ("node_modules", "__pycache__"):
                            continue
                        if sub.is_dir():
                            folders.append(f"  {sub.name}/")
            elif item.is_file() and item.name in (
                "package.json", "pom.xml", "build.gradle", "requirements.txt",
                "Dockerfile", "Makefile", "go.mod", "Cargo.toml", "pyproject.toml",
            ):
                folders.append(item.name)
    except PermissionError:
        pass
    return folders


def _infer_build_commands(info: RepoInfo) -> dict:
    """Infer build/run/test commands based on detected tech."""
    cmds = dict(info.build_commands)  # preserve already-detected commands

    tags = info.tech_tags

    if "java" in tags or "kotlin" in tags:
        if "gradle" in tags:
            cmds.setdefault("build", "./gradlew build")
            cmds.setdefault("test", "./gradlew test")
            cmds.setdefault("run", "./gradlew bootRun" if "spring-boot" in tags else "./gradlew run")
        elif "maven" in tags:
            cmds.setdefault("build", "mvn clean package")
            cmds.setdefault("test", "mvn test")
            cmds.setdefault("run", "mvn spring-boot:run" if "spring-boot" in tags else "java -jar target/*.jar")

    if "python" in tags:
        if "django" in tags:
            cmds.setdefault("run", "python manage.py runserver")
            cmds.setdefault("test", "python manage.py test")
            cmds.setdefault("migrate", "python manage.py migrate")
        elif "flask" in tags:
            cmds.setdefault("run", "python app.py")
        elif "fastapi" in tags:
            cmds.setdefault("run", "uvicorn main:app --reload")
        elif "streamlit" in tags:
            cmds.setdefault("run", "streamlit run app.py")

        cmds.setdefault("install", "pip install -r requirements.txt")
        if "pytest" in tags:
            cmds.setdefault("test", "pytest tests/")

    if "golang" in tags:
        cmds.setdefault("build", "go build ./...")
        cmds.setdefault("test", "go test ./...")
        cmds.setdefault("run", "go run main.go")

    if "rust" in tags:
        cmds.setdefault("build", "cargo build")
        cmds.setdefault("test", "cargo test")
        cmds.setdefault("run", "cargo run")

    if "docker" in tags:
        cmds.setdefault("docker-build", "docker build -t <image-name> .")
        if "docker-compose" in tags:
            cmds.setdefault("docker-up", "docker-compose up -d")

    if "terraform" in tags:
        cmds.setdefault("init", "terraform init")
        cmds.setdefault("plan", "terraform plan")
        cmds.setdefault("apply", "terraform apply")

    if "flyway" in tags:
        cmds.setdefault("migrate", "./gradlew flywayMigrate" if "gradle" in tags else "flyway migrate")

    return cmds


def _read_description(repo_path: Path) -> str:
    """Try to read a description from README.md or package.json."""
    readme = repo_path / "README.md"
    if readme.exists():
        try:
            lines = readme.read_text().splitlines()
            for line in lines:
                stripped = line.strip().lstrip("#").strip()
                if stripped and not stripped.startswith("!") and not stripped.startswith("["):
                    return stripped
        except IOError:
            pass
    return ""


# ─────────────────────────────────────────────────────────────
# CLAUDE.md Generation
# ─────────────────────────────────────────────────────────────

def generate_claude_md(info: RepoInfo) -> str:
    """Generate the CLAUDE.md content for a single repo."""
    lines = []

    # Header
    lines.append(f"# {info.name}")
    lines.append("")
    if info.description:
        lines.append(f"> {info.description}")
        lines.append("")

    # Overview
    lines.append("## Overview")
    lines.append(f"- **Primary Language**: {info.primary_language}")
    lines.append(f"- **Framework**: {info.framework}")
    lines.append(f"- **Tech Stack**: {', '.join(sorted(info.tech_tags)) if info.tech_tags else 'N/A'}")
    lines.append("")

    # Commands
    if info.build_commands:
        lines.append("## Key Commands")
        for label, cmd in info.build_commands.items():
            lines.append(f"- **{label}**: `{cmd}`")
        lines.append("")

    # Folder Structure
    if info.folder_structure:
        lines.append("## Project Structure")
        lines.append("```")
        for entry in info.folder_structure[:30]:  # limit output
            lines.append(entry)
        lines.append("```")
        lines.append("")

    # Conventions (template — users should customize)
    lines.append("## Conventions")
    lines.append("<!-- TODO: Fill in your team's coding conventions -->")

    if info.primary_language in ("JavaScript", "TypeScript", "JavaScript/TypeScript"):
        lines.append("- Use named exports over default exports (except pages/routes)")
        lines.append("- Keep components small and composable")
        if "typescript" in info.tech_tags:
            lines.append("- Avoid `any` — use `unknown` and type-narrow")
        if "react" in info.tech_tags:
            lines.append("- Co-locate tests with components (`Component.test.tsx`)")
        if "tailwind" in info.tech_tags:
            lines.append("- Use Tailwind utility classes; avoid custom CSS where possible")

    elif info.primary_language == "Python":
        lines.append("- Follow PEP 8 style guidelines")
        lines.append("- Use type hints for all function signatures")
        if "django" in info.tech_tags:
            lines.append("- Fat models, thin views — keep business logic in models/services")
        if "flask" in info.tech_tags or "fastapi" in info.tech_tags:
            lines.append("- Organize routes in blueprints/routers, not in a single file")
        if "langchain" in info.tech_tags:
            lines.append("- Store prompts in external files under `prompts/`")
            lines.append("- All LLM calls should go through a gateway/wrapper for retries and fallback")

    elif info.primary_language in ("Java", "Kotlin"):
        lines.append("- Follow standard Java/Kotlin naming conventions")
        if "spring-boot" in info.tech_tags:
            lines.append("- No business logic in controllers — delegate to service layer")
            lines.append("- Use `@Transactional` at service layer only")
        if "flyway" in info.tech_tags:
            lines.append("- Flyway migrations: `V{version}__{description}.sql`")

    elif info.primary_language == "Go":
        lines.append("- Follow `go fmt` and `go vet` standards")
        lines.append("- Use table-driven tests")
        lines.append("- Keep interfaces small (1-3 methods)")

    elif info.primary_language == "Rust":
        lines.append("- Run `cargo clippy` before committing")
        lines.append("- Prefer `Result<T, E>` over panics")

    lines.append("")

    # Integration Points
    lines.append("## Integration Points")
    lines.append("<!-- TODO: List services this repo communicates with -->")
    lines.append("- [ ] API contracts / OpenAPI specs")
    lines.append("- [ ] Shared schemas or protobufs")
    lines.append("- [ ] Message queues / event topics")
    lines.append("")

    # Features / Capabilities
    features = []
    if info.has_tests:
        features.append("✅ Tests detected")
    if info.has_docker:
        features.append("🐳 Docker support")
    if info.has_ci:
        features.append("⚙️  CI/CD pipeline")
    if info.has_db_migrations:
        migration_tool = (info.tech_tags & {"flyway", "alembic", "prisma", "drizzle", "liquibase"})
        features.append(f"🗄️  DB Migrations ({', '.join(migration_tool)})")
    if features:
        lines.append("## Detected Features")
        for feat in features:
            lines.append(f"- {feat}")
        lines.append("")

    # Common Pitfalls
    lines.append("## Common Pitfalls")
    lines.append("<!-- TODO: Add known gotchas for this repo -->")
    lines.append("- ")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Auto-generated by claude-md-initializer on {datetime.now().strftime('%Y-%m-%d %H:%M')}. Please review and customize.*")

    return "\n".join(lines)


def generate_root_claude_md(repos: list[RepoInfo]) -> str:
    """Generate a root-level CLAUDE.md that indexes all sub-repos."""
    lines = []
    lines.append("# Workspace — CLAUDE.md")
    lines.append("")
    lines.append("## Repository Index")
    lines.append("")
    lines.append("| Repository | Language | Framework | Key Tech |")
    lines.append("|------------|----------|-----------|----------|")
    for r in sorted(repos, key=lambda x: x.name):
        top_tags = ", ".join(sorted(r.tech_tags)[:5])
        lines.append(f"| `{r.name}` | {r.primary_language} | {r.framework} | {top_tags} |")
    lines.append("")

    lines.append("## Global Conventions")
    lines.append("<!-- TODO: Add workspace-wide conventions -->")
    lines.append("- Branch naming: `feature/<ticket-id>-<short-desc>`")
    lines.append("- Commit format: Conventional Commits (`feat:`, `fix:`, `chore:`)")
    lines.append("- PR reviews required before merge")
    lines.append("")

    lines.append("## Cross-Repo Dependencies")
    lines.append("<!-- TODO: Document how repos interact -->")
    lines.append("")

    lines.append("---")
    lines.append(f"*Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Main Execution
# ─────────────────────────────────────────────────────────────

def find_repos(base_dir: Path) -> list[Path]:
    """Find all git repositories in the base directory."""
    repos = []
    for item in sorted(base_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            # Check if it's a git repo OR has recognizable project files
            is_repo = (item / ".git").exists()
            has_project_files = any(
                (item / f).exists() for f in [
                    "package.json", "pom.xml", "build.gradle", "build.gradle.kts",
                    "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml",
                    "Gemfile", "composer.json", "Makefile", "main.tf",
                ]
            )
            if is_repo or has_project_files:
                repos.append(item)
    return repos


def main():
    parser = argparse.ArgumentParser(
        description="Initialize CLAUDE.md files across multiple repositories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --repos-dir ~/projects
  %(prog)s --repos-dir ~/projects --dry-run
  %(prog)s --repos-dir ~/projects --force --root-claude-md
        """,
    )
    parser.add_argument(
        "--repos-dir", "-d",
        type=Path,
        required=True,
        help="Parent directory containing cloned repositories",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated CLAUDE.md without writing files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing CLAUDE.md files",
    )
    parser.add_argument(
        "--root-claude-md",
        action="store_true",
        help="Also generate a root-level CLAUDE.md indexing all repos",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=None,
        help="Write CLAUDE.md files to a separate output directory instead of inside repos",
    )
    args = parser.parse_args()

    base_dir = args.repos_dir.resolve()
    if not base_dir.is_dir():
        logger.error(f"Directory not found: {base_dir}")
        return

    # Discover repos
    repos = find_repos(base_dir)
    if not repos:
        logger.warning(f"No repositories found in {base_dir}")
        return

    logger.info(f"Found {len(repos)} repositories in {base_dir}")
    print("=" * 60)

    all_info: list[RepoInfo] = []

    for repo_path in repos:
        logger.info(f"🔍 Scanning: {repo_path.name}")

        # Detect tech stack
        info = detect_tech_stack(repo_path)
        all_info.append(info)

        logger.info(f"   Language: {info.primary_language} | Framework: {info.framework}")
        logger.info(f"   Tags: {', '.join(sorted(info.tech_tags))}")

        # Generate CLAUDE.md
        content = generate_claude_md(info)

        # Determine output path
        if args.output_dir:
            out_dir = args.output_dir.resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{info.name}_CLAUDE.md"
        else:
            out_path = repo_path / "CLAUDE.md"

        if args.dry_run:
            print(f"\n{'─' * 60}")
            print(f"📄 {out_path}")
            print(f"{'─' * 60}")
            print(content)
            print()
        else:
            if out_path.exists() and not args.force:
                logger.warning(f"   ⏭️  Skipped (CLAUDE.md exists). Use --force to overwrite.")
            else:
                out_path.write_text(content)
                logger.info(f"   ✅ Written: {out_path}")

    # Root-level CLAUDE.md
    if args.root_claude_md:
        root_content = generate_root_claude_md(all_info)
        if args.output_dir:
            root_path = args.output_dir.resolve() / "CLAUDE.md"
        else:
            root_path = base_dir / "CLAUDE.md"

        if args.dry_run:
            print(f"\n{'═' * 60}")
            print(f"📄 ROOT: {root_path}")
            print(f"{'═' * 60}")
            print(root_content)
        else:
            if root_path.exists() and not args.force:
                logger.warning(f"Root CLAUDE.md exists. Use --force to overwrite.")
            else:
                root_path.write_text(root_content)
                logger.info(f"✅ Root CLAUDE.md written: {root_path}")

    # Summary
    print()
    print("=" * 60)
    print(f"📊 Summary: {len(all_info)} repositories processed")
    print("=" * 60)
    for info in sorted(all_info, key=lambda x: x.name):
        tags_str = ", ".join(sorted(info.tech_tags)[:6])
        print(f"  {info.name:<30} {info.primary_language:<20} [{tags_str}]")


if __name__ == "__main__":
    main()
