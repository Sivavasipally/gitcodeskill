#!/usr/bin/env python3
"""
Step 2: Fetch Jira Requirements
Fetches Jira ticket details via REST API v3.
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ── ADF → Plain text converter ──────────────────────────────────────────────────

def adf_to_text(node, depth=0) -> str:
    """Convert Atlassian Document Format (ADF) JSON to plain text."""
    if not node:
        return ""
    if isinstance(node, str):
        return node

    node_type = node.get("type", "")
    content = node.get("content", [])
    text = node.get("text", "")

    if node_type == "text":
        marks = node.get("marks", [])
        result = text
        for mark in marks:
            if mark.get("type") == "code":
                result = f"`{result}`"
        return result

    parts = []

    if node_type == "paragraph":
        parts.append("".join(adf_to_text(c) for c in content))
        parts.append("\n")
    elif node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        heading_text = "".join(adf_to_text(c) for c in content)
        parts.append(f"{'#' * level} {heading_text}\n")
    elif node_type == "bulletList":
        for item in content:
            parts.append(f"  - {''.join(adf_to_text(c) for c in item.get('content', []))}")
    elif node_type == "orderedList":
        for i, item in enumerate(content, 1):
            parts.append(f"  {i}. {''.join(adf_to_text(c) for c in item.get('content', []))}")
    elif node_type == "listItem":
        parts.append("".join(adf_to_text(c) for c in content))
    elif node_type == "codeBlock":
        lang = node.get("attrs", {}).get("language", "")
        code_text = "".join(adf_to_text(c) for c in content)
        parts.append(f"```{lang}\n{code_text}\n```\n")
    elif node_type == "blockquote":
        for c in content:
            parts.append(f"> {adf_to_text(c)}")
    elif node_type == "hardBreak":
        parts.append("\n")
    elif node_type == "rule":
        parts.append("---\n")
    elif node_type in ("doc", "listItem"):
        for c in content:
            parts.append(adf_to_text(c))
    elif node_type == "table":
        for row in content:
            cells = [adf_to_text(c) for c in row.get("content", [])]
            parts.append(" | ".join(cells) + "\n")
    elif node_type == "mention":
        parts.append(f"@{node.get('attrs', {}).get('text', 'user')}")
    elif node_type == "emoji":
        parts.append(node.get("attrs", {}).get("text", ""))
    else:
        for c in content:
            parts.append(adf_to_text(c))

    return "".join(parts)


def description_to_text(description) -> str:
    """Handle both ADF objects and plain strings."""
    if not description:
        return ""
    if isinstance(description, str):
        return description
    if isinstance(description, dict):
        return adf_to_text(description)
    return str(description)


# ── Acceptance criteria extraction ─────────────────────────────────────────────

def extract_acceptance_criteria(fields: dict, desc_text: str) -> str:
    """Extract acceptance criteria from custom fields or description."""
    # Common custom field names for acceptance criteria
    ac_field_names = [
        "customfield_10016", "customfield_10014", "customfield_10200",
        "acceptance_criteria", "acceptanceCriteria",
    ]
    for fn in ac_field_names:
        val = fields.get(fn)
        if val:
            return description_to_text(val)

    # Try to parse from description
    if desc_text:
        patterns = [
            r"(?i)acceptance\s+criteria[:\s]+([\s\S]+?)(?=\n#{1,3}\s|\Z)",
            r"(?i)##\s*acceptance\s+criteria\s*\n([\s\S]+?)(?=\n##|\Z)",
            r"(?i)ac:\s*([\s\S]+?)(?=\n\n|\Z)",
        ]
        import re
        for pat in patterns:
            m = re.search(pat, desc_text)
            if m:
                return m.group(1).strip()

    return ""


def extract_story_points(fields: dict) -> float:
    """Extract story points from common custom fields."""
    sp_fields = ["story_points", "customfield_10016", "customfield_10004",
                 "customfield_10028", "storyPoints"]
    for fn in sp_fields:
        val = fields.get(fn)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
    return 0.0


def extract_sprint(fields: dict) -> str:
    """Extract sprint name from fields."""
    sprint_fields = ["customfield_10020", "customfield_10021", "sprint"]
    for fn in sprint_fields:
        val = fields.get(fn)
        if val:
            if isinstance(val, list) and val:
                sprint = val[0]
                if isinstance(sprint, dict):
                    return sprint.get("name", str(sprint))
                return str(sprint)
            if isinstance(val, dict):
                return val.get("name", str(val))
            return str(val)
    return ""


# ── Jira API client ─────────────────────────────────────────────────────────────

class JiraClient:
    def __init__(self, base_url: str, email: str, token: str):
        if not HAS_REQUESTS:
            raise ImportError("requests library required. pip install requests")
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (email, token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self.timeout = 30

    def get(self, path: str, params: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def test_connection(self) -> dict:
        return self.get("/rest/api/3/myself")

    def fetch_issue(self, ticket_id: str) -> dict:
        return self.get(
            f"/rest/api/3/issue/{ticket_id}",
            params={"expand": "renderedFields,names,changelog"}
        )

    def fetch_comments(self, ticket_id: str, max_results: int = 50) -> list:
        try:
            data = self.get(
                f"/rest/api/3/issue/{ticket_id}/comment",
                params={"maxResults": max_results, "orderBy": "-created"}
            )
            return data.get("comments", [])
        except Exception:
            return []

    def fetch_attachments(self, fields: dict) -> list:
        attachments = fields.get("attachment", [])
        return [
            {
                "filename": a.get("filename"),
                "mimeType": a.get("mimeType"),
                "size": a.get("size"),
                "created": a.get("created"),
            }
            for a in attachments
        ]


def fetch_requirements(jira_url: str, email: str, token: str, ticket_id: str,
                        logs: list) -> dict:
    client = JiraClient(jira_url, email, token)

    logs.append(f"Connecting to Jira: {jira_url}")
    try:
        myself = client.test_connection()
        logs.append(f"Authenticated as: {myself.get('displayName', email)}")
    except Exception as e:
        raise RuntimeError(f"Jira connection failed: {e}")

    logs.append(f"Fetching ticket: {ticket_id}")
    issue = client.fetch_issue(ticket_id)

    fields = issue.get("fields", {})
    rendered = issue.get("renderedFields", {})

    # Core fields
    summary = fields.get("summary", "")
    status = fields.get("status", {}).get("name", "Unknown")
    priority = (fields.get("priority") or {}).get("name", "")
    issue_type = fields.get("issuetype", {}).get("name", "")
    assignee = (fields.get("assignee") or {}).get("displayName", "Unassigned")
    reporter = (fields.get("reporter") or {}).get("displayName", "")
    labels = fields.get("labels", [])
    components = [c.get("name") for c in fields.get("components", [])]
    fix_versions = [v.get("name") for v in fields.get("fixVersions", [])]
    created = fields.get("created", "")
    updated = fields.get("updated", "")

    # Description
    desc_raw = fields.get("description")
    desc_rendered = rendered.get("description", "")
    desc_text = description_to_text(desc_raw) or desc_rendered

    # Custom derived fields
    story_points = extract_story_points(fields)
    sprint = extract_sprint(fields)
    acceptance_criteria = extract_acceptance_criteria(fields, desc_text)

    # Sub-tasks
    subtasks = []
    for st in fields.get("subtasks", []):
        subtasks.append({
            "id": st.get("key"),
            "summary": st.get("fields", {}).get("summary", ""),
            "status": st.get("fields", {}).get("status", {}).get("name", ""),
            "type": st.get("fields", {}).get("issuetype", {}).get("name", ""),
        })

    # Linked issues
    linked_issues = []
    for link in fields.get("issuelinks", []):
        li = {}
        if link.get("outwardIssue"):
            oi = link["outwardIssue"]
            li = {
                "direction": "outward",
                "type": link.get("type", {}).get("outward", ""),
                "key": oi.get("key"),
                "summary": oi.get("fields", {}).get("summary", ""),
                "status": oi.get("fields", {}).get("status", {}).get("name", ""),
            }
        elif link.get("inwardIssue"):
            ii = link["inwardIssue"]
            li = {
                "direction": "inward",
                "type": link.get("type", {}).get("inward", ""),
                "key": ii.get("key"),
                "summary": ii.get("fields", {}).get("summary", ""),
                "status": ii.get("fields", {}).get("status", {}).get("name", ""),
            }
        if li:
            linked_issues.append(li)

    # Comments
    logs.append("Fetching comments...")
    raw_comments = client.fetch_comments(ticket_id)
    comments = []
    for c in raw_comments[:50]:
        body_raw = c.get("body")
        comments.append({
            "author": c.get("author", {}).get("displayName", ""),
            "created": c.get("created", ""),
            "body": description_to_text(body_raw)[:500],
        })

    # Attachments
    attachments = client.fetch_attachments(fields)

    requirement = {
        "ticket_id": ticket_id,
        "summary": summary,
        "description": desc_text,
        "acceptance_criteria": acceptance_criteria,
        "status": status,
        "priority": priority,
        "type": issue_type,
        "assignee": assignee,
        "reporter": reporter,
        "labels": labels,
        "components": components,
        "fix_versions": fix_versions,
        "story_points": story_points,
        "sprint": sprint,
        "created": created,
        "updated": updated,
        "subtasks": subtasks,
        "linked_issues": linked_issues,
        "comments": comments,
        "attachments": attachments,
        "jira_url": jira_url,
    }

    logs.append(f"[OK] Fetched ticket: {summary}")
    logs.append(f"     Status: {status}, Priority: {priority}, Type: {issue_type}")
    logs.append(f"     Sub-tasks: {len(subtasks)}, Links: {len(linked_issues)}, "
                f"Comments: {len(comments)}, Attachments: {len(attachments)}")

    return requirement


def build_manual_requirement(ticket_id: str, summary: str, description: str,
                              issue_type: str = "task") -> dict:
    """Build a requirement dict from manually-entered text (no Jira needed)."""
    return {
        "ticket_id": ticket_id or "MANUAL-1",
        "summary": summary,
        "description": description,
        "acceptance_criteria": "",
        "status": "In Progress",
        "priority": "Medium",
        "type": issue_type,
        "assignee": "Unassigned",
        "reporter": "",
        "labels": [],
        "components": [],
        "fix_versions": [],
        "story_points": 0.0,
        "sprint": "",
        "created": "",
        "updated": "",
        "subtasks": [],
        "linked_issues": [],
        "comments": [],
        "attachments": [],
        "jira_url": "",
        "source": "manual",
    }


def main():
    from step_0_setup import load_config

    parser = argparse.ArgumentParser(
        description="Fetch requirements — from Jira OR entered manually"
    )
    # Jira mode
    parser.add_argument("--jira-url", help="Jira server URL")
    parser.add_argument("--jira-email", help="Jira email")
    parser.add_argument("--jira-token", help="Jira API token")
    parser.add_argument("--ticket", help="Jira ticket ID (e.g. PROJ-123)")
    parser.add_argument("--test-connection", action="store_true",
                        help="Test Jira connection only")
    # Manual mode (no Jira)
    parser.add_argument("--manual", action="store_true",
                        help="Enter requirements manually instead of fetching from Jira")
    parser.add_argument("--manual-id", default="MANUAL-1",
                        help="Ticket/task ID for manual requirement (default: MANUAL-1)")
    parser.add_argument("--manual-summary", default="",
                        help="One-line summary of the requirement")
    parser.add_argument("--manual-description", default="",
                        help="Full description of the requirement")
    parser.add_argument("--manual-type", default="task",
                        choices=["task", "bug", "story", "feature"],
                        help="Issue type for manual requirement")
    # Common
    parser.add_argument("--output", default="requirement.json", help="Output JSON path")
    args = parser.parse_args()

    config = load_config()

    # ── Manual mode ─────────────────────────────────────────────────────────────
    if args.manual:
        summary = args.manual_summary
        description = args.manual_description
        if not summary and not description:
            # Interactive prompts when nothing passed on CLI
            print("=== Manual Requirement Entry ===")
            args.manual_id = input(f"Task ID [{args.manual_id}]: ").strip() or args.manual_id
            summary = input("Summary (one line): ").strip()
            print("Description (paste text, end with a line containing only '---END---'):")
            lines = []
            while True:
                line = input()
                if line == "---END---":
                    break
                lines.append(line)
            description = "\n".join(lines)
            args.manual_type = input(
                f"Type (task/bug/story/feature) [{args.manual_type}]: "
            ).strip() or args.manual_type

        requirement = build_manual_requirement(
            args.manual_id, summary, description, args.manual_type
        )
        requirement["logs"] = ["[OK] Requirement created from manual input."]

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(requirement, f, indent=2)
        print(f"[OK] Manual requirement saved to {output_path}")
        return

    # ── Jira mode ────────────────────────────────────────────────────────────────
    jira_url = args.jira_url or config.get("jira_url", "")
    email = args.jira_email or config.get("jira_email", "")
    token = args.jira_token or config.get("jira_token", "")
    ticket = args.ticket or config.get("jira_ticket", "")

    if not jira_url or not email or not token:
        print("[ERROR] Jira credentials required. Either run step_0_setup.py with Jira details,\n"
              "        or use --manual to enter the requirement directly.", file=sys.stderr)
        sys.exit(1)

    if args.test_connection:
        try:
            client = JiraClient(jira_url, email, token)
            myself = client.test_connection()
            print(f"[OK] Connected to Jira as: {myself.get('displayName', email)}")
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}", file=sys.stderr)
            sys.exit(1)
        return

    if not ticket:
        print("[ERROR] Jira ticket ID required (--ticket or set in config).", file=sys.stderr)
        sys.exit(1)

    logs = []
    try:
        requirement = fetch_requirements(jira_url, email, token, ticket, logs)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    requirement["logs"] = logs

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(requirement, f, indent=2)

    for line in logs:
        print(line)
    print(f"\n[OK] Requirement saved to {output_path}")


if __name__ == "__main__":
    main()
