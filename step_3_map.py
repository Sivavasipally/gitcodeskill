#!/usr/bin/env python3
"""
Step 3: Map Requirements to Code Changes
Extracts keywords from Jira ticket and scores code elements for relevance.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


# ── Stop words ──────────────────────────────────────────────────────────────────

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "shall", "can",
    "not", "no", "nor", "so", "yet", "both", "either", "neither", "each",
    "few", "more", "most", "other", "some", "such", "than", "too", "very",
    "just", "this", "that", "these", "those", "it", "its", "their", "they",
    "we", "you", "he", "she", "him", "her", "his", "our", "your", "my",
    "any", "all", "one", "two", "new", "also", "when", "where", "how",
    "what", "which", "who", "need", "update", "add", "use", "get", "set",
    "null", "true", "false", "return", "if", "else", "then", "fix", "bug",
    "change", "test", "run", "make", "into", "up", "out", "over",
}


# ── Keyword extraction ──────────────────────────────────────────────────────────

def split_camel_case(text: str) -> list:
    """Split camelCase and PascalCase into individual words."""
    words = re.sub(r"([A-Z][a-z]+)", r" \1", text)
    words = re.sub(r"([A-Z]+)(?=[A-Z][a-z])", r"\1 ", words)
    return [w.lower() for w in words.split() if w]


def split_snake_case(text: str) -> list:
    """Split snake_case and kebab-case into words."""
    return [w.lower() for w in re.split(r"[_\-\s]+", text) if w]


def tokenize(text: str) -> list:
    """Extract all meaningful tokens from text."""
    if not text:
        return []

    tokens = set()
    # Split on whitespace and punctuation first
    raw_words = re.findall(r"[a-zA-Z][a-zA-Z0-9]*", text)

    for word in raw_words:
        lw = word.lower()
        if len(lw) >= 3 and lw not in STOP_WORDS:
            tokens.add(lw)
            # Also add camelCase and snake_case splits
            for part in split_camel_case(word):
                if len(part) >= 3 and part not in STOP_WORDS:
                    tokens.add(part)

    return list(tokens)


def extract_keywords(requirement: dict) -> list:
    """Extract all keywords from Jira requirement."""
    text_sources = []

    # Primary sources (high value)
    text_sources.append(requirement.get("summary", ""))
    text_sources.append(requirement.get("acceptance_criteria", ""))

    # Description
    text_sources.append(requirement.get("description", "")[:3000])

    # Labels and components (exact terms)
    text_sources.extend(requirement.get("labels", []))
    text_sources.extend(requirement.get("components", []))

    # Sub-task summaries
    for st in requirement.get("subtasks", []):
        text_sources.append(st.get("summary", ""))

    # Linked issue summaries
    for li in requirement.get("linked_issues", []):
        text_sources.append(li.get("summary", ""))

    # First few comments
    for c in requirement.get("comments", [])[:5]:
        text_sources.append(c.get("body", "")[:500])

    # Combine and tokenize
    all_text = " ".join(text_sources)
    keywords = tokenize(all_text)

    # Also add exact label/component names (may be multi-word)
    for label in requirement.get("labels", []) + requirement.get("components", []):
        if label and len(label) >= 3:
            keywords.append(label.lower())

    # Deduplicate
    return list(dict.fromkeys(keywords))


# ── Relevance scoring ───────────────────────────────────────────────────────────

def get_name_parts(name: str) -> list:
    """Get all meaningful parts of a code element name."""
    parts = set()
    parts.add(name.lower())
    parts.update(split_camel_case(name))
    parts.update(split_snake_case(name))
    return [p for p in parts if len(p) >= 3]


def score_element(element_name: str, keywords: list) -> float:
    """Score a code element name against keywords."""
    name_lower = element_name.lower()
    name_parts = get_name_parts(element_name)
    score = 0.0

    for kw in keywords:
        kw_lower = kw.lower()
        # Exact match
        if kw_lower == name_lower:
            score += 10.0
        # Substring match
        elif kw_lower in name_lower or name_lower in kw_lower:
            score += 5.0
        # Word-part match
        elif any(kw_lower == part or kw_lower in part or part in kw_lower
                 for part in name_parts):
            score += 3.0

    return score


def score_file_content(file_path: str, content: str, keywords: list) -> float:
    """Score file content by keyword frequency."""
    content_lower = content.lower()
    score = 0.0
    for kw in keywords:
        count = content_lower.count(kw.lower())
        score += count * 0.5
    return score


def find_keyword_clusters(content: str, keywords: list, max_locations: int = 10) -> list:
    """Find line ranges where keywords cluster, return top locations with snippets."""
    if not content or not keywords:
        return []

    lines = content.split("\n")
    keyword_hits = defaultdict(list)  # line_no -> [keyword]

    kw_set = {kw.lower() for kw in keywords}
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for kw in kw_set:
            if kw in line_lower:
                keyword_hits[i].append(kw)

    if not keyword_hits:
        return []

    # Sort by number of hits
    sorted_hits = sorted(keyword_hits.items(), key=lambda x: -len(x[1]))

    # Merge nearby blocks (within 3 lines)
    locations = []
    used = set()

    for line_no, _ in sorted_hits[:50]:
        if line_no in used:
            continue
        # Expand context window ±5 lines
        start = max(0, line_no - 5)
        end = min(len(lines) - 1, line_no + 5)

        # Merge with nearby used blocks
        for l in range(start, end + 1):
            used.add(l)

        # Collect keywords in range
        range_kws = []
        for l in range(start, end + 1):
            range_kws.extend(keyword_hits.get(l, []))

        snippet = "\n".join(lines[start:end + 1])
        locations.append({
            "start_line": start + 1,
            "end_line": end + 1,
            "keywords_found": list(set(range_kws)),
            "snippet": snippet[:500],
        })

        if len(locations) >= max_locations:
            break

    return locations


# ── Main mapping ────────────────────────────────────────────────────────────────

def score_files(analysis_report: dict, keywords: list, repo_path: Path) -> list:
    """Score all indexed files and file content for relevance."""
    code_index = analysis_report.get("code_index", {})
    file_scores = defaultdict(float)
    file_matches = defaultdict(list)

    # Score code index elements
    for element_type in ["classes", "functions", "api_endpoints", "db_entities", "interfaces"]:
        for element in code_index.get(element_type, []):
            fname = element.get("file", "")
            name = element.get("name") or element.get("path", "")
            if not name:
                continue
            score = score_element(name, keywords)
            if score > 0:
                file_scores[fname] += score
                file_matches[fname].append({
                    "type": element_type,
                    "name": name,
                    "score": score,
                    "line": element.get("line"),
                })

    # Score file content
    if repo_path.exists():
        from step_1_analyze import walk_files, read_file_safe, SKIP_DIRS, to_posix_rel
        for fp in walk_files(repo_path):
            ext = fp.suffix.lower()
            if ext in (".java", ".py", ".js", ".jsx", ".ts", ".tsx",
                       ".xml", ".yml", ".yaml", ".json", ".properties"):
                rel = to_posix_rel(fp, repo_path)
                content = read_file_safe(fp, max_bytes=100_000)
                if content:
                    content_score = score_file_content(rel, content, keywords)
                    if content_score > 0:
                        file_scores[rel] += content_score

    # Rank by score
    ranked = sorted(file_scores.items(), key=lambda x: -x[1])[:30]

    results = []
    for fname, total_score in ranked:
        # Get line clusters
        clusters = []
        if repo_path.exists():
            fp = repo_path / fname
            if fp.exists():
                content = ""
                try:
                    content = fp.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass
                if content:
                    clusters = find_keyword_clusters(content, keywords)

        results.append({
            "file": fname,
            "score": round(total_score, 2),
            "matches": sorted(file_matches.get(fname, []),
                               key=lambda x: -x["score"])[:10],
            "keyword_locations": clusters,
        })

    return results


def generate_proposal(analysis_report: dict, requirement: dict,
                       repo_path: Path, logs: list) -> dict:
    """Generate change proposal."""
    logs.append("Extracting keywords from Jira ticket...")
    keywords = extract_keywords(requirement)
    logs.append(f"Extracted {len(keywords)} keywords: {', '.join(keywords[:20])}...")

    logs.append("Scoring files for relevance...")
    scored_files = score_files(analysis_report, keywords, repo_path)
    logs.append(f"Scored {len(scored_files)} relevant files.")

    # Separate by type
    files_to_modify = [f for f in scored_files if f["score"] >= 2.0]
    files_to_create = []
    files_to_delete = []

    # Config changes detection
    config_changes = []
    req_text = requirement.get("description", "") + requirement.get("acceptance_criteria", "")
    config_keywords = ["config", "environment", "variable", "property", "setting",
                       "database", "connection", "url", "port", "host"]
    if any(kw in req_text.lower() for kw in config_keywords):
        for cfg_file in analysis_report.get("configurations", {}).get("config_files", {}):
            config_changes.append({
                "file": cfg_file,
                "reason": "Requirement may require configuration changes",
            })

    # Test changes
    test_changes = []
    test_info = analysis_report.get("tests", {})
    for fw in test_info.get("frameworks", {}).keys():
        test_changes.append({
            "framework": fw,
            "note": f"Add/update tests using {fw}",
        })

    # Notes
    notes = []
    ticket_type = requirement.get("type", "")
    if ticket_type.lower() in ("story", "feature"):
        notes.append("This appears to be a feature request — consider new files and API endpoints.")
    elif ticket_type.lower() == "bug":
        notes.append("Bug fix — focus on modifying existing files rather than creating new ones.")
    elif ticket_type.lower() in ("task", "subtask"):
        notes.append("Task — review all matched files and apply targeted changes.")

    sp = requirement.get("story_points", 0)
    if sp >= 8:
        notes.append(f"High complexity ticket ({sp} story points) — changes may span multiple services.")

    proposal = {
        "ticket_id": requirement.get("ticket_id"),
        "ticket_summary": requirement.get("summary"),
        "keywords_used": keywords,
        "files_to_modify": files_to_modify,
        "files_to_create": files_to_create,
        "files_to_delete": files_to_delete,
        "config_changes": config_changes[:5],
        "test_changes": test_changes,
        "notes": notes,
        "total_files_matched": len(scored_files),
    }

    logs.append(f"Proposal generated: {len(files_to_modify)} files to modify, "
                f"{len(files_to_create)} to create, {len(files_to_delete)} to delete.")
    return proposal


def main():
    parser = argparse.ArgumentParser(
        description="Map Jira requirements to code change proposals"
    )
    parser.add_argument("--analysis", default="analysis_report.json",
                        help="Path to analysis_report.json")
    parser.add_argument("--requirement", default="requirement.json",
                        help="Path to requirement.json")
    parser.add_argument("--output", default="change_proposal.json",
                        help="Output JSON path")
    args = parser.parse_args()

    # Load inputs
    analysis_path = Path(args.analysis)
    req_path = Path(args.requirement)

    if not analysis_path.exists():
        print(f"[ERROR] Analysis report not found: {analysis_path}", file=sys.stderr)
        sys.exit(1)
    if not req_path.exists():
        print(f"[ERROR] Requirement not found: {req_path}", file=sys.stderr)
        sys.exit(1)

    with open(analysis_path, encoding="utf-8") as f:
        analysis_report = json.load(f)
    with open(req_path, encoding="utf-8") as f:
        requirement = json.load(f)

    repo_path = Path(analysis_report.get("repo_path", "."))

    logs = []
    proposal = generate_proposal(analysis_report, requirement, repo_path, logs)
    proposal["logs"] = logs

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2)

    for line in logs:
        print(line)
    print(f"\n[OK] Change proposal saved to {output_path}")
    print(f"     Files to modify: {len(proposal['files_to_modify'])}, "
          f"Create: {len(proposal['files_to_create'])}, "
          f"Delete: {len(proposal['files_to_delete'])}")


if __name__ == "__main__":
    main()
