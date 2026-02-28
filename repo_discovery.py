#!/usr/bin/env python3
"""
repo_discovery.py — Multi-repository discovery for GitHub and Bitbucket.

GitHub  : list all repos for a user/organization (handles pagination).
Bitbucket Server/Cloud: list all repos for one or more project keys (handles pagination).

Both providers are accessed via REST APIs authenticated with the same credentials
already stored in config/config.json.
"""
import sys
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ── GitHub ──────────────────────────────────────────────────────────────────────

def list_github_repos(
    owner: str,
    token: str,
    repo_type: str = "all",
    per_page: int = 100,
) -> list:
    """
    Return a list of repo dicts for a GitHub owner or organisation.

    Each dict contains at minimum:
      { "name": str, "clone_url": str, "ssh_url": str,
        "default_branch": str, "private": bool, "description": str }

    Args:
        owner      – GitHub username or organisation name.
        token      – Personal Access Token (needs at least repo / read:org scope).
        repo_type  – "all", "public", or "private"  (only for org endpoints;
                     user endpoints ignore this but the value is still passed).
        per_page   – results per API page (max 100).
    """
    if not HAS_REQUESTS:
        raise ImportError("requests library required. pip install requests")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    repos = []
    page = 1

    # Try org endpoint first; fall back to user endpoint on 404
    def fetch_page(url: str, params: dict) -> requests.Response:
        return requests.get(url, headers=headers, params=params, timeout=30)

    base_org_url = f"https://api.github.com/orgs/{owner}/repos"
    base_user_url = f"https://api.github.com/users/{owner}/repos"

    # Detect whether owner is an org or a user
    check = requests.get(f"https://api.github.com/orgs/{owner}",
                         headers=headers, timeout=30)
    is_org = check.status_code == 200

    base_url = base_org_url if is_org else base_user_url

    while True:
        params = {"per_page": per_page, "page": page}
        if is_org:
            params["type"] = repo_type

        resp = fetch_page(base_url, params)
        if resp.status_code == 404 and is_org:
            # Org not found — fall back to user
            is_org = False
            base_url = base_user_url
            resp = fetch_page(base_url, params)

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"GitHub API error {resp.status_code}: {resp.text[:400]}"
            )

        batch = resp.json()
        if not batch:
            break

        for r in batch:
            repos.append({
                "name": r["name"],
                "clone_url": r["clone_url"],
                "ssh_url": r.get("ssh_url", ""),
                "default_branch": r.get("default_branch") or "main",
                "private": r.get("private", False),
                "description": r.get("description") or "",
                "full_name": r.get("full_name", f"{owner}/{r['name']}"),
            })

        if len(batch) < per_page:
            break
        page += 1

    return repos


# ── Bitbucket Server ────────────────────────────────────────────────────────────

def _parse_bitbucket_base_url(repo_url: str) -> str:
    """
    Extract the Bitbucket Server base URL from a full repo URL.
    e.g. https://bitbucket.example.com/scm/PROJ/repo.git  →  https://bitbucket.example.com
    """
    import re
    repo_url = repo_url.rstrip("/").replace(".git", "")
    for pattern in (r"/scm/[^/]+/[^/]+$", r"/projects/[^/]+/repos/[^/]+$"):
        m = re.search(pattern, repo_url)
        if m:
            return repo_url[: m.start()]
    # Fallback: strip trailing path components until we get a base
    parts = repo_url.rstrip("/").split("/")
    if len(parts) >= 3:
        return "/".join(parts[:3])
    return repo_url


def list_bitbucket_server_repos(
    base_url: str,
    project_key: str,
    username: str,
    password: str,
    limit: int = 100,
) -> list:
    """
    Return a list of repo dicts for a single Bitbucket Server project key.

    Each dict contains:
      { "slug": str, "name": str, "clone_url": str,
        "project_key": str, "description": str }
    """
    if not HAS_REQUESTS:
        raise ImportError("requests library required. pip install requests")

    repos = []
    start = 0
    auth = (username, password)
    headers = {"Accept": "application/json"}

    while True:
        url = (f"{base_url}/rest/api/1.0/projects/{project_key}/repos"
               f"?limit={limit}&start={start}")
        resp = requests.get(url, auth=auth, headers=headers, timeout=30)

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Bitbucket API error {resp.status_code} for project {project_key}: "
                f"{resp.text[:400]}"
            )

        data = resp.json()

        for r in data.get("values", []):
            # Prefer http clone URL
            clone_url = ""
            for lnk in r.get("links", {}).get("clone", []):
                if lnk.get("name") == "http":
                    clone_url = lnk["href"]
                    break
            if not clone_url:
                clone_url = (
                    f"{base_url}/scm/{project_key.lower()}/{r['slug']}.git"
                )

            repos.append({
                "slug": r["slug"],
                "name": r.get("name", r["slug"]),
                "clone_url": clone_url,
                "project_key": project_key.upper(),
                "description": r.get("description") or "",
            })

        if data.get("isLastPage", True):
            break
        start = data.get("nextPageStart", start + limit)

    return repos


def list_bitbucket_cloud_repos(
    workspace: str,
    username: str,
    app_password: str,
    pagelen: int = 100,
) -> list:
    """
    Return repos for a Bitbucket Cloud workspace.

    workspace – the workspace slug (appears in bitbucket.org URLs).
    """
    if not HAS_REQUESTS:
        raise ImportError("requests library required. pip install requests")

    repos = []
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}"
    params = {"pagelen": pagelen}
    auth = (username, app_password)

    while url:
        resp = requests.get(url, auth=auth, params=params, timeout=30)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Bitbucket Cloud API error {resp.status_code}: {resp.text[:400]}"
            )
        data = resp.json()
        for r in data.get("values", []):
            links = r.get("links", {}).get("clone", [])
            clone_url = next(
                (lnk["href"] for lnk in links if lnk.get("name") == "https"), ""
            )
            repos.append({
                "slug": r.get("slug", r.get("full_name", "").split("/")[-1]),
                "name": r.get("name", ""),
                "clone_url": clone_url,
                "project_key": workspace,
                "description": r.get("description") or "",
                "default_branch": (
                    r.get("mainbranch", {}).get("name") or "main"
                ),
            })
        url = data.get("next")  # None → stop

    return repos


# ── Unified entry point ─────────────────────────────────────────────────────────

def discover_repos(config: dict, project_keys: list = None,
                   github_owner: str = None) -> list:
    """
    High-level helper: discover repos based on provider in config.

    For GitHub  : uses github_owner (or config["github_owner"]).
    For Bitbucket: iterates over project_keys (or config["project_keys"]).

    Returns a list of repo dicts, each with at least:
      { "name": str, "clone_url": str, "default_branch": str }
    """
    provider = config.get("git_provider", "")
    if not provider:
        provider = "github" if "github.com" in config.get("repo_url", "") else "bitbucket"

    username = config.get("git_username", config.get("bitbucket_username", ""))
    password = config.get("git_password", config.get("bitbucket_password", ""))

    if provider == "github":
        owner = github_owner or config.get("github_owner", "")
        if not owner:
            raise ValueError(
                "GitHub owner/organisation required. "
                "Pass github_owner or set 'github_owner' in config."
            )
        repos = list_github_repos(owner=owner, token=password)
        # Ensure default_branch is present
        for r in repos:
            r.setdefault("default_branch", "main")
        return repos

    else:  # bitbucket
        keys = project_keys or config.get("project_keys", [])
        if not keys:
            raise ValueError(
                "Bitbucket project key(s) required. "
                "Pass project_keys or set 'project_keys' in config."
            )

        repo_url = config.get("repo_url", config.get("bitbucket_url", ""))
        is_cloud = "bitbucket.org" in repo_url

        all_repos = []
        if is_cloud:
            for pk in keys:
                all_repos.extend(
                    list_bitbucket_cloud_repos(
                        workspace=pk,
                        username=username,
                        app_password=password,
                    )
                )
        else:
            base_url = _parse_bitbucket_base_url(repo_url)
            for pk in keys:
                all_repos.extend(
                    list_bitbucket_server_repos(
                        base_url=base_url,
                        project_key=pk,
                        username=username,
                        password=password,
                    )
                )
        return all_repos


# ── CLI helper (for quick testing) ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Discover repositories")
    parser.add_argument("--github-owner", help="GitHub user/org name")
    parser.add_argument("--project-keys", nargs="+",
                        help="Bitbucket project key(s) e.g. PROJ1 PROJ2")
    args = parser.parse_args()

    try:
        from step_0_setup import load_config
        cfg = load_config()
    except Exception:
        cfg = {}

    repos = discover_repos(
        cfg,
        project_keys=args.project_keys,
        github_owner=args.github_owner,
    )
    print(json.dumps(repos, indent=2))
    print(f"\nTotal repos: {len(repos)}", file=sys.stderr)
