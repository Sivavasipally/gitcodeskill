# Git + Jira Dev Skill

A production-ready Python automation system that drives the full development workflow —
from a requirement to a committed, tested, pushed code change — with a Streamlit UI dashboard.

Supports **GitHub** and **Bitbucket Server/Cloud**. Jira is **optional** — requirements
can be entered manually in the UI or via CLI instead.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Setup & Configuration](#setup--configuration)
5. [Running the Streamlit UI](#running-the-streamlit-ui)
6. [Running via CLI / Orchestrator](#running-via-cli--orchestrator)
7. [File Reference](#file-reference)
8. [Workflow Walkthrough](#workflow-walkthrough)
9. [Output Files](#output-files)
10. [Enterprise Notes](#enterprise-notes)
11. [Troubleshooting](#troubleshooting)
12. [Windows-Specific Notes](#windows-specific-notes)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     app.py  (Streamlit UI)                  │
│  Sidebar nav ──► Step screens ──► subprocess.run() calls    │
└────────────────────────────┬────────────────────────────────┘
                             │ subprocess calls
         ┌───────────────────▼───────────────────┐
         │          orchestrator.py               │
         │  --full (end-to-end) | --step N        │
         └──┬────┬────┬────┬────┬────┬────────────┘
            │    │    │    │    │    │
     step_0 ▼  step_1▼  step_2▼  step_3▼  step_4▼  step_5▼  step_6
     Setup  Analyze  Req    Map   Review  Apply   Commit
            │         │      │       │       │       │
            ▼         ▼      ▼       ▼       ▼       ▼
       analysis_  require- change_  (same) apply_  commit_
       report.json ment.json proposal.json result.json result.json
```

Each step script is **fully standalone** (run directly via CLI) and also callable
from the Streamlit UI or orchestrator via `subprocess.run()`.

---

## Prerequisites

| Requirement | Minimum Version | Notes |
|-------------|----------------|-------|
| Python | 3.8+ | |
| Git | 2.x | Must be on PATH |
| GitHub or Bitbucket | Any | Cloud and Server supported |
| Jira | Cloud or Server | **Optional** — can enter requirements manually |
| Optional: `black` | any | Python auto-formatter |
| Optional: `isort` | any | Python import sorter |
| Optional: `prettier` | any | JS/TS auto-formatter |
| Optional: `mvn` / `mvn.cmd` | any | Java/Maven build & format |

> **Windows note:** Git must be installed and `git.exe` on your `PATH`.
> Install [Git for Windows](https://gitforwindows.org/) which includes Git Bash.
> All `npm`, `mvn`, `prettier` tools are auto-discovered including `.cmd` wrappers.

---

## Installation

### Windows

```powershell
# 1. Install Python 3.8+ from https://python.org — tick "Add to PATH"
# 2. Install Git from https://gitforwindows.org
# 3. Open Command Prompt or PowerShell in the project folder
pip install -r requirements.txt

# 4. Launch UI
streamlit run app.py
```

> If you see "externally managed environment" on newer Python:
> ```powershell
> pip install -r requirements.txt --break-system-packages
> ```
> Or use a virtual environment (see below).

### Linux / macOS

```bash
# 1. Ensure Python 3.8+ and git are installed
python3 --version
git --version

# 2. Install dependencies
pip install -r requirements.txt
# On Debian/Ubuntu 23+ with externally-managed Python:
pip install -r requirements.txt --break-system-packages

# 3. Launch UI
streamlit run app.py
```

### Using a virtual environment (recommended on both platforms)

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py

# Windows (Command Prompt)
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run app.py
```

### Verify installation

```bash
# Linux/macOS
python3 -c "import streamlit, requests, pathspec; print('OK')"

# Windows
python -c "import streamlit, requests, pathspec; print('OK')"
```

---

## Setup & Configuration

Credentials are stored in `config/config.json` inside the project folder.
An `example_config.json` is included — copy and fill it in.
Passwords are never logged — displayed as `first4****last4`.

### config/config.json — field reference

| Field | Required | Description |
|-------|----------|-------------|
| `git_provider` | yes | `"github"` or `"bitbucket"` (auto-detected from URL if omitted) |
| `repo_url` | yes | Full repository clone URL (used for single-repo mode and for deriving the Bitbucket base URL) |
| `git_username` | yes | GitHub login or Bitbucket username |
| `git_password` | yes | GitHub PAT or Bitbucket App Password (never your login password) |
| `git_branch` | yes | Default branch to clone (e.g. `main`, `develop`) |
| `github_owner` | **optional** | GitHub user or organisation name — enables multi-repo scan of all repos under this owner |
| `project_keys` | **optional** | List of Bitbucket project keys e.g. `["PROJ1","PROJ2"]` — enables multi-repo scan across all listed projects |
| `jira_url` | **optional** | Jira base URL — leave blank to enter requirements manually |
| `jira_email` | optional | Email for Jira authentication |
| `jira_token` | optional | Jira API token |
| `jira_ticket` | optional | Default ticket ID — can be overridden per run |
| `workspace_dir` | yes | Local directory where repositories will be cloned |

### Option A — Copy example config and edit

```bash
# Linux/macOS
cp example_config.json config/config.json
nano config/config.json      # fill in values, remove _ comment keys

# Windows (PowerShell)
Copy-Item example_config.json config\config.json
notepad config\config.json
```

### Option B — Interactive (prompts in terminal)

```bash
python step_0_setup.py
```

Prompts for all fields one by one. Press Enter to keep existing values.

### Option C — CLI flags (for scripting / CI)

**GitHub — Linux / macOS / Git Bash:**
```bash
python step_0_setup.py \
  --git-provider  github \
  --repo-url      https://github.com/your-org/your-repo.git \
  --git-username  john.doe \
  --git-password  ghp_YourPersonalAccessToken \
  --git-branch    main \
  --workspace-dir /home/john/dev-workspace
```

**GitHub — Windows (PowerShell):**
```powershell
python step_0_setup.py `
  --git-provider  github `
  --repo-url      "https://github.com/your-org/your-repo.git" `
  --git-username  "john.doe" `
  --git-password  "ghp_YourPersonalAccessToken" `
  --git-branch    "main" `
  --workspace-dir "C:\Users\john\dev-workspace"
```

**Bitbucket + Jira — Linux / macOS / Git Bash:**
```bash
python step_0_setup.py \
  --git-provider  bitbucket \
  --repo-url      https://bitbucket.example.com/scm/MYPROJ/my-service.git \
  --git-username  john.doe \
  --git-password  myAppPassword123 \
  --git-branch    main \
  --jira-url      https://jira.example.com \
  --jira-email    john.doe@company.com \
  --jira-token    ATATT3xFfGF0... \
  --jira-ticket   PROJ-123 \
  --workspace-dir /home/john/dev-workspace
```

**Bitbucket + Jira — Windows (PowerShell):**
```powershell
python step_0_setup.py `
  --git-provider  bitbucket `
  --repo-url      "https://bitbucket.example.com/scm/MYPROJ/my-service.git" `
  --git-username  "john.doe" `
  --git-password  "myAppPassword123" `
  --git-branch    "main" `
  --jira-url      "https://jira.example.com" `
  --jira-email    "john.doe@company.com" `
  --jira-token    "ATATT3xFfGF0..." `
  --jira-ticket   "PROJ-123" `
  --workspace-dir "C:\Users\john\dev-workspace"
```

**GitHub — with multi-repo owner (scan all org repos):**
```bash
python step_0_setup.py \
  --git-provider  github \
  --repo-url      https://github.com/your-org/any-repo.git \
  --git-username  john.doe \
  --git-password  ghp_YourPersonalAccessToken \
  --github-owner  your-org \
  --workspace-dir /home/john/dev-workspace
```

**Bitbucket — with multiple project keys (scan repos across projects):**
```bash
python step_0_setup.py \
  --git-provider  bitbucket \
  --repo-url      https://bitbucket.example.com/scm/PROJ1/any-repo.git \
  --git-username  john.doe \
  --git-password  myAppPassword123 \
  --project-keys  "PROJ1,PROJ2,PROJ3" \
  --workspace-dir /home/john/dev-workspace
```

**Windows (Command Prompt — single line):**
```cmd
python step_0_setup.py --git-provider github --repo-url "https://github.com/org/repo.git" --git-username "john.doe" --git-password "ghp_token" --workspace-dir "C:\Users\john\dev-workspace"
```

### Option D — Streamlit UI (Step 0 screen)

Launch the UI, select the provider (GitHub / Bitbucket) with the radio toggle,
fill in the form, and click **Save Configuration**. Includes live connection test buttons.
Jira section is clearly marked optional. A "Multi-Repository Scan" section at the bottom
of Step 0 lets you set the GitHub Owner or Bitbucket Project Keys directly in the UI.

### View current configuration

```bash
python step_0_setup.py --show
```

---

## Running the Streamlit UI

```bash
streamlit run app.py
```

Opens at `http://localhost:8501` by default.

### Dashboard Layout

```
┌──────────────────────────────────────────────────────────────┐
│ Sidebar                │  Main Content Area                   │
│                        │                                      │
│ ✅ 0. Setup & Config   │  [Pipeline progress bar]             │
│ ✅ 1. Clone & Analyze  │                                      │
│ 🔄 2. Fetch Reqs       │  Step header (icon + name + desc)    │
│ ⬜ 3. Map Changes      │                                      │
│ ⬜ 4. Review           │  Step-specific content               │
│ ⬜ 5. Apply Changes    │  (forms, buttons, metric cards,      │
│ ⬜ 6. Commit & Push    │   terminal output, tabs)             │
│                        │                                      │
│ ─────────────────────  │                                      │
│ 🔄 Reset All           │                                      │
│ 📁 View Workspace      │                                      │
└──────────────────────────────────────────────────────────────┘
```

Navigate between steps using the sidebar buttons. Status icons update automatically:
- `✅` — Step completed
- `🔄` — Step currently active
- `⬜` — Step not yet started

### Step 1 — Clone & Analyze (Single or Multi-Repo)

Step 1 shows a **Scan Mode** radio at the top:

| Mode | When to use |
|------|-------------|
| **Single Repository** | Analyze one specific repo (from config URL or override) |
| **Multi-Repository Scan** | Scan all repos under a GitHub owner or Bitbucket project key(s) |

Multi-Repo Scan requires `github_owner` or `project_keys` to be set in Step 0.
The scan runs sequentially — each repo is cloned, analyzed, and deleted before the next.
Results are shown as aggregate metrics + per-repo expandable cards.

### Step 2 — Requirements (Jira or Manual)

Step 2 shows **two tabs**:

| Tab | When to use |
|-----|-------------|
| **Fetch from Jira** | Jira URL/email/token configured in Step 0 |
| **Enter Manually** | No Jira, or for ad-hoc tasks — type summary + description directly |

Both produce the same `requirement.json` consumed by all later steps.

---

## Running via CLI / Orchestrator

### Full end-to-end run (with Jira)

```bash
python orchestrator.py --full --ticket PROJ-123
```

Runs all 7 steps in sequence. Pauses at Step 4 for human review.

### Full run with auto-approval (no pause)

```bash
python orchestrator.py --full --ticket PROJ-123 --auto-apply
```

### Full run + push branch

```bash
python orchestrator.py --full --ticket PROJ-123 --auto-apply --push
```

### Full run + push + create PR

```bash
python orchestrator.py --full --ticket PROJ-123 --auto-apply --push --create-pr \
  --target-branch develop
```

### Run a single step

```bash
python orchestrator.py --step 0          # Setup
python orchestrator.py --step 1          # Clone & Analyze
python orchestrator.py --step 2 --ticket PROJ-456    # Fetch from Jira
python orchestrator.py --step 3          # Map
python orchestrator.py --step 4 --confirmed-changes all    # Auto-confirm all
python orchestrator.py --step 4 --confirmed-changes "1,3,5"   # Cherry-pick
python orchestrator.py --step 5          # Apply
python orchestrator.py --step 5 --no-tests   # Apply without running tests
python orchestrator.py --step 6 --push   # Commit & push
```

### Multi-repository scan (CLI)

Scan **all** repositories under a GitHub owner or across multiple Bitbucket project keys.
Each repo is cloned, analyzed, and deleted before moving to the next.

```bash
# GitHub — scan every repo under an org/user
python step_1_analyze.py --multi-repo --github-owner your-org

# Bitbucket — scan every repo in one or more project keys
python step_1_analyze.py --multi-repo --project-keys PROJ1 PROJ2 PROJ3

# Keep clones on disk (skip auto-delete after analysis)
python step_1_analyze.py --multi-repo --github-owner your-org --no-cleanup

# Custom output file name
python step_1_analyze.py --multi-repo --github-owner your-org \
  --multi-output /tmp/org_scan.json
```

Output: `multi_analysis_report.json` — contains per-repo analysis plus aggregate totals.

---

### Run each script directly

Every step script also runs standalone:

```bash
python step_0_setup.py --show
python step_1_analyze.py --repo-url https://github.com/org/repo.git --workspace-dir ~/workspace
python step_1_analyze.py --local-path /path/to/existing/repo

# Jira mode
python step_2_jira.py --ticket PROJ-123
python step_2_jira.py --test-connection

# Manual mode (no Jira needed)
python step_2_jira.py --manual
python step_2_jira.py --manual --manual-id TASK-1 --manual-summary "Add email validation" \
  --manual-description "Validate email format on registration form" --manual-type task

python step_3_map.py
python step_4_review.py --show-only
python step_4_review.py --confirmed-changes all
python step_5_apply.py --no-tests
python step_6_commit.py --check-status
python step_6_commit.py --push
python step_6_commit.py --push --create-pr --target-branch develop

# Bitbucket-only: specify project key and repo slug explicitly
python step_6_commit.py --push --create-pr --project-key MYPROJ --repo-slug my-service
```

---

## File Reference

### `step_0_setup.py` — Setup & Configuration

**Purpose:** Collects Git provider (GitHub / Bitbucket) and optional Jira credentials,
saves them to `config/config.json` inside the project folder.

**What it does:**
- Saves config to `<project>/config/config.json` — location is project-relative, not home directory
- Sets file permissions cross-platform: `chmod 600` on Linux/macOS; no-op on Windows (NTFS ACLs apply)
- All file I/O uses explicit `encoding="utf-8"` — safe on all locales and platforms
- Masks sensitive values in display (`first4****last4`)
- Validates required git fields; validates Jira fields only if any Jira field is provided
- Supports interactive prompts (with defaults shown) or full CLI args
- Backward-compatible: old `--bitbucket-url` / `--bitbucket-username` / `--bitbucket-password` flags
  still accepted and mapped to the new unified field names

**Key functions:**
- `_restrict_file_permissions(path)` — cross-platform permission setter
- `save_config(config)` — writes UTF-8 JSON and restricts permissions
- `load_config()` — reads and returns the stored config dict
- `validate_config(config)` — returns list of missing field errors (Jira optional)
- `mask_credential(value)` — masks passwords for display
- `interactive_setup()` — prompt-driven config collection
- `cli_setup(args)` — CLI args-driven config collection

**Config fields written:**

| Field | Required |
|-------|----------|
| `git_provider` | yes (`github` or `bitbucket`) |
| `repo_url` | yes |
| `git_username` | yes |
| `git_password` | yes |
| `git_branch` | yes |
| `github_owner` | optional — GitHub user/org for multi-repo scan |
| `project_keys` | optional — list of Bitbucket project keys for multi-repo scan |
| `jira_url` | optional |
| `jira_email` | optional |
| `jira_token` | optional |
| `jira_ticket` | optional |
| `workspace_dir` | yes |

**CLI usage:**
```bash
python step_0_setup.py                        # Interactive
python step_0_setup.py --show                 # Show current config (masked)
python step_0_setup.py --git-provider github --repo-url https://github.com/org/repo.git \
  --git-username john --git-password ghp_token --github-owner your-org
python step_0_setup.py --git-provider bitbucket \
  --repo-url https://bitbucket.example.com/scm/P1/repo.git \
  --git-username john --git-password appPass \
  --project-keys "PROJ1,PROJ2"
```

---

### `step_1_analyze.py` — Clone & Analyze Repository

**Purpose:** Clones (or pulls) a repository and produces a deep analysis of its tech stack,
code structure, and content. Works with any Git host — GitHub or Bitbucket.
Supports both **single-repo** and **multi-repo** scan modes.

**What it does:**
- Reads `repo_url`, `git_username`, `git_password`, `git_branch` from config
  (falls back to old `bitbucket_*` keys for backward compatibility)
- Clones with authenticated URL (`scheme://user:pass@host/path`) or pulls if repo exists
- Respects `.gitignore` via `pathspec` library — paths are normalised to POSIX forward-slashes before matching (works correctly on Windows)
- All relative path construction uses `Path.relative_to().as_posix()` via the `to_posix_rel()` helper — no hardcoded path separators
- Skips `node_modules`, `.git`, `__pycache__`, `build`, `dist`, `target`, `venv`, etc.
- Detects **languages** by file extension (Java, Python, JS, TS, Go, Rust, C#, etc.)
- Detects **frameworks**: Spring Boot, React, Angular, Vue, NestJS, FastAPI, Django, Flask, Next.js, etc.
- Detects **build tools**: Maven, Gradle, npm, yarn, pip, poetry, Cargo, Docker
- Detects **architecture patterns**: Microservices, Monorepo, MVC, Layered, API Gateway, Event-Driven
- Builds a **searchable code index** via regex
- Extracts **config files**: `.env`, `application.yml`, `appsettings.json`, etc.
- Detects **test setup**: directories, frameworks (JUnit, pytest, Jest, Cypress, Playwright)
- Generates a **3-level directory tree**
- Fetches **git metadata**: current branch, last 10 commits, branches, remotes

**Multi-repo mode** (`--multi-repo`):
1. Calls `repo_discovery.py` to list all repos via the provider API
2. For each repo: clone → analyze → **delete clone from local disk** (unless `--no-cleanup`)
3. Collects per-repo analysis and writes an aggregated `multi_analysis_report.json`
4. Prints progress as `[N/total] Processing: repo-name`

**Key functions:**
- `analyze(repo_path, logs)` — full single-repo analysis
- `analyze_single(repo_url, ...)` — clone + analyze + optional cleanup for one repo
- `multi_repo_scan(repos, ...)` — iterate repo list, call `analyze_single`, aggregate
- `remove_repo(repo_path, logs)` — `shutil.rmtree` cleanup after analysis

**Output:** `analysis_report.json` (single-repo) or `multi_analysis_report.json` (multi-repo)

**CLI usage:**
```bash
# Single-repo
python step_1_analyze.py
python step_1_analyze.py --repo-url https://github.com/org/repo.git
python step_1_analyze.py --repo-url https://bitbucket.example.com/scm/PROJ/repo.git
python step_1_analyze.py --local-path /path/to/existing/repo
python step_1_analyze.py --output my_report.json

# Multi-repo
python step_1_analyze.py --multi-repo --github-owner your-org
python step_1_analyze.py --multi-repo --project-keys PROJ1 PROJ2
python step_1_analyze.py --multi-repo --github-owner your-org --no-cleanup
python step_1_analyze.py --multi-repo --project-keys PROJ1 --multi-output scan.json
```

---

### `repo_discovery.py` — Multi-Repository Discovery

**Purpose:** Lists all repositories for a given GitHub owner/organisation or one or more
Bitbucket project keys via their respective REST APIs. Used internally by `step_1_analyze.py`
in multi-repo mode.

**Providers supported:**

| Provider | API used | Authentication |
|----------|----------|---------------|
| GitHub | `GET /orgs/{owner}/repos` or `/users/{owner}/repos` | Bearer token (PAT) |
| Bitbucket Server | `GET /rest/api/1.0/projects/{key}/repos` | Basic auth (username + app-password) |
| Bitbucket Cloud | `GET /2.0/repositories/{workspace}` | Basic auth |

**Key functions:**
- `list_github_repos(owner, token)` — paginates through all repos under a user or org; auto-detects org vs user
- `list_bitbucket_server_repos(base_url, project_key, username, password)` — paginates a single project key
- `list_bitbucket_cloud_repos(workspace, username, app_password)` — paginates a Bitbucket Cloud workspace
- `discover_repos(config, project_keys, github_owner)` — unified entry point; routes to the correct provider and iterates multiple project keys

**CLI usage (for testing):**
```bash
# GitHub — list all repos for an org
python repo_discovery.py --github-owner your-org

# Bitbucket — list repos for one or more project keys
python repo_discovery.py --project-keys PROJ1 PROJ2
```

---

### `step_2_jira.py` — Fetch Requirements

**Purpose:** Provides requirements to the rest of the pipeline — either fetched from Jira
or entered as free text. Both modes produce the same `requirement.json` schema.

#### Jira mode

- Authenticates with Jira Cloud or Server via Basic Auth (email + API token)
- Fetches `GET /rest/api/3/issue/{ticket}?expand=renderedFields,names,changelog`
- Converts Atlassian Document Format (ADF) description to plain text/Markdown
- Extracts **acceptance criteria** from custom fields or by parsing the description
- Extracts **story points**, **sprint**, **sub-tasks**, **linked issues**, **comments**, **attachments**

```bash
python step_2_jira.py --ticket PROJ-123
python step_2_jira.py --test-connection
```

#### Manual mode (no Jira needed)

Produces the same `requirement.json` from free-text input. Use when you don't have Jira
or want to describe the task yourself.

```bash
# Interactive (prompts for all fields)
python step_2_jira.py --manual

# Non-interactive (all fields via CLI — good for scripting)
python step_2_jira.py --manual \
  --manual-id   TASK-42 \
  --manual-summary "Add rate limiting to the payments API" \
  --manual-description "Limit to 100 req/min per client. Return 429 on breach." \
  --manual-type task
```

**Manual requirement fields produced:** `ticket_id`, `summary`, `description`,
`type`, `status`, `priority`, `assignee` and all array fields (empty).
`"source": "manual"` is set to distinguish from Jira-fetched data.

**Output:** `requirement.json`

---

### `step_3_map.py` — Map Requirements to Code Changes

**Purpose:** Extracts keywords from the requirement and scores every indexed code element
and file for relevance, producing a ranked change proposal.

**Keyword extraction:**
- Sources: summary, description, acceptance criteria, labels, components, sub-task summaries, comment excerpts
- Splits camelCase and snake_case, removes English stop words

**Relevance scoring (per code element):**

| Match type | Points |
|-----------|--------|
| Exact match (`keyword == element name`) | +10 |
| Substring match (`keyword in name`) | +5 |
| Word-part match (camelCase decomposition) | +3 |
| Full-text frequency per file | +0.5 per hit |

- Returns top **30 files** by aggregate score
- For each file: finds **line ranges** where keywords cluster, top 10 locations with code snippets
- Detects likely config changes and test framework impacts

**Output:** `change_proposal.json`

**CLI usage:**
```bash
python step_3_map.py
python step_3_map.py --analysis my_report.json --requirement my_req.json
```

---

### `step_4_review.py` — Review & Confirm Changes

**Purpose:** Presents the proposal for human review and allows adding specific
change instructions to any file before applying.

**What it does:**
- Displays ranked file list with match details and snippet locations
- Supports confirming **all** files or **cherry-picking** by number
- Adds `suggested_changes` array to any file with typed operations:

| Change type | Parameters | Effect |
|------------|-----------|--------|
| `replace` | `old_text`, `new_text` | Replace first occurrence |
| `insert_after` | `after_line` (number or text), `new_text` | Insert after matching line |
| `insert_before` | `before_line` (number or text), `new_text` | Insert before matching line |
| `append` | `new_text` | Append to end of file |
| `full_replace` | `new_text` | Replace entire file content |

- Can load enrichment from an external JSON file (`--enrichment-file`)
- Saves the updated proposal back to disk

**Output:** Updated `change_proposal.json` with `confirmed: true`

**CLI usage:**
```bash
python step_4_review.py                               # Interactive review
python step_4_review.py --show-only                   # Display without changing
python step_4_review.py --confirmed-changes all       # Auto-confirm everything
python step_4_review.py --confirmed-changes "1,3,5"   # Cherry-pick files 1, 3, 5
python step_4_review.py --enrichment-file enrichments.json
```

---

### `step_5_apply.py` — Apply Changes Locally

**Purpose:** Creates a feature branch and applies all confirmed changes to the repository.

**What it does:**
- Creates branch: `feature/<ticket-id>-<slugified-summary>`
- Applies each `suggested_change` using precise string operations
- Creates new files with parent directory creation
- Deletes specified files
- **Auto-detects and runs formatters** using `find_tool()` (tries plain name, then `.cmd`/`.exe` on Windows):
  - Python files → `black` + `isort`
  - JS/TS files → `prettier --write`
  - Java files with Maven → `mvn spotless:apply`
- **Auto-detects and runs tests**: `pytest`, `npm test`, `yarn test`, `mvn test`
- Generates `git diff --stat`, `--shortstat`, and full diff

**Key functions:**
- `find_tool(*names)` — cross-platform tool discovery (`.cmd`/`.exe` variants on Windows)
- `create_feature_branch(repo_path, ticket_id, summary)` — creates `feature/<id>-<slug>` branch
- `apply_change(content, change)` — dispatches to the correct change type handler

**Output:** `apply_result.json`

**CLI usage:**
```bash
python step_5_apply.py
python step_5_apply.py --no-tests
python step_5_apply.py --repo-path /path/to/repo
```

---

### `step_6_commit.py` — Commit & Push

**Purpose:** Commits applied changes, pushes the feature branch, and optionally creates
a pull request on **GitHub** or **Bitbucket Server**.

**What it does:**
- Generates a **conventional commit message**: `feat(proj): Add payment gateway support`
- Runs `git add -A` → `git commit` → `git push --set-upstream origin <branch>`
- Auto-detects the provider from `config["git_provider"]` (or by sniffing the URL)
- **GitHub PR**: calls `POST https://api.github.com/repos/{owner}/{repo}/pulls` with Bearer token
- **Bitbucket PR**: parses URL for project key + repo slug, calls Bitbucket Server REST API

**Output:** `commit_result.json`

**CLI usage:**
```bash
python step_6_commit.py --check-status
python step_6_commit.py --commit-message "feat(proj): custom message"
python step_6_commit.py --push
python step_6_commit.py --push --create-pr --target-branch develop

# Bitbucket — override project key / repo slug if auto-parse fails
python step_6_commit.py --push --create-pr --project-key MYPROJ --repo-slug my-service
```

---

### `orchestrator.py` — Step Chainer

**Purpose:** Single entry point that chains all steps in sequence or runs any one step.

**Modes:**
- `--full` — Runs steps 0 through 6 end-to-end
- `--step N` — Runs only step N (checks prerequisite files exist)

Config existence is checked at `<project>/config/config.json`.

**Key flags:**

| Flag | Description |
|------|-------------|
| `--full` | End-to-end run |
| `--step N` | Run single step (0-6) |
| `--ticket PROJ-123` | Jira ticket ID |
| `--repo-url URL` | Override repository URL |
| `--workspace-dir DIR` | Override workspace directory |
| `--auto-apply` | Skip Step 4 confirmation pause (confirm all) |
| `--push` | Push branch after Step 5 |
| `--create-pr` | Create PR after push (GitHub or Bitbucket) |
| `--target-branch` | PR target branch (default: `main`) |
| `--no-tests` | Skip test execution in Step 5 |
| `--reconfigure` | Re-run Step 0 even if config exists |
| `--confirmed-changes` | For `--step 4`: `"all"` or `"1,3,5"` |

---

### `app.py` — Streamlit Dashboard

**Purpose:** Full dark-themed web UI for the entire workflow. No manual terminal needed.

**Tech:**
- Streamlit with custom CSS (GitHub dark color scheme)
- Background `#0E1117`, cards `#161b22`, borders `#21262d`
- Primary accent `#6C63FF` (purple), success `#3fb950`, error `#f85149`

**Screens:**

| Step | Screen | Key features |
|------|--------|-------------|
| 0 | Setup | Provider radio (GitHub / Bitbucket), 2-column form, optional Jira section, live connection test buttons; **Multi-repo scope section**: GitHub Owner field (GitHub) or Bitbucket Project Keys field (Bitbucket) |
| 1 | Clone & Analyze | **Scan mode radio** — Single Repository (original) or Multi-Repository Scan; single mode: one-click analyze + 5-tab results; multi mode: scope info, start scan button, aggregate metrics + per-repo expandable cards |
| 2 | Fetch Requirements | **Two tabs**: Fetch from Jira (if configured) OR Enter Manually; shared result display |
| 3 | Map Changes | File list with expandable match details and code snippets |
| 4 | Review | Checkbox per file, inline change editor (type dropdown + text areas) |
| 5 | Apply | Terminal output, metric cards, git diff viewers, test result display |
| 6 | Commit & Push | Editable commit message, 3 action buttons, provider-aware PR creation form (GitHub shows repo info; Bitbucket shows project key/slug fields) |

---

### `config/config.json` — Project Configuration

Stored inside the project at `config/config.json`. Listed in `.gitignore` — never committed.

```json
{
  "git_provider": "github",
  "repo_url": "https://github.com/your-org/your-repo.git",
  "git_username": "your-username",
  "git_password": "your-token-or-app-password",
  "git_branch": "main",
  "github_owner": "your-org",
  "project_keys": [],
  "jira_url": "",
  "jira_email": "",
  "jira_token": "",
  "jira_ticket": "",
  "workspace_dir": "/home/you/workspaces"
}
```

`github_owner` and `project_keys` are optional — leave them blank / empty to use
single-repo mode only. See `example_config.json` for annotated field descriptions.

---

### `requirements.txt` — Dependencies

```
streamlit>=1.28.0    # Web UI framework
requests>=2.28.0     # HTTP client for Jira, GitHub, and Bitbucket REST APIs
pathspec>=0.11.0     # .gitignore-aware file walking
```

---

## Workflow Walkthrough

### Step 1 — Configure credentials

```bash
python step_0_setup.py
# Choose provider: github or bitbucket
# Enter repo URL, username, token/app-password
# Optionally enter Jira URL, email, API token
# Set workspace directory
```

### Step 2 — Analyze the repository

**Single repo:**
```bash
python step_1_analyze.py
# Clones repo into workspace/repo-name
# Scans all non-ignored files
# Produces analysis_report.json
```

**All repos under a GitHub org or across Bitbucket projects:**
```bash
# GitHub
python step_1_analyze.py --multi-repo --github-owner your-org

# Bitbucket
python step_1_analyze.py --multi-repo --project-keys PROJ1 PROJ2

# Each repo is cloned, analyzed, then deleted automatically.
# Produces multi_analysis_report.json with per-repo results + aggregate totals.
```

### Step 3 — Provide requirements

```bash
# From Jira:
python step_2_jira.py --ticket PROJ-123

# Or manually (no Jira needed):
python step_2_jira.py --manual --manual-summary "Fix null pointer in payment service"
# Produces requirement.json
```

### Step 4 — Map to code

```bash
python step_3_map.py
# Extracts keywords from requirement
# Scores all indexed elements
# Produces change_proposal.json with top 30 files
```

### Step 5 — Review and enrich

```bash
python step_4_review.py
# Shows ranked file list
# Enter: all / 1,3,5 / e 2 (to add a change to file 2)
# Produces updated change_proposal.json with suggested_changes
```

### Step 6 — Apply locally

```bash
python step_5_apply.py
# Creates feature/PROJ-123-... branch
# Applies all suggested_changes
# Runs formatters and tests
# Produces apply_result.json
```

### Step 7 — Commit and push

```bash
python step_6_commit.py --push --create-pr
# git add -A → git commit → git push
# Creates PR on GitHub or Bitbucket Server
```

---

## Output Files

| File | Created by | Contents |
|------|-----------|----------|
| `analysis_report.json` | `step_1_analyze.py` (single-repo) | Languages, frameworks, code index, configs, git metadata |
| `multi_analysis_report.json` | `step_1_analyze.py` (multi-repo) | Per-repo analysis array + aggregate totals (files, classes, endpoints, test files); list of failed repos |
| `requirement.json` | `step_2_jira.py` | Ticket summary, description, AC, sub-tasks, links, comments (or manual input) |
| `change_proposal.json` | `step_3_map.py` + `step_4_review.py` | Scored file list, suggested_changes, confirmation status |
| `apply_result.json` | `step_5_apply.py` | Branch name, file results, test results, git diff |
| `commit_result.json` | `step_6_commit.py` | Commit hash, push status, PR URL |

All files are pretty-printed JSON (`indent=2`) written with UTF-8 encoding — safe to open on any OS locale.
These runtime files are listed in `.gitignore` and are not committed.

---

## Enterprise Notes

This system is designed for enterprise platforms with:

- **90+ microservices** — use multi-repo scan to index all services in one pass; keyword scoring focuses subsequent changes to the right services
- **25+ micro-frontends** — JS/TS analysis covers React, Angular, Vue, Next.js patterns; multi-repo scan works across all frontend project keys
- **Core banking integrations** (Finacle, Avaloq, T24) — entity and endpoint detection works across all Java service patterns
- **Multi-country deployment** — config detection covers environment-specific YAML/properties files
- **Jenkins CI/CD** — the `apply_result.json`, `commit_result.json`, and `multi_analysis_report.json` outputs are machine-readable for pipeline integration
- **Multiple Bitbucket project keys** — set `project_keys: ["CORE","FRONTEND","INFRA"]` to scan all services in a single command
- **GitHub organisations** — set `github_owner: "your-org"` to scan every repository in the org automatically

### Git provider URL formats supported

**GitHub:**
```
https://github.com/owner/repo.git
https://github.com/owner/repo
```

**Bitbucket Server:**
```
https://bitbucket.example.com/scm/PROJ/my-service.git
https://bitbucket.example.com/projects/PROJ/repos/my-service
```

**Bitbucket Cloud:**
```
https://bitbucket.org/workspace/repo.git
```

---

## Troubleshooting

### "No configuration found" error
Run `python step_0_setup.py` or copy `example_config.json` to `config/config.json` and fill in values.

### Clone fails with authentication error
- **GitHub**: use a **Personal Access Token** (Settings → Developer settings → Personal access tokens → Fine-grained tokens). Required scopes: `Contents: Read & Write`.
- **Bitbucket**: use an **App Password** (Profile → Personal settings → App passwords). Required permissions: **Repositories: Read, Write**.

### Jira "401 Unauthorized"
- Use an **API Token**, not your Jira password
- Generate at: https://id.atlassian.net/manage-profile/security/api-tokens
- For Jira Server (on-premise): use your regular password as the token

### No Jira? Use manual requirements
```bash
# In the UI: go to Step 2 → "Enter Manually" tab
# On CLI:
python step_2_jira.py --manual --manual-summary "Your task description"
```

### `pathspec` not installed
```bash
pip install pathspec --break-system-packages
```
Without it, `.gitignore` rules are not applied but scanning still works.

### `requests` not installed
```bash
pip install requests --break-system-packages
```

### Streamlit "ModuleNotFoundError"
Make sure you installed in the correct Python environment:
```bash
# Linux/macOS
which python3
pip show streamlit

# Windows (PowerShell)
where.exe python
pip show streamlit

# Fallback — run Streamlit via the Python module directly
python -m streamlit run app.py
```

### Proposal has no files / low scores
- Ensure the requirement description is detailed (more text = more keywords)
- Check that `analysis_report.json` was generated from the correct repository
- Run with `--local-path` if the repo URL format is non-standard

### Multi-repo scan finds 0 repositories
- **GitHub**: confirm `github_owner` is set and the PAT has `repo` (private) or public-read scope.
  Check the owner name is spelled correctly (case-sensitive).
- **Bitbucket Server**: confirm `project_keys` matches the project key visible in the Bitbucket UI
  (upper-case, e.g. `PROJ1`). Confirm the base URL is reachable from this machine.
- **Bitbucket Cloud**: the `project_keys` value should be the **workspace slug** shown in your
  Bitbucket Cloud URL (e.g. `https://bitbucket.org/my-workspace/`).
- Run `python repo_discovery.py --github-owner your-org` to test discovery independently.

### Multi-repo scan runs out of disk space
By default every clone is deleted after analysis. If you used `--no-cleanup`, disk usage
grows proportionally to the number and size of repos. Remove the flag or manually delete
the `workspace_dir` sub-folders after the scan.

### GitHub PR creation fails
- Ensure the PAT has `Pull requests: Read & Write` permission
- For GitHub Enterprise: the API URL is different — raise a GitHub issue if needed

### Bitbucket PR creation fails
- Verify `--project-key` matches the Bitbucket project key exactly (case-sensitive)
- Verify `--repo-slug` matches the repository slug in Bitbucket (not the display name)
- Ensure the app-password has **Pull Requests: Read, Write** permissions

---

## Windows-Specific Notes

### Config file location
Config is now stored inside the project at `config\config.json` — **not** in your home
directory. This makes it easier to manage per-project credentials and avoids home-directory
path issues on Windows.

### File permissions
On Linux/macOS, `config.json` is protected with `chmod 600` (owner read/write only).
On Windows, NTFS directory permissions apply — the `config\` folder is inside your project
and is not world-readable by default. No extra steps needed.

### Tool names on Windows
The following tools are auto-discovered with their Windows `.cmd` extensions:

| Tool | Windows equivalent auto-tried |
|------|-------------------------------|
| `mvn` | `mvn.cmd` |
| `npm` | `npm.cmd` |
| `yarn` | `yarn.cmd` |
| `prettier` | `prettier.cmd` |
| `black` | `black.exe` |
| `isort` | `isort.exe` |

If a tool is installed but not found, ensure its install directory is on `PATH`.

### `python` vs `python3` command
On Linux/macOS the command may be `python3`. On Windows it is usually `python`.
All scripts use `sys.executable` internally so the correct interpreter is always used.

### Running the Streamlit UI on Windows
```powershell
# Standard
streamlit run app.py

# If 'streamlit' is not found on PATH after pip install:
python -m streamlit run app.py
```

### Line endings
All JSON output files are written with UTF-8 encoding. Git may show CRLF warnings
on Windows — this is expected and does not affect functionality. You can configure:
```bash
git config --global core.autocrlf input
```
