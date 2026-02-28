#!/usr/bin/env python3
"""
Step 5: Apply Changes Locally
Creates feature branch, applies suggested_changes, runs formatters and tests.
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


# ── Cross-platform tool discovery ───────────────────────────────────────────────

def find_tool(*names: str) -> str:
    """
    Find an executable on PATH, trying each candidate name.
    On Windows, shutil.which() automatically appends .exe/.cmd/.bat,
    but pip-installed tools may also exist as plain names — try both.
    Extra Windows-specific names (e.g. 'mvn.cmd') are added automatically.
    Returns the resolved name/path, or empty string if not found.
    """
    candidates = list(names)
    if platform.system() == "Windows":
        # Add .cmd variants common on Windows (npm, mvn, prettier, etc.)
        candidates += [n + ".cmd" for n in names] + [n + ".exe" for n in names]
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    return ""


# ── Branch naming ───────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert text to git-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-{2,}", "-", text)
    return text[:50].rstrip("-")


def create_feature_branch(repo_path: Path, ticket_id: str, summary: str) -> tuple:
    """Create feature branch. Returns (branch_name, logs)."""
    logs = []
    slug = slugify(summary)
    branch_name = f"feature/{ticket_id}-{slug}"

    # Check if already on this branch
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, timeout=30
    )
    current = result.stdout.strip()
    if current == branch_name:
        logs.append(f"Already on branch: {branch_name}")
        return branch_name, logs

    # Create new branch from current HEAD
    result = subprocess.run(
        ["git", "-C", str(repo_path), "checkout", "-b", branch_name],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        # Branch may already exist
        result = subprocess.run(
            ["git", "-C", str(repo_path), "checkout", branch_name],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create/checkout branch: {result.stderr}")

    logs.append(f"Created/switched to branch: {branch_name}")
    return branch_name, logs


# ── Change application ──────────────────────────────────────────────────────────

def apply_replace(content: str, old_text: str, new_text: str) -> str:
    """Replace first occurrence of old_text with new_text."""
    if old_text not in content:
        raise ValueError(f"Text not found: {repr(old_text[:50])}")
    return content.replace(old_text, new_text, 1)


def apply_insert_after(content: str, after_line: str, new_text: str) -> str:
    """Insert new_text after the first line matching after_line."""
    lines = content.split("\n")
    after_line_str = str(after_line)

    # Try as line number first
    if after_line_str.isdigit():
        line_no = int(after_line_str) - 1
        if 0 <= line_no < len(lines):
            lines.insert(line_no + 1, new_text)
            return "\n".join(lines)

    # Try as text marker
    for i, line in enumerate(lines):
        if after_line_str in line:
            lines.insert(i + 1, new_text)
            return "\n".join(lines)

    raise ValueError(f"Insert-after marker not found: {repr(after_line_str)}")


def apply_insert_before(content: str, before_line: str, new_text: str) -> str:
    """Insert new_text before the first line matching before_line."""
    lines = content.split("\n")
    before_line_str = str(before_line)

    if before_line_str.isdigit():
        line_no = int(before_line_str) - 1
        if 0 <= line_no < len(lines):
            lines.insert(line_no, new_text)
            return "\n".join(lines)

    for i, line in enumerate(lines):
        if before_line_str in line:
            lines.insert(i, new_text)
            return "\n".join(lines)

    raise ValueError(f"Insert-before marker not found: {repr(before_line_str)}")


def apply_change(content: str, change: dict) -> str:
    """Apply a single change operation to content."""
    change_type = change.get("type", "")

    if change_type == "replace":
        return apply_replace(content, change["old_text"], change["new_text"])
    elif change_type == "insert_after":
        key = "after_line"
        return apply_insert_after(content, change[key], change["new_text"])
    elif change_type == "insert_before":
        key = "before_line"
        return apply_insert_before(content, change[key], change["new_text"])
    elif change_type == "append":
        return content.rstrip("\n") + "\n" + change["new_text"] + "\n"
    elif change_type == "full_replace":
        return change["new_text"]
    else:
        raise ValueError(f"Unknown change type: {change_type}")


def apply_file_changes(repo_path: Path, file_entry: dict, logs: list) -> dict:
    """Apply all suggested_changes to a single file."""
    fname = file_entry.get("file", "")
    suggested_changes = file_entry.get("suggested_changes", [])
    result = {"file": fname, "status": "skipped", "changes_applied": 0, "errors": []}

    if not suggested_changes:
        result["status"] = "no_changes"
        return result

    fp = repo_path / fname
    if not fp.exists():
        result["status"] = "file_not_found"
        result["errors"].append(f"File not found: {fp}")
        logs.append(f"[WARN] File not found: {fname}")
        return result

    try:
        content = fp.read_text(encoding="utf-8", errors="replace")
        original_content = content

        for i, change in enumerate(suggested_changes):
            try:
                content = apply_change(content, change)
                result["changes_applied"] += 1
                logs.append(f"  Applied {change.get('type')} to {fname} (change {i + 1})")
            except Exception as e:
                err = f"Change {i + 1} ({change.get('type')}): {e}"
                result["errors"].append(err)
                logs.append(f"  [WARN] {err}")

        if content != original_content:
            fp.write_text(content, encoding="utf-8")
            result["status"] = "modified"
        else:
            result["status"] = "unchanged"

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        logs.append(f"[ERROR] Failed to modify {fname}: {e}")

    return result


def create_new_file(repo_path: Path, file_entry: dict, logs: list) -> dict:
    """Create a new file from file_entry."""
    fname = file_entry.get("file", file_entry.get("path", ""))
    content = file_entry.get("content", "")
    result = {"file": fname, "status": "created"}

    fp = repo_path / fname
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    logs.append(f"Created: {fname}")
    return result


def delete_file(repo_path: Path, file_entry, logs: list) -> dict:
    """Delete a file."""
    fname = file_entry if isinstance(file_entry, str) else file_entry.get("file", "")
    fp = repo_path / fname
    result = {"file": fname, "status": "not_found"}

    if fp.exists():
        fp.unlink()
        logs.append(f"Deleted: {fname}")
        result["status"] = "deleted"
    else:
        logs.append(f"[WARN] File to delete not found: {fname}")

    return result


# ── Formatters ──────────────────────────────────────────────────────────────────

def run_formatter(repo_path: Path, build_tools: list, changed_files: list,
                   logs: list) -> list:
    """Auto-detect and run code formatters."""
    formatter_logs = []
    py_files = [f for f in changed_files if f.endswith(".py")]
    js_ts_files = [f for f in changed_files
                   if any(f.endswith(ext) for ext in (".js", ".jsx", ".ts", ".tsx"))]
    java_files = [f for f in changed_files if f.endswith(".java")]

    # Python: black + isort
    if py_files:
        for formatter in ["black", "isort"]:
            tool = find_tool(formatter)
            if tool:
                r = subprocess.run(
                    [tool] + py_files,
                    capture_output=True, text=True, cwd=str(repo_path), timeout=60
                )
                if r.returncode == 0:
                    formatter_logs.append(f"[OK] {formatter} formatted {len(py_files)} Python files")
                else:
                    formatter_logs.append(f"[WARN] {formatter} failed: {r.stderr[:200]}")

    # JavaScript/TypeScript: prettier
    if js_ts_files:
        tool = find_tool("prettier")
        if tool:
            r = subprocess.run(
                [tool, "--write"] + js_ts_files,
                capture_output=True, text=True, cwd=str(repo_path), timeout=60
            )
            if r.returncode == 0:
                formatter_logs.append(f"[OK] prettier formatted {len(js_ts_files)} JS/TS files")
            else:
                formatter_logs.append(f"[WARN] prettier failed: {r.stderr[:200]}")

    # Java: spotless via Maven
    if java_files and "Maven" in build_tools:
        pom = repo_path / "pom.xml"
        mvn_tool = find_tool("mvn")
        if pom.exists() and mvn_tool:
            r = subprocess.run(
                [mvn_tool, "spotless:apply", "-q"],
                capture_output=True, text=True, cwd=str(repo_path), timeout=120
            )
            if r.returncode == 0:
                formatter_logs.append("[OK] spotless formatted Java files")
            else:
                formatter_logs.append("[WARN] spotless failed (non-fatal)")

    logs.extend(formatter_logs)
    return formatter_logs


# ── Test runners ────────────────────────────────────────────────────────────────

def run_tests(repo_path: Path, build_tools: list, logs: list) -> dict:
    """Auto-detect and run tests."""
    test_results = {"passed": False, "output": "", "framework": None}

    # pytest
    pytest_tool = find_tool("pytest")
    if pytest_tool:
        r = subprocess.run(
            [pytest_tool, "--tb=short", "-q"],
            capture_output=True, text=True, cwd=str(repo_path), timeout=300
        )
        test_results["framework"] = "pytest"
        test_results["output"] = (r.stdout + r.stderr)[-2000:]
        test_results["passed"] = r.returncode == 0
        logs.append(f"pytest: {'PASSED' if r.returncode == 0 else 'FAILED'}")
        return test_results

    # npm test
    if "npm" in build_tools or "yarn" in build_tools:
        pkg_json = repo_path / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
                if "test" in pkg.get("scripts", {}):
                    manager_name = "yarn" if (repo_path / "yarn.lock").exists() else "npm"
                    manager = find_tool(manager_name) or manager_name
                    r = subprocess.run(
                        [manager, "test", "--passWithNoTests"],
                        capture_output=True, text=True, cwd=str(repo_path), timeout=300
                    )
                    test_results["framework"] = f"{manager_name} test"
                    test_results["output"] = (r.stdout + r.stderr)[-2000:]
                    test_results["passed"] = r.returncode == 0
                    logs.append(f"{manager_name} test: {'PASSED' if r.returncode == 0 else 'FAILED'}")
                    return test_results
            except Exception:
                pass

    # Maven test
    if "Maven" in build_tools:
        pom = repo_path / "pom.xml"
        mvn_tool = find_tool("mvn")
        if pom.exists() and mvn_tool:
            r = subprocess.run(
                [mvn_tool, "test", "-q"],
                capture_output=True, text=True, cwd=str(repo_path), timeout=300
            )
            test_results["framework"] = "mvn test"
            test_results["output"] = (r.stdout + r.stderr)[-2000:]
            test_results["passed"] = r.returncode == 0
            logs.append(f"mvn test: {'PASSED' if r.returncode == 0 else 'FAILED'}")
            return test_results

    logs.append("[INFO] No test runner detected, skipping tests.")
    return test_results


# ── Git diff ────────────────────────────────────────────────────────────────────

def get_git_diff(repo_path: Path) -> dict:
    """Get git diff summary."""
    diff_stat = subprocess.run(
        ["git", "-C", str(repo_path), "diff", "--stat"],
        capture_output=True, text=True, timeout=30
    ).stdout.strip()

    diff_short = subprocess.run(
        ["git", "-C", str(repo_path), "diff", "--shortstat"],
        capture_output=True, text=True, timeout=30
    ).stdout.strip()

    diff_full = subprocess.run(
        ["git", "-C", str(repo_path), "diff"],
        capture_output=True, text=True, timeout=30
    ).stdout[:10000]

    return {
        "stat": diff_stat,
        "shortstat": diff_short,
        "full_diff": diff_full,
    }


# ── Main ────────────────────────────────────────────────────────────────────────

def apply_proposal(proposal: dict, repo_path: Path, analysis_report: dict,
                    logs: list, run_tests_flag: bool = True) -> dict:
    """Apply the full proposal to the repository."""
    ticket_id = proposal.get("ticket_id", "TICKET")
    summary = proposal.get("ticket_summary", "update")

    # Create feature branch
    logs.append(f"Creating feature branch for {ticket_id}...")
    try:
        branch_name, branch_logs = create_feature_branch(repo_path, ticket_id, summary)
        logs.extend(branch_logs)
    except Exception as e:
        raise RuntimeError(f"Branch creation failed: {e}")

    # Apply file modifications
    file_results = []
    changed_files = []
    files_to_modify = [f for f in proposal.get("files_to_modify", [])
                        if f.get("confirmed", True) and f.get("suggested_changes")]

    logs.append(f"Applying changes to {len(files_to_modify)} files...")
    for file_entry in files_to_modify:
        result = apply_file_changes(repo_path, file_entry, logs)
        file_results.append(result)
        if result["status"] == "modified":
            changed_files.append(file_entry["file"])

    # Create new files
    for file_entry in proposal.get("files_to_create", []):
        result = create_new_file(repo_path, file_entry, logs)
        file_results.append(result)
        changed_files.append(file_entry.get("file", ""))

    # Delete files
    for file_entry in proposal.get("files_to_delete", []):
        result = delete_file(repo_path, file_entry, logs)
        file_results.append(result)

    # Run formatters
    build_tools = analysis_report.get("build_tools", [])
    if changed_files:
        logs.append("Running code formatters...")
        run_formatter(repo_path, build_tools, changed_files, logs)

    # Run tests
    test_results = {"passed": None, "output": "", "framework": None}
    if run_tests_flag and changed_files:
        logs.append("Running tests...")
        test_results = run_tests(repo_path, build_tools, logs)

    # Git diff
    logs.append("Generating git diff...")
    diff = get_git_diff(repo_path)

    apply_result = {
        "branch": branch_name,
        "ticket_id": ticket_id,
        "files_modified": len([r for r in file_results if r["status"] == "modified"]),
        "files_created": len([r for r in file_results if r["status"] == "created"]),
        "files_deleted": len([r for r in file_results if r["status"] == "deleted"]),
        "file_results": file_results,
        "test_results": test_results,
        "git_diff": diff,
        "logs": logs,
    }

    return apply_result


def main():
    parser = argparse.ArgumentParser(description="Apply change proposal to repository")
    parser.add_argument("--proposal", default="change_proposal.json",
                        help="Path to change_proposal.json")
    parser.add_argument("--analysis", default="analysis_report.json",
                        help="Path to analysis_report.json")
    parser.add_argument("--output", default="apply_result.json",
                        help="Output JSON path")
    parser.add_argument("--no-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--repo-path", help="Override repo path from analysis report")
    args = parser.parse_args()

    proposal_path = Path(args.proposal)
    analysis_path = Path(args.analysis)

    if not proposal_path.exists():
        print(f"[ERROR] Proposal not found: {proposal_path}", file=sys.stderr)
        sys.exit(1)
    if not analysis_path.exists():
        print(f"[ERROR] Analysis report not found: {analysis_path}", file=sys.stderr)
        sys.exit(1)

    with open(proposal_path, encoding="utf-8") as f:
        proposal = json.load(f)
    with open(analysis_path, encoding="utf-8") as f:
        analysis_report = json.load(f)

    repo_path = Path(args.repo_path or analysis_report.get("repo_path", "."))

    if not repo_path.exists():
        print(f"[ERROR] Repository path not found: {repo_path}", file=sys.stderr)
        sys.exit(1)

    if not proposal.get("confirmed"):
        print("[ERROR] Proposal not confirmed. Run step_4_review.py first.", file=sys.stderr)
        sys.exit(1)

    logs = []
    try:
        result = apply_proposal(proposal, repo_path, analysis_report, logs,
                                 run_tests_flag=not args.no_tests)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    for line in logs:
        print(line)
    print(f"\n[OK] Apply result saved to {output_path}")
    print(f"     Branch: {result['branch']}")
    print(f"     Modified: {result['files_modified']}, "
          f"Created: {result['files_created']}, "
          f"Deleted: {result['files_deleted']}")
    if result["git_diff"]["shortstat"]:
        print(f"     Diff: {result['git_diff']['shortstat']}")


if __name__ == "__main__":
    main()
