#!/usr/bin/env python3
"""
Step 6: Commit & Push
Commits changes, pushes to Bitbucket, optionally creates a PR.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ── Git operations ──────────────────────────────────────────────────────────────

def git_status(repo_path: Path) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo_path), "status", "--short"],
        capture_output=True, text=True, timeout=30
    )
    return r.stdout.strip()


def git_add_all(repo_path: Path) -> tuple:
    r = subprocess.run(
        ["git", "-C", str(repo_path), "add", "-A"],
        capture_output=True, text=True, timeout=30
    )
    return r.returncode, r.stdout + r.stderr


def git_commit(repo_path: Path, message: str) -> tuple:
    r = subprocess.run(
        ["git", "-C", str(repo_path), "commit", "-m", message],
        capture_output=True, text=True, timeout=30
    )
    return r.returncode, r.stdout + r.stderr


def git_push(repo_path: Path, branch: str, remote: str = "origin") -> tuple:
    r = subprocess.run(
        ["git", "-C", str(repo_path), "push", "--set-upstream", remote, branch],
        capture_output=True, text=True, timeout=120
    )
    return r.returncode, r.stdout + r.stderr


def get_current_branch(repo_path: Path) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, timeout=30
    )
    return r.stdout.strip()


def get_latest_commit_hash(repo_path: Path) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=30
    )
    return r.stdout.strip()


# ── Commit message generation ───────────────────────────────────────────────────

def generate_commit_message(apply_result: dict, requirement: dict) -> str:
    """Generate conventional commit message."""
    ticket_id = apply_result.get("ticket_id", "TICKET")
    summary = requirement.get("summary", "update") if requirement else "update"
    issue_type = (requirement.get("type", "task") if requirement else "task").lower()

    # Conventional commit type
    type_map = {
        "bug": "fix", "story": "feat", "feature": "feat",
        "task": "chore", "epic": "feat", "improvement": "feat",
        "sub-task": "chore", "subtask": "chore",
    }
    commit_type = type_map.get(issue_type, "chore")

    # Scope from ticket id prefix
    parts = ticket_id.split("-")
    scope = parts[0].lower() if len(parts) >= 2 else ticket_id.lower()

    # Shorten summary
    short_summary = summary[:72].strip()

    return f"{commit_type}({scope}): {short_summary}\n\nJira: {ticket_id}"


# ── Bitbucket PR creation ───────────────────────────────────────────────────────

def parse_bitbucket_url(bb_url: str) -> tuple:
    """
    Parse Bitbucket Server URL to extract project key and repo slug.
    Supports: https://bitbucket.example.com/scm/PROJ/repo.git
              https://bitbucket.example.com/projects/PROJ/repos/repo
    Returns: (base_url, project_key, repo_slug) or raises ValueError.
    """
    import re
    bb_url = bb_url.rstrip("/").replace(".git", "")

    # Pattern: /scm/PROJECT/REPO
    m = re.search(r"/scm/([^/]+)/([^/]+)$", bb_url)
    if m:
        base = bb_url[:m.start()]
        return base, m.group(1).upper(), m.group(2)

    # Pattern: /projects/PROJECT/repos/REPO
    m = re.search(r"/projects/([^/]+)/repos/([^/]+)$", bb_url)
    if m:
        base = bb_url[:m.start()]
        return base, m.group(1).upper(), m.group(2)

    raise ValueError(
        f"Cannot parse Bitbucket URL: {bb_url}. "
        "Expected format: .../scm/PROJECT/repo or .../projects/PROJECT/repos/repo"
    )


def create_bitbucket_pr(
    base_url: str,
    project_key: str,
    repo_slug: str,
    username: str,
    password: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: str,
    logs: list,
) -> dict:
    """Create a PR via Bitbucket Server REST API."""
    if not HAS_REQUESTS:
        raise ImportError("requests library required. pip install requests")

    api_url = (f"{base_url}/rest/api/1.0/projects/{project_key}"
               f"/repos/{repo_slug}/pull-requests")

    payload = {
        "title": title,
        "description": description,
        "state": "OPEN",
        "open": True,
        "closed": False,
        "fromRef": {
            "id": f"refs/heads/{source_branch}",
            "repository": {
                "slug": repo_slug,
                "project": {"key": project_key},
            },
        },
        "toRef": {
            "id": f"refs/heads/{target_branch}",
            "repository": {
                "slug": repo_slug,
                "project": {"key": project_key},
            },
        },
        "locked": False,
    }

    resp = requests.post(
        api_url,
        json=payload,
        auth=(username, password),
        timeout=30,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )

    if resp.status_code in (200, 201):
        pr_data = resp.json()
        pr_url = pr_data.get("links", {}).get("self", [{}])[0].get("href", "")
        logs.append(f"[OK] PR created: {pr_url}")
        return {"id": pr_data.get("id"), "url": pr_url, "title": title}
    else:
        raise RuntimeError(
            f"PR creation failed ({resp.status_code}): {resp.text[:500]}"
        )


def parse_github_url(gh_url: str) -> tuple:
    """
    Parse a GitHub URL to extract owner and repo name.
    Supports: https://github.com/owner/repo.git
              https://github.com/owner/repo
    Returns: (owner, repo)
    """
    import re
    gh_url = gh_url.rstrip("/").replace(".git", "")
    m = re.search(r"github\.com/([^/]+)/([^/]+)$", gh_url)
    if m:
        return m.group(1), m.group(2)
    raise ValueError(
        f"Cannot parse GitHub URL: {gh_url}. "
        "Expected format: https://github.com/owner/repo"
    )


def create_github_pr(
    owner: str,
    repo: str,
    token: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: str,
    logs: list,
) -> dict:
    """Create a PR via GitHub REST API."""
    if not HAS_REQUESTS:
        raise ImportError("requests library required. pip install requests")

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "body": description,
        "head": source_branch,
        "base": target_branch,
    }
    resp = requests.post(
        api_url,
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    if resp.status_code in (200, 201):
        pr_data = resp.json()
        pr_url = pr_data.get("html_url", "")
        logs.append(f"[OK] GitHub PR created: {pr_url}")
        return {"id": pr_data.get("number"), "url": pr_url, "title": title}
    else:
        raise RuntimeError(
            f"GitHub PR creation failed ({resp.status_code}): {resp.text[:500]}"
        )


def generate_pr_description(requirement: dict, apply_result: dict) -> str:
    """Generate PR description from requirement and apply result."""
    if not requirement:
        return "Automated change via Dev Skill"

    ticket_id = requirement.get("ticket_id", "")
    summary = requirement.get("summary", "")
    ac = requirement.get("acceptance_criteria", "")
    modified = apply_result.get("files_modified", 0) if apply_result else 0
    created = apply_result.get("files_created", 0) if apply_result else 0

    desc = f"## {ticket_id}: {summary}\n\n"
    if ac:
        desc += f"### Acceptance Criteria\n{ac[:1000]}\n\n"
    desc += f"### Changes\n- Modified files: {modified}\n- Created files: {created}\n\n"
    desc += "### Testing\n- [ ] Unit tests pass\n- [ ] Integration tests pass\n"
    desc += "\n---\n*Generated by Bitbucket + Jira Dev Skill*"
    return desc


# ── Main ────────────────────────────────────────────────────────────────────────

def commit_and_push(
    repo_path: Path,
    commit_message: str,
    push: bool,
    create_pr: bool,
    pr_params: dict,
    logs: list,
) -> dict:
    """Perform git add, commit, push and optionally create PR."""
    result = {
        "committed": False,
        "pushed": False,
        "pr": None,
        "branch": None,
        "commit_hash": None,
        "logs": logs,
    }

    # Status check
    status = git_status(repo_path)
    if not status:
        logs.append("[INFO] No changes to commit (working tree clean).")
        return result

    logs.append(f"Working tree changes:\n{status}")

    # git add -A
    rc, out = git_add_all(repo_path)
    logs.append(f"git add -A: {out.strip() or 'OK'}")

    # git commit
    rc, out = git_commit(repo_path, commit_message)
    if rc != 0:
        raise RuntimeError(f"git commit failed: {out}")
    logs.append(f"Committed: {out.strip()}")
    result["committed"] = True
    result["branch"] = get_current_branch(repo_path)
    result["commit_hash"] = get_latest_commit_hash(repo_path)

    # git push
    if push:
        branch = result["branch"]
        logs.append(f"Pushing branch {branch}...")
        rc, out = git_push(repo_path, branch)
        if rc != 0:
            raise RuntimeError(f"git push failed: {out}")
        logs.append(f"Pushed: {out.strip() or 'OK'}")
        result["pushed"] = True

        # Create PR
        if create_pr and pr_params:
            provider = pr_params.get("provider", "bitbucket")
            logs.append(f"Creating {provider.title()} PR...")
            try:
                if provider == "github":
                    pr = create_github_pr(
                        owner=pr_params["owner"],
                        repo=pr_params["repo"],
                        token=pr_params["token"],
                        source_branch=branch,
                        target_branch=pr_params.get("target_branch", "main"),
                        title=pr_params.get("title", commit_message.split("\n")[0]),
                        description=pr_params.get("description", ""),
                        logs=logs,
                    )
                else:
                    pr = create_bitbucket_pr(
                        base_url=pr_params["base_url"],
                        project_key=pr_params["project_key"],
                        repo_slug=pr_params["repo_slug"],
                        username=pr_params["username"],
                        password=pr_params["password"],
                        source_branch=branch,
                        target_branch=pr_params.get("target_branch", "main"),
                        title=pr_params.get("title", commit_message.split("\n")[0]),
                        description=pr_params.get("description", ""),
                        logs=logs,
                    )
                result["pr"] = pr
            except Exception as e:
                logs.append(f"[WARN] PR creation failed: {e}")

    return result


def main():
    from step_0_setup import load_config

    parser = argparse.ArgumentParser(description="Commit and push changes")
    parser.add_argument("--apply-result", default="apply_result.json",
                        help="Path to apply_result.json")
    parser.add_argument("--requirement", default="requirement.json",
                        help="Path to requirement.json")
    parser.add_argument("--commit-message", help="Override commit message")
    parser.add_argument("--push", action="store_true", help="Push to remote")
    parser.add_argument("--create-pr", action="store_true", help="Create PR (Bitbucket or GitHub)")
    parser.add_argument("--target-branch", default="main", help="PR target branch")
    parser.add_argument("--project-key", help="Bitbucket project key (Bitbucket only)")
    parser.add_argument("--repo-slug", help="Bitbucket repo slug (Bitbucket only)")
    parser.add_argument("--repo-path", help="Override repo path")
    parser.add_argument("--output", default="commit_result.json", help="Output JSON path")
    parser.add_argument("--check-status", action="store_true", help="Show git status only")
    args = parser.parse_args()

    config = load_config()

    # Load apply result
    apply_result = {}
    if Path(args.apply_result).exists():
        with open(args.apply_result, encoding="utf-8") as f:
            apply_result = json.load(f)

    # Load requirement
    requirement = {}
    if Path(args.requirement).exists():
        with open(args.requirement, encoding="utf-8") as f:
            requirement = json.load(f)

    repo_path_str = (args.repo_path or
                     config.get("workspace_dir", "") or
                     apply_result.get("branch", ""))

    # Try to find repo from analysis report
    analysis_path = Path("analysis_report.json")
    if analysis_path.exists():
        with open(analysis_path, encoding="utf-8") as f:
            ar = json.load(f)
        repo_path = Path(ar.get("repo_path", "."))
    elif repo_path_str:
        repo_path = Path(repo_path_str)
    else:
        repo_path = Path(".")

    if args.check_status:
        status = git_status(repo_path)
        print(f"Branch: {get_current_branch(repo_path)}")
        print(f"Status:\n{status if status else '(clean)'}")
        return

    # Generate commit message
    if args.commit_message:
        commit_msg = args.commit_message
    else:
        commit_msg = generate_commit_message(apply_result, requirement)

    print(f"Commit message:\n{commit_msg}\n")

    # Build PR params — detect provider from config
    pr_params = {}
    if args.create_pr:
        repo_url = config.get("repo_url", config.get("bitbucket_url", ""))
        git_provider = config.get("git_provider", "")
        if not git_provider:
            git_provider = "github" if "github.com" in repo_url else "bitbucket"

        pr_title = commit_msg.split("\n")[0]
        pr_desc = generate_pr_description(requirement, apply_result)

        if git_provider == "github":
            try:
                owner, repo_name = parse_github_url(repo_url)
            except Exception:
                owner, repo_name = "", ""
            pr_params = {
                "provider": "github",
                "owner": owner,
                "repo": repo_name,
                "token": config.get("git_password", config.get("bitbucket_password", "")),
                "target_branch": args.target_branch,
                "title": pr_title,
                "description": pr_desc,
            }
        else:
            try:
                base_url, project_key, repo_slug = parse_bitbucket_url(repo_url)
            except Exception:
                base_url = repo_url
                project_key = args.project_key or ""
                repo_slug = args.repo_slug or ""
            pr_params = {
                "provider": "bitbucket",
                "base_url": base_url,
                "project_key": args.project_key or project_key,
                "repo_slug": args.repo_slug or repo_slug,
                "username": config.get("git_username", config.get("bitbucket_username", "")),
                "password": config.get("git_password", config.get("bitbucket_password", "")),
                "target_branch": args.target_branch,
                "title": pr_title,
                "description": pr_desc,
            }

    logs = []
    try:
        result = commit_and_push(
            repo_path=repo_path,
            commit_message=commit_msg,
            push=args.push,
            create_pr=args.create_pr,
            pr_params=pr_params,
            logs=logs,
        )
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    for line in logs:
        print(line)
    print(f"\n[OK] Commit result saved to {output_path}")
    if result.get("pr"):
        print(f"     PR: {result['pr'].get('url', '')}")


if __name__ == "__main__":
    main()
