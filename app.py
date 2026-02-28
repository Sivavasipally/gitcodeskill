#!/usr/bin/env python3
"""
Bitbucket + Jira Dev Skill — Streamlit Dashboard
Dark-themed full workflow UI.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st

# ── Page config (must be first Streamlit call) ──────────────────────────────────
st.set_page_config(
    page_title="Bitbucket + Jira Dev Skill",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ───────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
STEPS_META = [
    (0, "⚙️", "Setup & Config", "Configure Bitbucket and Jira credentials"),
    (1, "🔍", "Clone & Analyze", "Clone repository and build code index"),
    (2, "📋", "Fetch Requirements", "Pull Jira ticket details"),
    (3, "🗺️", "Map Changes", "Map requirements to relevant code files"),
    (4, "✏️", "Review & Confirm", "Review proposal and add specific changes"),
    (5, "⚡", "Apply Changes", "Apply changes to feature branch"),
    (6, "🚀", "Commit & Push", "Commit, push and create PR"),
]
STATUS_DONE = "✅"
STATUS_ACTIVE = "🔄"
STATUS_PENDING = "⬜"

WORKSPACE_FILES = {
    "analysis_report.json": "analysis",
    "multi_analysis_report.json": "multi_analysis",
    "requirement.json": "requirement",
    "change_proposal.json": "proposal",
    "apply_result.json": "apply_result",
    "commit_result.json": "commit_result",
}


# ── Custom CSS ──────────────────────────────────────────────────────────────────
DARK_CSS = """
<style>
/* Base */
[data-testid="stAppViewContainer"] { background: #0E1117; }
[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #21262d; }
[data-testid="stHeader"] { background: #0E1117; }

/* Cards */
.metric-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 16px 12px;
    text-align: center;
}
.metric-value {
    font-size: 1.8em;
    font-weight: 700;
    color: #e6edf3;
}
.metric-label {
    font-size: 0.78em;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 4px;
}

/* Terminal output */
.terminal {
    background: #000000;
    color: #3fb950;
    font-family: 'Courier New', Courier, monospace;
    font-size: 0.85em;
    padding: 16px;
    border-radius: 6px;
    border: 1px solid #21262d;
    max-height: 400px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: 600;
    border: 1px solid;
}
.badge-todo { color: #8b949e; border-color: #8b949e; }
.badge-inprogress { color: #d29922; border-color: #d29922; }
.badge-done { color: #3fb950; border-color: #3fb950; }
.badge-review { color: #6C63FF; border-color: #6C63FF; }
.badge-blocked { color: #f85149; border-color: #f85149; }

/* Pipeline bar */
.pipeline-container {
    display: flex;
    width: 100%;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin: 8px 0 20px 0;
    gap: 2px;
}
.pipeline-done { background: #3fb950; }
.pipeline-active { background: #6C63FF; animation: pulse 1.5s infinite; }
.pipeline-pending { background: #21262d; }
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Step header */
.step-header {
    background: #161b22;
    border: 1px solid #21262d;
    border-left: 3px solid #6C63FF;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 20px;
}
.step-title { font-size: 1.3em; font-weight: 700; color: #e6edf3; }
.step-desc { color: #8b949e; font-size: 0.9em; margin-top: 4px; }

/* File entry */
.file-entry {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 4px 0;
}
.file-score { color: #6C63FF; font-weight: 600; font-size: 0.9em; }

/* Ticket header */
.ticket-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 20px;
    margin: 10px 0;
}

/* Sidebar nav item */
.nav-item {
    padding: 6px 8px;
    border-radius: 6px;
    margin: 2px 0;
    cursor: pointer;
    font-size: 0.9em;
}
.nav-active { background: #21262d; color: #e6edf3; }

/* Buttons override */
.stButton > button {
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
}
.stButton > button:hover {
    border-color: #6C63FF;
    color: #6C63FF;
}

/* Diff viewer */
.diff-viewer {
    background: #0d1117;
    font-family: monospace;
    font-size: 0.82em;
    padding: 12px;
    border-radius: 6px;
    border: 1px solid #21262d;
    max-height: 500px;
    overflow-y: auto;
    white-space: pre-wrap;
    color: #c9d1d9;
}
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)


# ── Session state helpers ───────────────────────────────────────────────────────

def ss_get(key, default=None):
    return st.session_state.get(key, default)


def ss_set(key, value):
    st.session_state[key] = value


def init_session():
    defaults = {
        "current_step": 0,
        "step_status": {0: "pending", 1: "pending", 2: "pending",
                        3: "pending", 4: "pending", 5: "pending", 6: "pending"},
        "config": {},
        "analysis": None,
        "multi_analysis": None,
        "requirement": None,
        "proposal": None,
        "apply_result": None,
        "commit_result": None,
        "terminal_logs": {i: "" for i in range(7)},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# ── File helpers ────────────────────────────────────────────────────────────────

def load_workspace_file(fname: str):
    p = Path(fname) if Path(fname).is_absolute() else SCRIPT_DIR / fname
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_workspace_file(fname: str, data: dict) -> None:
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_all_workspace():
    for fname, key in WORKSPACE_FILES.items():
        data = load_workspace_file(fname)
        if data and ss_get(key) is None:
            ss_set(key, data)


load_all_workspace()


# ── Subprocess runner ───────────────────────────────────────────────────────────

def run_script(script_name: str, args: list = None) -> tuple:
    """Run a script and return (returncode, output)."""
    script_path = SCRIPT_DIR / script_name
    cmd = [sys.executable, str(script_path)] + (args or [])
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(SCRIPT_DIR),  # ensures output JSONs are written/read from the project dir
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr.strip() else "")
        return result.returncode, output.strip()
    except subprocess.TimeoutExpired:
        return 1, "[ERROR] Script timed out after 300 seconds."
    except Exception as e:
        return 1, f"[ERROR] Failed to run {script_name}: {e}"


# ── UI components ───────────────────────────────────────────────────────────────

def render_terminal(log_text: str, height: int = 300) -> None:
    if log_text:
        escaped = log_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(
            f'<div class="terminal" style="max-height:{height}px">{escaped}</div>',
            unsafe_allow_html=True,
        )


def render_step_header(step_num: int) -> None:
    _, icon, name, desc = STEPS_META[step_num]
    st.markdown(
        f'<div class="step-header">'
        f'<div class="step-title">{icon} Step {step_num}: {name}</div>'
        f'<div class="step-desc">{desc}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_pipeline_bar(current_step: int) -> None:
    step_statuses = ss_get("step_status", {})
    segments = []
    for i in range(7):
        st_val = step_statuses.get(i, "pending")
        if st_val == "done":
            css_class = "pipeline-done"
        elif i == current_step:
            css_class = "pipeline-active"
        else:
            css_class = "pipeline-pending"
        segments.append(f'<div class="pipeline-{css_class.split("-")[1]}" style="flex:1"></div>')

    bar_html = '<div class="pipeline-container">' + "".join(segments) + "</div>"
    st.markdown(bar_html, unsafe_allow_html=True)


def render_metric_cards(metrics: list) -> None:
    """metrics: list of (value, label) tuples."""
    cols = st.columns(len(metrics))
    for col, (value, label) in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-value">{value}</div>'
                f'<div class="metric-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def status_badge(status: str) -> str:
    status_map = {
        "to do": "badge-todo", "todo": "badge-todo",
        "in progress": "badge-inprogress", "in review": "badge-review",
        "done": "badge-done", "closed": "badge-done",
        "blocked": "badge-blocked", "open": "badge-inprogress",
    }
    css = status_map.get(status.lower(), "badge-todo")
    return f'<span class="badge {css}">{status}</span>'


def mask_cred(v: str) -> str:
    if not v or len(v) < 8:
        return "****"
    return v[:4] + "****" + v[-4:]


# ── Sidebar ─────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🚀 Dev Skill")
        st.markdown("---")

        current = ss_get("current_step", 0)
        step_statuses = ss_get("step_status", {})

        for step_num, icon, name, _ in STEPS_META:
            st_val = step_statuses.get(step_num, "pending")
            indicator = STATUS_DONE if st_val == "done" else (
                STATUS_ACTIVE if step_num == current else STATUS_PENDING
            )
            is_active = step_num == current
            bg = "#21262d" if is_active else "transparent"
            if st.button(
                f"{indicator} {step_num}. {name}",
                key=f"nav_{step_num}",
                use_container_width=True,
            ):
                ss_set("current_step", step_num)

        st.markdown("---")
        st.markdown("**Quick Actions**")

        if st.button("🔄 Reset All", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        if st.button("📁 View Workspace", use_container_width=True):
            ws = ss_get("config", {}).get("workspace_dir", ".")
            files = list(Path(".").glob("*.json"))
            if files:
                st.markdown("**JSON files:**")
                for f in files:
                    st.text(f.name)
            else:
                st.info("No workspace files found.")

        # Config summary
        config = ss_get("config", {})
        repo_url_cfg = config.get("repo_url", config.get("bitbucket_url", ""))
        if repo_url_cfg:
            st.markdown("---")
            provider = config.get("git_provider", "git").title()
            st.markdown(f"**Connected to ({provider}):**")
            st.caption(f"Repo: {repo_url_cfg[:35]}...")
            if config.get("jira_url"):
                st.caption(f"Jira: {config.get('jira_url', '')[:30]}...")
            else:
                st.caption("Jira: not configured")
            # Multi-repo scope hint
            if config.get("github_owner"):
                st.caption(f"Multi-scan owner: {config['github_owner']}")
            elif config.get("project_keys"):
                keys = config["project_keys"]
                st.caption(f"Multi-scan keys: {', '.join(keys[:3])}"
                           + (" …" if len(keys) > 3 else ""))


# ── Step 0: Setup ───────────────────────────────────────────────────────────────

def render_setup():
    render_step_header(0)

    # Load existing config
    try:
        from step_0_setup import load_config
        existing = load_config()
    except Exception:
        existing = {}

    # ── Git Provider selector ────────────────────────────────────────────────────
    provider_options = ["bitbucket", "github"]
    current_provider = existing.get("git_provider", "bitbucket")
    git_provider = st.radio(
        "Git Provider",
        options=provider_options,
        index=provider_options.index(current_provider) if current_provider in provider_options else 0,
        horizontal=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        provider_label = "GitHub" if git_provider == "github" else "Bitbucket"
        st.markdown(f"#### 🔧 {provider_label} Configuration")

        repo_url_placeholder = (
            "https://github.com/org/repo.git"
            if git_provider == "github"
            else "https://bitbucket.example.com/scm/PROJ/repo.git"
        )
        repo_url = st.text_input(
            "Repository URL",
            value=existing.get("repo_url", existing.get("bitbucket_url", "")),
            placeholder=repo_url_placeholder,
        )
        git_user = st.text_input(
            "Username",
            value=existing.get("git_username", existing.get("bitbucket_username", "")),
        )
        token_label = "Personal Access Token" if git_provider == "github" else "App-Password / Token"
        git_pass = st.text_input(
            token_label,
            value=existing.get("git_password", existing.get("bitbucket_password", "")),
            type="password",
            placeholder="Never your account password",
        )
        git_branch = st.text_input(
            "Default Branch",
            value=existing.get("git_branch", existing.get("bitbucket_branch", "main")),
        )

        if st.button(f"🔗 Test {provider_label} Connection", use_container_width=True):
            if repo_url and git_user and git_pass:
                from step_1_analyze import build_auth_url
                auth_url = build_auth_url(repo_url, git_user, git_pass)
                try:
                    result = subprocess.run(
                        ["git", "ls-remote", "--heads", auth_url],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        branches = len([l for l in result.stdout.strip().split("\n") if l])
                        st.success(f"✅ Connected! Found {branches} branch(es).")
                    else:
                        st.error(f"❌ Connection failed: {result.stderr[:200]}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("Fill in URL, username, and password/token first.")

    with col2:
        st.markdown("#### 📋 Jira Configuration *(optional)*")
        st.caption("Leave blank to enter requirements manually in Step 2.")
        jira_url = st.text_input("Jira URL",
                                  value=existing.get("jira_url", ""),
                                  placeholder="https://your-company.atlassian.net")
        jira_email = st.text_input("Email",
                                    value=existing.get("jira_email", ""))
        jira_token = st.text_input("API Token",
                                    value=existing.get("jira_token", ""),
                                    type="password")
        jira_ticket = st.text_input("Default Ticket ID",
                                     value=existing.get("jira_ticket", ""),
                                     placeholder="PROJ-123 (optional)")

        if st.button("🔗 Test Jira Connection", use_container_width=True):
            if jira_url and jira_email and jira_token:
                try:
                    import requests
                    resp = requests.get(
                        f"{jira_url}/rest/api/3/myself",
                        auth=(jira_email, jira_token),
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        user = resp.json().get("displayName", jira_email)
                        st.success(f"✅ Connected as: {user}")
                    else:
                        st.error(f"❌ HTTP {resp.status_code}: {resp.text[:200]}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.info("Jira is optional. Fill in all three fields to test the connection.")

    st.markdown("---")
    workspace_dir = st.text_input(
        "📂 Workspace Directory",
        value=existing.get("workspace_dir", str(Path.home() / "dev-workspace")),
    )

    # ── Multi-repo scope ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔁 Multi-Repository Scan *(optional)*")
    st.caption(
        "Fill in the fields below to enable scanning all repositories under a "
        "GitHub owner/organisation or one or more Bitbucket project keys."
    )

    if git_provider == "github":
        github_owner = st.text_input(
            "GitHub Owner / Organisation",
            value=existing.get("github_owner", ""),
            placeholder="e.g. my-org  or  my-username",
        )
        project_keys_str = ""
    else:
        github_owner = ""
        project_keys_str = st.text_input(
            "Bitbucket Project Keys (comma-separated)",
            value=",".join(existing.get("project_keys", [])),
            placeholder="e.g. PROJ1, PROJ2, PROJ3",
        )

    if st.button("💾 Save Configuration", use_container_width=True, type="primary"):
        if not repo_url.strip() or not git_user.strip() or not git_pass.strip():
            st.error("❌ Repository URL, Username, and Password/Token are required.")
        else:
            project_keys_list = [k.strip().upper() for k in project_keys_str.split(",") if k.strip()]

            cli_args = [
                "--git-provider", git_provider,
                "--repo-url", repo_url,
                "--git-username", git_user,
                "--git-password", git_pass,
                "--git-branch", git_branch,
                "--workspace-dir", workspace_dir,
            ]
            if github_owner.strip():
                cli_args += ["--github-owner", github_owner.strip()]
            if project_keys_list:
                cli_args += ["--project-keys", ",".join(project_keys_list)]
            if jira_url.strip():
                cli_args += ["--jira-url", jira_url]
            if jira_email.strip():
                cli_args += ["--jira-email", jira_email]
            if jira_token.strip():
                cli_args += ["--jira-token", jira_token]
            if jira_ticket.strip():
                cli_args += ["--jira-ticket", jira_ticket]

            try:
                rc, out = run_script("step_0_setup.py", cli_args)
                if rc == 0:
                    config = {
                        "git_provider": git_provider,
                        "repo_url": repo_url,
                        "git_username": git_user,
                        "git_password": git_pass,
                        "git_branch": git_branch,
                        "github_owner": github_owner.strip(),
                        "project_keys": project_keys_list,
                        "jira_url": jira_url,
                        "jira_email": jira_email,
                        "jira_token": jira_token,
                        "jira_ticket": jira_ticket,
                        "workspace_dir": workspace_dir,
                    }
                    ss_set("config", config)
                    step_statuses = ss_get("step_status", {})
                    step_statuses[0] = "done"
                    ss_set("step_status", step_statuses)
                    st.success("✅ Configuration saved successfully!")
                else:
                    st.error(f"❌ Save failed:\n{out}")
            except Exception as e:
                st.error(f"❌ Error: {e}")


# ── Step 1: Clone & Analyze ─────────────────────────────────────────────────────

def _render_multi_repo_results(multi_data: dict) -> None:
    """Display aggregate results from a multi-repo scan."""
    agg = multi_data.get("aggregate_stats", {})
    render_metric_cards([
        (multi_data.get("total_repos_succeeded", 0), "Repos Scanned"),
        (multi_data.get("total_repos_failed", 0), "Failed"),
        (agg.get("total_files", 0), "Total Files"),
        (agg.get("total_classes", 0), "Classes"),
        (agg.get("total_api_endpoints", 0), "API Endpoints"),
        (agg.get("test_files", 0), "Test Files"),
    ])

    failed = multi_data.get("failed_repos", [])
    if failed:
        with st.expander(f"⚠️ {len(failed)} repo(s) failed"):
            for f in failed:
                st.markdown(f"- **{f['repo_name']}**: {f['error']}")

    repos = multi_data.get("repos", [])
    if repos:
        st.markdown(f"#### Repositories ({len(repos)})")
        for repo in repos:
            with st.expander(f"📦 {repo.get('repo_name', repo.get('repo_path', ''))}"):
                s = repo.get("stats", {})
                st.markdown(
                    f"Files: **{repo.get('total_files', 0)}** | "
                    f"Classes: **{s.get('total_classes', 0)}** | "
                    f"Functions: **{s.get('total_functions', 0)}** | "
                    f"Endpoints: **{s.get('total_api_endpoints', 0)}**"
                )
                langs = repo.get("languages", {})
                if langs:
                    top = list(langs.items())[:4]
                    st.caption("Languages: " + ", ".join(
                        f"{l} ({i.get('percent', 0)}%)" for l, i in top
                    ))
                fws = repo.get("frameworks", [])
                if fws:
                    st.caption("Frameworks: " + ", ".join(fws[:5]))

    with st.expander("📄 Full Multi-Repo Report JSON"):
        st.json(multi_data)


def render_analyze():
    render_step_header(1)

    config = ss_get("config", {})
    analysis = ss_get("analysis")
    multi_analysis = ss_get("multi_analysis")

    git_provider = config.get("git_provider", "bitbucket")
    has_multi_scope = bool(
        config.get("github_owner") or config.get("project_keys")
    )

    # ── Scan mode toggle ─────────────────────────────────────────────────────────
    scan_mode = st.radio(
        "Scan Mode",
        options=["Single Repository", "Multi-Repository Scan"],
        horizontal=True,
        help=(
            "Multi-Repository Scan requires GitHub Owner or Bitbucket Project Keys "
            "to be configured in Step 0."
        ),
    )

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════════
    # Single-repo mode (original behaviour)
    # ════════════════════════════════════════════════════════════════════════════
    if scan_mode == "Single Repository":
        col1, col2 = st.columns([2, 1])
        with col1:
            repo_url_override = st.text_input(
                "Repository URL (optional override)",
                value=config.get("repo_url", config.get("bitbucket_url", "")),
                placeholder="https://github.com/org/repo.git  or  https://bitbucket.example.com/scm/PROJ/repo.git",
            )
        with col2:
            local_path = st.text_input(
                "Or analyze local path",
                placeholder="D:/path/to/repo-root  (or workspace parent folder)",
                help="Point to the repo root (the folder that contains the code). "
                     "If you enter a workspace/clone-parent folder, the tool will "
                     "auto-detect the git repo subfolder inside it.",
            )

        if st.button("🔍 Clone & Analyze Repository", use_container_width=True, type="primary"):
            args = []
            if local_path.strip():
                args += ["--local-path", local_path.strip()]
            else:
                if repo_url_override:
                    args += ["--repo-url", repo_url_override]
                if config.get("workspace_dir"):
                    args += ["--workspace-dir", config["workspace_dir"]]

            with st.spinner("Analyzing repository... (this may take a minute)"):
                rc, output = run_script("step_1_analyze.py", args)

            ss_set("terminal_logs", {**ss_get("terminal_logs", {}), 1: output})

            if rc == 0:
                data = load_workspace_file("analysis_report.json")
                if data:
                    ss_set("analysis", data)
                    step_statuses = ss_get("step_status", {})
                    step_statuses[1] = "done"
                    ss_set("step_status", step_statuses)
                    st.success("✅ Analysis complete!")
                else:
                    st.error("❌ Analysis ran but report not found.")
            else:
                st.error("❌ Analysis failed.")

        # Terminal output (single-repo)
        logs = ss_get("terminal_logs", {}).get(1, "")
        if logs:
            with st.expander("📟 Terminal Output", expanded=not analysis):
                render_terminal(logs)

        if analysis:
            stats = analysis.get("stats", {})
            render_metric_cards([
                (analysis.get("total_files", 0), "Total Files"),
                (stats.get("total_classes", 0), "Classes"),
                (stats.get("total_functions", 0), "Functions"),
                (stats.get("total_api_endpoints", 0), "API Endpoints"),
                (stats.get("total_db_entities", 0), "DB Entities"),
                (stats.get("test_files", 0), "Test Files"),
            ])

            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["🧰 Tech Stack", "🏗️ Architecture", "📚 Code Index", "🌳 Structure", "📄 Full Report"]
            )

            with tab1:
                st.markdown("#### Languages")
                langs = analysis.get("languages", {})
                for lang, info in list(langs.items())[:10]:
                    pct = info.get("percent", 0)
                    st.markdown(f"**{lang}** — {info.get('count', 0)} files ({pct}%)")
                    st.progress(int(pct))

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### Frameworks")
                    for fw in analysis.get("frameworks", []):
                        st.markdown(f"- {fw}")
                with col2:
                    st.markdown("#### Build Tools")
                    for bt in analysis.get("build_tools", []):
                        st.markdown(f"- {bt}")

            with tab2:
                st.markdown("#### Architecture Patterns")
                arch = analysis.get("architecture", [])
                cols = st.columns(min(len(arch), 4) or 1)
                for i, pattern in enumerate(arch):
                    cols[i % len(cols)].markdown(
                        f'<span class="badge badge-review">{pattern}</span>',
                        unsafe_allow_html=True,
                    )
                st.markdown("#### Directory Structure")
                tree = analysis.get("directory_tree", {})
                children = tree.get("children", {})
                cols = st.columns(min(len(children), 4) or 1)
                for i, (name, node) in enumerate(list(children.items())[:12]):
                    icon = "📁" if node.get("type") == "dir" else "📄"
                    cols[i % len(cols)].markdown(f"{icon} **{name}**")

            with tab3:
                code_index = analysis.get("code_index", {})
                ci_tab1, ci_tab2, ci_tab3, ci_tab4 = st.tabs(
                    ["Classes", "Functions", "API Endpoints", "DB Entities"]
                )
                with ci_tab1:
                    items = code_index.get("classes", [])
                    st.markdown(f"**{len(items)} classes**")
                    for item in items[:100]:
                        st.text(f"  {item.get('name')} — {item.get('file')}:{item.get('line', '')}")
                with ci_tab2:
                    items = code_index.get("functions", [])
                    st.markdown(f"**{len(items)} functions**")
                    for item in items[:100]:
                        st.text(f"  {item.get('name')} — {item.get('file')}:{item.get('line', '')}")
                with ci_tab3:
                    items = code_index.get("api_endpoints", [])
                    st.markdown(f"**{len(items)} endpoints**")
                    for item in items[:100]:
                        st.text(f"  {item.get('path')} — {item.get('file')}")
                with ci_tab4:
                    items = code_index.get("db_entities", [])
                    st.markdown(f"**{len(items)} entities**")
                    for item in items[:50]:
                        st.text(f"  {item.get('name')} — {item.get('file')}")

            with tab4:
                def render_tree(node, prefix="", max_depth=3, current_depth=0):
                    if current_depth >= max_depth:
                        return
                    children = node.get("children", {})
                    for name, child in list(children.items())[:30]:
                        icon = "📁" if child.get("type") == "dir" else "📄"
                        st.text(f"{prefix}{icon} {name}")
                        if child.get("type") == "dir":
                            render_tree(child, prefix + "  ", max_depth, current_depth + 1)

                render_tree(analysis.get("directory_tree", {}))

            with tab5:
                st.json(analysis)

    # ════════════════════════════════════════════════════════════════════════════
    # Multi-repo mode
    # ════════════════════════════════════════════════════════════════════════════
    else:
        git_provider = config.get("git_provider", "bitbucket")
        has_github = bool(config.get("github_owner"))
        has_bitbucket = bool(config.get("project_keys"))

        if not has_github and not has_bitbucket:
            st.warning(
                "⚠️ No multi-repo scope configured. "
                "Go to **Step 0 — Setup** and fill in "
                "**GitHub Owner** (for GitHub) or "
                "**Bitbucket Project Keys** (for Bitbucket)."
            )
        else:
            # Show current scope
            if git_provider == "github":
                owner = config.get("github_owner", "")
                st.info(f"Will scan all repositories under GitHub owner: **{owner}**")
            else:
                keys = config.get("project_keys", [])
                st.info(f"Will scan all repositories under Bitbucket project(s): **{', '.join(keys)}**")

            # Extra CLI args
            col_l, col_r = st.columns(2)
            with col_l:
                keep_clones = st.checkbox(
                    "Keep cloned repos after scan",
                    value=False,
                    help="By default each repo is deleted after analysis to save disk space.",
                )
            with col_r:
                multi_out = st.text_input(
                    "Output file",
                    value="multi_analysis_report.json",
                )

            if st.button("🔁 Start Multi-Repo Scan", use_container_width=True, type="primary"):
                args = ["--multi-repo"]
                if git_provider == "github":
                    args += ["--github-owner", config.get("github_owner", "")]
                else:
                    keys = config.get("project_keys", [])
                    if keys:
                        args += ["--project-keys"] + keys
                if keep_clones:
                    args.append("--no-cleanup")
                if multi_out.strip():
                    args += ["--multi-output", multi_out.strip()]
                if config.get("workspace_dir"):
                    args += ["--workspace-dir", config["workspace_dir"]]

                with st.spinner("Scanning repositories… this may take several minutes."):
                    rc, output = run_script("step_1_analyze.py", args)

                ss_set("terminal_logs", {**ss_get("terminal_logs", {}), 1: output})

                if rc == 0:
                    data = load_workspace_file(multi_out.strip() or "multi_analysis_report.json")
                    if data:
                        ss_set("multi_analysis", data)
                        step_statuses = ss_get("step_status", {})
                        step_statuses[1] = "done"
                        ss_set("step_status", step_statuses)
                        n = data.get("total_repos_succeeded", 0)
                        f = data.get("total_repos_failed", 0)
                        st.success(f"✅ Multi-repo scan complete! {n} succeeded, {f} failed.")
                    else:
                        st.error("❌ Scan ran but report not found.")
                else:
                    st.error("❌ Multi-repo scan failed.")

            logs = ss_get("terminal_logs", {}).get(1, "")
            if logs:
                with st.expander("📟 Terminal Output", expanded=not multi_analysis):
                    render_terminal(logs)

            if multi_analysis:
                st.markdown("---")
                st.markdown("#### Multi-Repo Scan Results")
                _render_multi_repo_results(multi_analysis)


# ── Step 2: Fetch Requirements ──────────────────────────────────────────────────

def _render_requirement_card(requirement: dict) -> None:
    """Shared display card for any loaded requirement."""
    status = requirement.get("status", "Unknown")
    priority = requirement.get("priority", "")
    issue_type = requirement.get("type", "")
    source = requirement.get("source", "jira")
    source_label = " (manual)" if source == "manual" else ""
    st.markdown(
        f'<div class="ticket-card">'
        f'<div style="font-size:1.1em;font-weight:700;color:#e6edf3;margin-bottom:8px">'
        f'🎫 {requirement.get("ticket_id")} — {requirement.get("summary", "")}'
        f'{source_label}'
        f'</div>'
        f'<div>{status_badge(status)} &nbsp; '
        f'<span style="color:#8b949e;font-size:0.85em">'
        f'Priority: {priority} | Type: {issue_type} | '
        f'Assignee: {requirement.get("assignee", "Unassigned")}'
        f'</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    render_metric_cards([
        (requirement.get("story_points", 0), "Story Points"),
        (len(requirement.get("subtasks", [])), "Sub-tasks"),
        (len(requirement.get("linked_issues", [])), "Linked Issues"),
        (len(requirement.get("comments", [])), "Comments"),
        (len(requirement.get("attachments", [])), "Attachments"),
    ])
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📝 Description", "✅ Acceptance Criteria", "🔗 Sub-tasks", "🔗 Links", "📄 Full JSON"]
    )
    with tab1:
        desc = requirement.get("description", "*No description*")
        st.markdown(desc[:3000] if desc else "*No description*")
    with tab2:
        ac = requirement.get("acceptance_criteria", "")
        if ac:
            st.markdown(ac[:2000])
        else:
            st.info("No acceptance criteria found.")
    with tab3:
        subtasks = requirement.get("subtasks", [])
        if subtasks:
            for st_item in subtasks:
                badge = status_badge(st_item.get("status", ""))
                st.markdown(
                    f'**{st_item.get("id")}** — {st_item.get("summary", "")} {badge}',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No sub-tasks.")
    with tab4:
        links = requirement.get("linked_issues", [])
        if links:
            for link in links:
                badge = status_badge(link.get("status", ""))
                st.markdown(
                    f'**{link.get("key")}** ({link.get("type", "")}) — '
                    f'{link.get("summary", "")} {badge}',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No linked issues.")
    with tab5:
        st.json(requirement)


def render_jira():
    render_step_header(2)

    config = ss_get("config", {})
    requirement = ss_get("requirement")
    has_jira = bool(config.get("jira_url") and config.get("jira_email") and config.get("jira_token"))

    # Choose input mode
    tab_jira, tab_manual = st.tabs([
        "📋 Fetch from Jira" + ("" if has_jira else " *(not configured)*"),
        "✏️ Enter Manually",
    ])

    # ── Tab 1: Jira fetch ────────────────────────────────────────────────────────
    with tab_jira:
        if not has_jira:
            st.warning(
                "Jira is not configured. Go to **Step 0 — Setup** and fill in the Jira section, "
                "or use the **Enter Manually** tab."
            )
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                ticket_id = st.text_input(
                    "Jira Ticket ID",
                    value=config.get("jira_ticket", ""),
                    placeholder="PROJ-123",
                    key="jira_ticket_input",
                )
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                fetch_clicked = st.button("📋 Fetch Ticket", use_container_width=True,
                                          type="primary", key="jira_fetch_btn")

            if fetch_clicked:
                if not ticket_id.strip():
                    st.error("❌ Enter a Jira ticket ID.")
                else:
                    args = ["--ticket", ticket_id.strip()]
                    with st.spinner(f"Fetching {ticket_id}..."):
                        rc, output = run_script("step_2_jira.py", args)
                    ss_set("terminal_logs", {**ss_get("terminal_logs", {}), 2: output})
                    if rc == 0:
                        data = load_workspace_file("requirement.json")
                        if data:
                            ss_set("requirement", data)
                            step_statuses = ss_get("step_status", {})
                            step_statuses[2] = "done"
                            ss_set("step_status", step_statuses)
                            st.success(f"✅ Fetched: {data.get('summary', '')}")
                        else:
                            st.error("❌ Fetch ran but requirement.json not found.")
                    else:
                        st.error("❌ Fetch failed.")

            logs = ss_get("terminal_logs", {}).get(2, "")
            if logs:
                with st.expander("📟 Terminal Output", expanded=not requirement):
                    render_terminal(logs)

    # ── Tab 2: Manual entry ──────────────────────────────────────────────────────
    with tab_manual:
        st.markdown("Enter your requirement directly — no Jira connection needed.")
        m_col1, m_col2 = st.columns([1, 3])
        with m_col1:
            manual_id = st.text_input("Task / Ticket ID", value="MANUAL-1",
                                       key="manual_id")
            manual_type = st.selectbox("Type", ["task", "bug", "story", "feature"],
                                        key="manual_type")
        with m_col2:
            manual_summary = st.text_input("Summary (one line)", key="manual_summary",
                                            placeholder="e.g. Add email validation to registration form")

        manual_desc = st.text_area(
            "Description / Acceptance Criteria",
            height=180,
            key="manual_desc",
            placeholder=(
                "Describe what needs to be done.\n"
                "Include acceptance criteria, affected areas, or any notes."
            ),
        )

        if st.button("💾 Save Manual Requirement", use_container_width=True,
                     type="primary", key="manual_save_btn"):
            if not manual_summary.strip() and not manual_desc.strip():
                st.error("❌ Enter at least a summary or description.")
            else:
                args = [
                    "--manual",
                    "--manual-id", manual_id.strip() or "MANUAL-1",
                    "--manual-summary", manual_summary.strip(),
                    "--manual-description", manual_desc.strip(),
                    "--manual-type", manual_type,
                ]
                with st.spinner("Saving requirement..."):
                    rc, output = run_script("step_2_jira.py", args)
                if rc == 0:
                    data = load_workspace_file("requirement.json")
                    if data:
                        ss_set("requirement", data)
                        step_statuses = ss_get("step_status", {})
                        step_statuses[2] = "done"
                        ss_set("step_status", step_statuses)
                        st.success(f"✅ Requirement saved: {data.get('summary', '')}")
                    else:
                        st.error("❌ Saved but requirement.json not found.")
                else:
                    st.error(f"❌ Failed to save requirement.\n{output}")

    # ── Requirement display (common for both modes) ──────────────────────────────
    if requirement:
        st.markdown("---")
        st.markdown("#### Current Requirement")
        _render_requirement_card(requirement)


# ── Step 3: Map Changes ─────────────────────────────────────────────────────────

def render_map():
    render_step_header(3)

    analysis = ss_get("analysis")
    requirement = ss_get("requirement")
    proposal = ss_get("proposal")

    if not analysis:
        st.warning("⚠️ Complete Step 1 (Clone & Analyze) first.")
        return
    if not requirement:
        st.warning("⚠️ Complete Step 2 (Fetch Requirements) first.")
        return

    if st.button("🗺️ Map Requirements to Code", use_container_width=True, type="primary"):
        with st.spinner("Analyzing relevance... "):
            rc, output = run_script("step_3_map.py")

        ss_set("terminal_logs", {**ss_get("terminal_logs", {}), 3: output})

        if rc == 0:
            data = load_workspace_file("change_proposal.json")
            if data:
                ss_set("proposal", data)
                step_statuses = ss_get("step_status", {})
                step_statuses[3] = "done"
                ss_set("step_status", step_statuses)
                st.success("✅ Mapping complete!")
            else:
                st.error("❌ Mapping ran but proposal not found.")
        else:
            st.error("❌ Mapping failed.")

    logs = ss_get("terminal_logs", {}).get(3, "")
    if logs:
        with st.expander("📟 Terminal Output", expanded=not proposal):
            render_terminal(logs)

    if proposal:
        files_mod = len(proposal.get("files_to_modify", []))
        files_create = len(proposal.get("files_to_create", []))
        files_delete = len(proposal.get("files_to_delete", []))
        notes = len(proposal.get("notes", []))

        render_metric_cards([
            (files_mod, "Files to Modify"),
            (files_create, "Files to Create"),
            (files_delete, "Files to Delete"),
            (notes, "Notes"),
        ])

        st.markdown("#### Files to Modify")
        for file_entry in proposal.get("files_to_modify", [])[:20]:
            fname = file_entry.get("file", "")
            score = file_entry.get("score", 0)
            matches = file_entry.get("matches", [])
            with st.expander(f"📄 {fname} (score: {score})"):
                if matches:
                    st.markdown("**Matched elements:**")
                    for m in matches[:5]:
                        st.text(f"  [{m.get('type')}] {m.get('name')} (+{m.get('score', 0)})")
                locations = file_entry.get("keyword_locations", [])
                if locations:
                    st.markdown("**Keyword locations:**")
                    for loc in locations[:5]:
                        st.markdown(
                            f"Lines {loc.get('start_line')}-{loc.get('end_line')}: "
                            f"`{', '.join(loc.get('keywords_found', [])[:5])}`"
                        )
                        st.code(loc.get("snippet", "")[:300], language="text")

        if proposal.get("notes"):
            st.markdown("#### Notes")
            for note in proposal["notes"]:
                st.info(f"💡 {note}")

        with st.expander("📄 Full Proposal JSON"):
            st.json(proposal)


# ── Step 4: Review & Confirm ────────────────────────────────────────────────────

def render_review():
    render_step_header(4)

    proposal = ss_get("proposal")
    if not proposal:
        st.warning("⚠️ Complete Step 3 (Map Changes) first.")
        return

    files_to_modify = proposal.get("files_to_modify", [])

    st.markdown(f"**{len(files_to_modify)} files identified for modification.**")

    # Select All toggle
    select_all = st.checkbox("Select All Files", value=True)

    # Initialize file selections
    if "file_selections" not in st.session_state:
        st.session_state.file_selections = {i: True for i in range(len(files_to_modify))}

    updated_files = []
    for i, file_entry in enumerate(files_to_modify):
        fname = file_entry.get("file", "")
        is_selected = st.session_state.file_selections.get(i, True)
        if select_all:
            is_selected = True

        with st.expander(f"{'✅' if is_selected else '⬜'} {fname}"):
            checked = st.checkbox("Include this file", value=is_selected, key=f"include_{i}")
            st.session_state.file_selections[i] = checked

            # Add specific changes
            st.markdown("**Add specific change:**")
            change_type = st.selectbox(
                "Change type",
                ["(none)", "replace", "insert_after", "insert_before", "append", "full_replace"],
                key=f"ct_{i}",
            )

            if change_type != "(none)":
                new_change = {"type": change_type}

                if change_type == "replace":
                    old_t = st.text_area("Old text (first occurrence)", key=f"old_{i}", height=80)
                    new_t = st.text_area("New text", key=f"new_{i}", height=80)
                    new_change["old_text"] = old_t
                    new_change["new_text"] = new_t

                elif change_type in ("insert_after", "insert_before"):
                    marker_key = "after_line" if change_type == "insert_after" else "before_line"
                    marker = st.text_input("Line number or text marker", key=f"marker_{i}")
                    new_t = st.text_area("Text to insert", key=f"new_{i}", height=80)
                    new_change[marker_key] = marker
                    new_change["new_text"] = new_t

                elif change_type == "append":
                    new_t = st.text_area("Text to append", key=f"new_{i}", height=80)
                    new_change["new_text"] = new_t

                elif change_type == "full_replace":
                    new_t = st.text_area("Full new content", key=f"new_{i}", height=200)
                    new_change["new_text"] = new_t

                if st.button(f"➕ Add Change", key=f"add_change_{i}"):
                    if "suggested_changes" not in file_entry:
                        file_entry["suggested_changes"] = []
                    file_entry["suggested_changes"].append(new_change)
                    st.success("✅ Change added!")

            # Show existing suggested changes
            if file_entry.get("suggested_changes"):
                st.markdown(f"**{len(file_entry['suggested_changes'])} change(s) queued:**")
                for j, chg in enumerate(file_entry["suggested_changes"]):
                    st.text(f"  [{j + 1}] {chg.get('type')}: "
                            f"{str(chg)[:80]}...")

        file_entry["confirmed"] = st.session_state.file_selections.get(i, True)
        if file_entry.get("confirmed") or select_all:
            file_entry["confirmed"] = True
        updated_files.append(file_entry)

    proposal["files_to_modify"] = updated_files

    if st.button("💾 Save Updated Proposal", use_container_width=True, type="primary"):
        proposal["confirmed"] = True
        save_workspace_file("change_proposal.json", proposal)
        ss_set("proposal", proposal)
        step_statuses = ss_get("step_status", {})
        step_statuses[4] = "done"
        ss_set("step_status", step_statuses)
        confirmed = len([f for f in updated_files if f.get("confirmed")])
        st.success(f"✅ Proposal saved. {confirmed} files confirmed.")


# ── Step 5: Apply Changes ───────────────────────────────────────────────────────

def render_apply():
    render_step_header(5)

    proposal = ss_get("proposal")
    analysis = ss_get("analysis")
    apply_result = ss_get("apply_result")

    if not proposal or not proposal.get("confirmed"):
        st.warning("⚠️ Complete Step 4 (Review & Confirm) first.")
        return

    change_scope = st.radio(
        "Apply scope",
        ["All Changes", "Selected Changes Only"],
        horizontal=True,
    )

    run_tests = st.checkbox("Run tests after applying", value=True)

    if st.button("⚡ Apply Changes", use_container_width=True, type="primary"):
        args = []
        if not run_tests:
            args.append("--no-tests")

        with st.spinner("Applying changes to repository..."):
            rc, output = run_script("step_5_apply.py", args)

        ss_set("terminal_logs", {**ss_get("terminal_logs", {}), 5: output})

        if rc == 0:
            data = load_workspace_file("apply_result.json")
            if data:
                ss_set("apply_result", data)
                step_statuses = ss_get("step_status", {})
                step_statuses[5] = "done"
                ss_set("step_status", step_statuses)
                st.success(f"✅ Changes applied to branch: {data.get('branch', '')}")
            else:
                st.error("❌ Apply ran but result not found.")
        else:
            st.error("❌ Apply failed.")

    logs = ss_get("terminal_logs", {}).get(5, "")
    if logs:
        with st.expander("📟 Terminal Output", expanded=not apply_result):
            render_terminal(logs)

    if apply_result:
        test_res = apply_result.get("test_results", {})
        test_status = "✅ Pass" if test_res.get("passed") else (
            "❌ Fail" if test_res.get("passed") is False else "—"
        )

        render_metric_cards([
            (apply_result.get("files_modified", 0), "Modified"),
            (apply_result.get("files_created", 0), "Created"),
            (apply_result.get("files_deleted", 0), "Deleted"),
            (test_status, "Tests"),
        ])

        st.markdown(f"**Branch:** `{apply_result.get('branch', '')}`")

        diff = apply_result.get("git_diff", {})
        if diff.get("shortstat"):
            st.markdown(f"**Diff:** {diff['shortstat']}")

        if diff.get("stat"):
            with st.expander("📊 git diff --stat"):
                st.code(diff["stat"], language="text")

        if diff.get("full_diff"):
            with st.expander("📄 Full git diff"):
                st.markdown(
                    f'<div class="diff-viewer">{diff["full_diff"][:5000]}</div>',
                    unsafe_allow_html=True,
                )

        if test_res.get("output"):
            with st.expander(f"🧪 Test Output ({test_res.get('framework', '')})"):
                render_terminal(test_res["output"])


# ── Step 6: Commit & Push ───────────────────────────────────────────────────────

def render_commit():
    render_step_header(6)

    apply_result = ss_get("apply_result")
    requirement = ss_get("requirement")
    config = ss_get("config", {})
    commit_result = ss_get("commit_result")

    if not apply_result:
        st.warning("⚠️ Complete Step 5 (Apply Changes) first.")
        return

    # Auto-generate commit message
    ticket_id = (requirement or {}).get("ticket_id", "TICKET")
    summary = (requirement or {}).get("summary", "update")
    issue_type = (requirement or {}).get("type", "task").lower()
    type_map = {
        "bug": "fix", "story": "feat", "feature": "feat",
        "task": "chore", "improvement": "feat",
    }
    commit_type = type_map.get(issue_type, "chore")
    scope = ticket_id.split("-")[0].lower() if "-" in ticket_id else ticket_id.lower()
    default_msg = f"{commit_type}({scope}): {summary[:70]}\n\nJira: {ticket_id}"

    commit_msg = st.text_area("Commit Message", value=default_msg, height=100)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Check Status", use_container_width=True):
            rc, output = run_script("step_6_commit.py", ["--check-status"])
            ss_set("terminal_logs", {**ss_get("terminal_logs", {}), 6: output})

    with col2:
        if st.button("✅ Commit Only", use_container_width=True):
            rc, output = run_script("step_6_commit.py",
                                     ["--commit-message", commit_msg])
            ss_set("terminal_logs", {**ss_get("terminal_logs", {}), 6: output})
            if rc == 0:
                st.success("✅ Committed!")
            else:
                st.error(f"❌ Commit failed.")

    with col3:
        if st.button("🚀 Commit & Push", use_container_width=True, type="primary"):
            rc, output = run_script("step_6_commit.py",
                                     ["--commit-message", commit_msg, "--push"])
            ss_set("terminal_logs", {**ss_get("terminal_logs", {}), 6: output})
            if rc == 0:
                data = load_workspace_file("commit_result.json")
                if data:
                    ss_set("commit_result", data)
                    step_statuses = ss_get("step_status", {})
                    step_statuses[6] = "done"
                    ss_set("step_status", step_statuses)
                st.success("✅ Committed & Pushed!")
                st.balloons()
            else:
                st.error("❌ Push failed.")

    logs = ss_get("terminal_logs", {}).get(6, "")
    if logs:
        with st.expander("📟 Terminal Output", expanded=True):
            render_terminal(logs)

    # PR creation form
    st.markdown("---")
    st.markdown("#### 🔀 Create Pull Request")

    git_provider = config.get("git_provider", "bitbucket")
    provider_label = "GitHub" if git_provider == "github" else "Bitbucket"

    with st.expander(f"🔀 Create {provider_label} Pull Request"):
        pr_title = st.text_input("PR Title",
                                  value=f"{ticket_id}: {summary[:60]}" if requirement else "")
        target_branch = st.text_input("Target Branch", value="main")

        # Bitbucket-only fields
        if git_provider == "bitbucket":
            repo_url_cfg = config.get("repo_url", config.get("bitbucket_url", ""))
            # Auto-parse project key from URL
            default_project_key = ""
            try:
                import re as _re
                m = _re.search(r"/scm/([^/]+)/", repo_url_cfg) or \
                    _re.search(r"/projects/([^/]+)/", repo_url_cfg)
                if m:
                    default_project_key = m.group(1).upper()
            except Exception:
                pass
            project_key = st.text_input("Bitbucket Project Key",
                                         value=default_project_key,
                                         placeholder="MYPROJ")
            repo_slug = st.text_input("Bitbucket Repo Slug",
                                       placeholder="my-service")
        else:
            project_key = ""
            repo_slug = ""
            st.info(f"GitHub PR will be created using the repo from config: "
                    f"`{config.get('repo_url', '')}`")

        pr_desc = st.text_area(
            "PR Description",
            value=f"## {ticket_id}: {summary}\n\n"
                  f"Changes applied by Dev Skill.\n\nJira: {ticket_id}",
            height=150,
        )

        if st.button(f"🔀 Create {provider_label} PR", use_container_width=True):
            args = [
                "--push",
                "--create-pr",
                "--commit-message", commit_msg,
                "--target-branch", target_branch,
            ]
            if project_key:
                args += ["--project-key", project_key]
            if repo_slug:
                args += ["--repo-slug", repo_slug]

            with st.spinner(f"Creating {provider_label} PR..."):
                rc, output = run_script("step_6_commit.py", args)
            ss_set("terminal_logs", {**ss_get("terminal_logs", {}), 6: output})
            if rc == 0:
                data = load_workspace_file("commit_result.json")
                if data and data.get("pr"):
                    pr_url = data["pr"].get("url", "")
                    st.success(f"✅ PR Created: {pr_url}")
                    st.balloons()
                else:
                    st.success("✅ Push completed.")
            else:
                st.error(f"❌ {provider_label} PR creation failed.")

    if commit_result:
        st.markdown("---")
        st.markdown("#### Last Commit Result")
        st.json(commit_result)


# ── Main routing ─────────────────────────────────────────────────────────────────

def main():
    render_sidebar()

    current_step = ss_get("current_step", 0)
    render_pipeline_bar(current_step)

    step_renderers = {
        0: render_setup,
        1: render_analyze,
        2: render_jira,
        3: render_map,
        4: render_review,
        5: render_apply,
        6: render_commit,
    }

    renderer = step_renderers.get(current_step, render_setup)
    renderer()


if __name__ == "__main__":
    main()
