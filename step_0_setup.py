#!/usr/bin/env python3
"""
Step 0: Setup & Configuration
Collects and securely stores Bitbucket + Jira credentials.
"""
import argparse
import json
import os
import platform
import stat
import sys
from getpass import getpass
from pathlib import Path


CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"


def mask_credential(value: str) -> str:
    """Mask credential: show first4****last4."""
    if not value or len(value) < 8:
        return "****"
    return value[:4] + "****" + value[-4:]


def _restrict_file_permissions(path: Path) -> None:
    """Set file to owner-read/write only. Works on both Linux and Windows."""
    if platform.system() == "Windows":
        # On Windows: remove the read-only attribute is all we can do without
        # win32security; at minimum ensure the file is writable by owner.
        try:
            import stat as _stat
            current = os.stat(path).st_mode
            os.chmod(path, current | _stat.S_IWRITE)
        except Exception:
            pass  # Non-fatal on Windows — NTFS ACLs handle real permissions
    else:
        # POSIX: chmod 600
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    _restrict_file_permissions(CONFIG_FILE)
    print(f"[OK] Configuration saved to {CONFIG_FILE.resolve()}")


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def validate_config(config: dict) -> list:
    errors = []
    # Git provider credentials are always required
    required = [
        ("repo_url", "Repository URL"),
        ("git_username", "Git username"),
        ("git_password", "Git password / token"),
    ]
    for key, label in required:
        if not config.get(key, "").strip():
            errors.append(f"Missing: {label}")
    # Jira is optional — only validate if any Jira field is provided
    jira_provided = any(config.get(k, "").strip()
                        for k in ("jira_url", "jira_email", "jira_token"))
    if jira_provided:
        for key, label in [("jira_url", "Jira URL"),
                            ("jira_email", "Jira email"),
                            ("jira_token", "Jira API token")]:
            if not config.get(key, "").strip():
                errors.append(f"Missing: {label} (required when Jira is configured)")
    # project_keys must be a list if present
    pk = config.get("project_keys")
    if pk is not None and not isinstance(pk, list):
        errors.append("project_keys must be a list of strings")
    return errors


def interactive_setup() -> dict:
    print("=== Bitbucket + Jira Dev Skill — Setup ===\n")
    existing = load_config()

    def prompt(label, key, secret=False, default=""):
        current = existing.get(key, default)
        hint = f" [{mask_credential(current) if (secret and current) else current}]" if current else ""
        if secret:
            val = getpass(f"{label}{hint}: ").strip()
        else:
            val = input(f"{label}{hint}: ").strip()
        return val if val else current

    provider_input = input(
        f"Git Provider (bitbucket/github) [{existing.get('git_provider', 'bitbucket')}]: "
    ).strip().lower()
    git_provider = provider_input if provider_input in ("bitbucket", "github") \
        else existing.get("git_provider", "bitbucket")

    # Multi-repo scope — optional
    if git_provider == "github":
        github_owner_val = input(
            f"GitHub Owner/Org for multi-repo scan (leave blank to skip) "
            f"[{existing.get('github_owner', '')}]: "
        ).strip() or existing.get("github_owner", "")
        project_keys_val = []
    else:
        github_owner_val = ""
        pk_raw = input(
            "Bitbucket Project Keys for multi-repo scan (comma-separated, leave blank to skip) "
            f"[{','.join(existing.get('project_keys', []))}]: "
        ).strip()
        if pk_raw:
            project_keys_val = [k.strip().upper() for k in pk_raw.split(",") if k.strip()]
        else:
            project_keys_val = existing.get("project_keys", [])

    config = {
        "git_provider": git_provider,
        "repo_url": prompt(
            f"Repository URL (e.g. https://{'github.com/org/repo' if git_provider == 'github' else 'bitbucket.example.com/scm/PROJ/repo.git'})",
            "repo_url",
        ),
        "git_username": prompt("Git Username", "git_username"),
        "git_password": prompt(
            "Git Password / Token (App-Password for Bitbucket, PAT for GitHub)",
            "git_password", secret=True,
        ),
        "git_branch": prompt("Default Branch", "git_branch", default="main"),
        # Multi-repo scope
        "github_owner": github_owner_val,
        "project_keys": project_keys_val,
        # Jira — optional
        "jira_url": prompt("Jira URL (leave blank to skip)", "jira_url"),
        "jira_email": prompt("Jira Email (leave blank to skip)", "jira_email"),
        "jira_token": prompt("Jira API Token (leave blank to skip)", "jira_token", secret=True),
        "jira_ticket": prompt("Default Jira Ticket ID (optional)", "jira_ticket"),
        "workspace_dir": prompt("Workspace Directory", "workspace_dir",
                                default=str(Path.home() / "dev-workspace")),
    }

    errors = validate_config(config)
    if errors:
        print("\n[WARN] Missing required fields:")
        for e in errors:
            print(f"  - {e}")
        print("Configuration saved anyway — please complete before running other steps.")

    save_config(config)
    return config


def cli_setup(args) -> dict:
    existing = load_config()

    # Detect provider from URL if not explicitly given
    repo_url = (getattr(args, "repo_url", None) or
                getattr(args, "bitbucket_url", None) or
                existing.get("repo_url", existing.get("bitbucket_url", "")))
    git_provider = (getattr(args, "git_provider", None) or
                    existing.get("git_provider", ""))
    if not git_provider:
        git_provider = "github" if "github.com" in repo_url else "bitbucket"

    git_username = (getattr(args, "git_username", None) or
                    getattr(args, "bitbucket_username", None) or
                    existing.get("git_username", existing.get("bitbucket_username", "")))
    git_password = (getattr(args, "git_password", None) or
                    getattr(args, "bitbucket_password", None) or
                    existing.get("git_password", existing.get("bitbucket_password", "")))
    git_branch = (getattr(args, "git_branch", None) or
                  getattr(args, "bitbucket_branch", None) or
                  existing.get("git_branch", existing.get("bitbucket_branch", "main")))

    # Multi-repo scope
    github_owner = (getattr(args, "github_owner", None) or
                    existing.get("github_owner", ""))
    # project_keys: CLI accepts comma-separated string; config stores list
    raw_pk = getattr(args, "project_keys", None)
    if raw_pk:
        if isinstance(raw_pk, list):
            project_keys = [k.strip().upper() for k in raw_pk if k.strip()]
        else:
            project_keys = [k.strip().upper() for k in raw_pk.split(",") if k.strip()]
    else:
        project_keys = existing.get("project_keys", [])

    config = {
        "git_provider": git_provider,
        "repo_url": repo_url,
        "git_username": git_username,
        "git_password": git_password,
        "git_branch": git_branch,
        "github_owner": github_owner,
        "project_keys": project_keys,
        "jira_url": getattr(args, "jira_url", None) or existing.get("jira_url", ""),
        "jira_email": getattr(args, "jira_email", None) or existing.get("jira_email", ""),
        "jira_token": getattr(args, "jira_token", None) or existing.get("jira_token", ""),
        "jira_ticket": getattr(args, "jira_ticket", None) or existing.get("jira_ticket", ""),
        "workspace_dir": (getattr(args, "workspace_dir", None) or
                          existing.get("workspace_dir", str(Path.home() / "dev-workspace"))),
    }

    errors = validate_config(config)
    if errors:
        print("[ERROR] Validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    save_config(config)
    return config


def show_config() -> None:
    config = load_config()
    if not config:
        print("[INFO] No configuration found. Run setup first.")
        return
    print("\n=== Current Configuration ===")
    sensitive = {"git_password", "jira_token",
                 "bitbucket_password"}  # keep old key for backward compat
    for k, v in config.items():
        display = mask_credential(str(v)) if k in sensitive else v
        print(f"  {k}: {display}")


def main():
    parser = argparse.ArgumentParser(
        description="Setup Git (Bitbucket/GitHub) + Jira credentials"
    )
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    # New unified args
    parser.add_argument("--git-provider", choices=["bitbucket", "github"],
                        help="Git provider (bitbucket or github)")
    parser.add_argument("--repo-url", help="Repository URL")
    parser.add_argument("--git-username", help="Git username")
    parser.add_argument("--git-password", help="Git password / token")
    parser.add_argument("--git-branch", default="main", help="Default branch")
    # Multi-repo scope
    parser.add_argument("--github-owner",
                        help="GitHub user/org for multi-repo scanning")
    parser.add_argument("--project-keys",
                        help="Bitbucket project keys (comma-separated) for multi-repo scanning")
    # Backward-compat aliases (Bitbucket)
    parser.add_argument("--bitbucket-url", help=argparse.SUPPRESS)
    parser.add_argument("--bitbucket-username", help=argparse.SUPPRESS)
    parser.add_argument("--bitbucket-password", help=argparse.SUPPRESS)
    parser.add_argument("--bitbucket-branch", help=argparse.SUPPRESS)
    # Jira (optional)
    parser.add_argument("--jira-url", help="Jira server URL (optional)")
    parser.add_argument("--jira-email", help="Jira email (optional)")
    parser.add_argument("--jira-token", help="Jira API token (optional)")
    parser.add_argument("--jira-ticket", help="Default Jira ticket ID (optional)")
    parser.add_argument("--workspace-dir", help="Local workspace directory")

    args = parser.parse_args()

    if args.show:
        show_config()
        return

    # If any CLI arg is provided, use CLI mode
    cli_args = [
        args.repo_url, args.git_username, args.git_password,
        args.bitbucket_url, args.bitbucket_username, args.bitbucket_password,
        args.jira_url, args.jira_email, args.jira_token,
    ]
    if any(cli_args):
        cli_setup(args)
    else:
        interactive_setup()


if __name__ == "__main__":
    main()
