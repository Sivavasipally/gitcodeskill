#!/usr/bin/env python3
"""
Step 4: Review & Confirm Changes
Presents the proposal for human review and allows inline enrichment.
"""
import argparse
import json
import sys
from pathlib import Path


CHANGE_TYPES = ["replace", "insert_after", "insert_before", "append", "full_replace"]


def display_proposal(proposal: dict) -> None:
    """Pretty-print the proposal for CLI review."""
    ticket = proposal.get("ticket_id", "N/A")
    summary = proposal.get("ticket_summary", "")
    print(f"\n{'=' * 70}")
    print(f"CHANGE PROPOSAL — {ticket}: {summary}")
    print(f"{'=' * 70}")

    files_to_modify = proposal.get("files_to_modify", [])
    files_to_create = proposal.get("files_to_create", [])
    files_to_delete = proposal.get("files_to_delete", [])

    print(f"\nFiles to MODIFY ({len(files_to_modify)}):")
    for i, f in enumerate(files_to_modify, 1):
        score = f.get("score", 0)
        matches = f.get("matches", [])
        print(f"  [{i}] {f['file']} (score: {score})")
        if matches:
            names = [m["name"] for m in matches[:3]]
            print(f"      Matches: {', '.join(names)}")
        locations = f.get("keyword_locations", [])
        if locations:
            print(f"      Keyword locations: {len(locations)} blocks")

    if files_to_create:
        print(f"\nFiles to CREATE ({len(files_to_create)}):")
        for i, f in enumerate(files_to_create, 1):
            print(f"  [{i}] {f.get('file', f.get('path', 'unknown'))}")

    if files_to_delete:
        print(f"\nFiles to DELETE ({len(files_to_delete)}):")
        for f in files_to_delete:
            print(f"  - {f.get('file', f)}")

    notes = proposal.get("notes", [])
    if notes:
        print("\nNotes:")
        for note in notes:
            print(f"  * {note}")

    config_changes = proposal.get("config_changes", [])
    if config_changes:
        print(f"\nPossible Config Changes ({len(config_changes)}):")
        for c in config_changes:
            print(f"  - {c.get('file', '')}: {c.get('reason', '')}")

    print()


def parse_confirmed_indices(confirmed_arg: str, max_idx: int) -> list:
    """Parse --confirmed-changes argument."""
    if confirmed_arg.lower() == "all":
        return list(range(max_idx))

    indices = []
    for part in confirmed_arg.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < max_idx:
                indices.append(idx)
    return indices


def interactive_review(proposal: dict) -> dict:
    """Interactive CLI review loop."""
    display_proposal(proposal)

    files_to_modify = proposal.get("files_to_modify", [])
    if not files_to_modify:
        print("[INFO] No files to modify in proposal.")
        return proposal

    print("Options:")
    print("  'all'      — confirm all files")
    print("  '1,3,5'    — cherry-pick by number")
    print("  'q'        — quit without changes")
    print("  'e <n>'    — add specific change to file n")

    confirmed = input("\nEnter selection: ").strip()

    if confirmed.lower() == "q":
        print("[INFO] Review cancelled.")
        sys.exit(0)

    if confirmed.lower() == "all":
        indices = list(range(len(files_to_modify)))
    elif confirmed.startswith("e "):
        # Enrich a specific file
        try:
            n = int(confirmed.split()[1]) - 1
            _enrich_file_interactive(files_to_modify[n])
        except (IndexError, ValueError):
            print("[ERROR] Invalid file number.")
        return interactive_review(proposal)
    else:
        indices = parse_confirmed_indices(confirmed, len(files_to_modify))

    # Keep only confirmed files
    confirmed_files = [files_to_modify[i] for i in sorted(set(indices))]
    proposal["files_to_modify"] = confirmed_files
    proposal["confirmed"] = True

    print(f"\n[OK] Confirmed {len(confirmed_files)} files for modification.")
    return proposal


def _enrich_file_interactive(file_entry: dict) -> None:
    """Add suggested_changes to a file entry interactively."""
    print(f"\nAdding change to: {file_entry['file']}")
    print("Change types: replace | insert_after | insert_before | append | full_replace")

    change_type = input("Change type: ").strip().lower()
    if change_type not in CHANGE_TYPES:
        print(f"[ERROR] Invalid type. Choose from: {', '.join(CHANGE_TYPES)}")
        return

    change = {"type": change_type}

    if change_type == "replace":
        change["old_text"] = input("Old text (first occurrence): ")
        change["new_text"] = input("New text: ")
    elif change_type in ("insert_after", "insert_before"):
        key = "after_line" if change_type == "insert_after" else "before_line"
        change[key] = input(f"Line number or text marker: ")
        change["new_text"] = input("Text to insert: ")
    elif change_type == "append":
        change["new_text"] = input("Text to append: ")
    elif change_type == "full_replace":
        print("Enter full new content (end with a line containing only '---END---'):")
        lines = []
        while True:
            line = input()
            if line == "---END---":
                break
            lines.append(line)
        change["new_text"] = "\n".join(lines)

    if "suggested_changes" not in file_entry:
        file_entry["suggested_changes"] = []
    file_entry["suggested_changes"].append(change)
    print("[OK] Change added.")


def apply_confirmed_changes_arg(proposal: dict, confirmed_arg: str) -> dict:
    """Apply --confirmed-changes argument to proposal."""
    files_to_modify = proposal.get("files_to_modify", [])

    if confirmed_arg.lower() == "all":
        for f in files_to_modify:
            f["confirmed"] = True
        proposal["confirmed"] = True
        return proposal

    indices = parse_confirmed_indices(confirmed_arg, len(files_to_modify))
    confirmed_files = []
    for i, f in enumerate(files_to_modify):
        if i in indices:
            f["confirmed"] = True
            confirmed_files.append(f)

    proposal["files_to_modify"] = confirmed_files
    proposal["confirmed"] = True
    return proposal


def load_enrichment_json(enrichment_path: str, proposal: dict) -> dict:
    """Load enrichment from a JSON file and merge into proposal."""
    with open(enrichment_path, encoding="utf-8") as f:
        enrichment = json.load(f)

    enrichment_map = {e["file"]: e for e in enrichment}

    for file_entry in proposal.get("files_to_modify", []):
        fname = file_entry.get("file")
        if fname in enrichment_map:
            enrichment_data = enrichment_map[fname]
            if "suggested_changes" in enrichment_data:
                existing = file_entry.get("suggested_changes", [])
                existing.extend(enrichment_data["suggested_changes"])
                file_entry["suggested_changes"] = existing

    return proposal


def main():
    parser = argparse.ArgumentParser(
        description="Review and confirm change proposal"
    )
    parser.add_argument("--proposal", default="change_proposal.json",
                        help="Path to change_proposal.json")
    parser.add_argument("--output", default="change_proposal.json",
                        help="Output JSON path (updated proposal)")
    parser.add_argument("--confirmed-changes",
                        help='Confirm changes: "all" or "1,3,5"')
    parser.add_argument("--enrichment-file",
                        help="JSON file with suggested_changes per file")
    parser.add_argument("--show-only", action="store_true",
                        help="Display proposal without modification")
    args = parser.parse_args()

    proposal_path = Path(args.proposal)
    if not proposal_path.exists():
        print(f"[ERROR] Proposal not found: {proposal_path}", file=sys.stderr)
        sys.exit(1)

    with open(proposal_path, encoding="utf-8") as f:
        proposal = json.load(f)

    if args.show_only:
        display_proposal(proposal)
        return

    # Apply enrichment if provided
    if args.enrichment_file:
        proposal = load_enrichment_json(args.enrichment_file, proposal)
        print(f"[OK] Loaded enrichment from {args.enrichment_file}")

    # Apply confirmed-changes arg or go interactive
    if args.confirmed_changes:
        proposal = apply_confirmed_changes_arg(proposal, args.confirmed_changes)
        print(f"[OK] Applied --confirmed-changes: {args.confirmed_changes}")
        display_proposal(proposal)
    else:
        proposal = interactive_review(proposal)

    # Save updated proposal
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2)

    confirmed_count = len([f for f in proposal.get("files_to_modify", [])
                            if f.get("confirmed")])
    print(f"\n[OK] Updated proposal saved to {output_path}")
    print(f"     {confirmed_count} files confirmed for changes.")


if __name__ == "__main__":
    main()
