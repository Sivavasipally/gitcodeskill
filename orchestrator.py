#!/usr/bin/env python3
"""
Orchestrator: Chains all 7 steps of the Bitbucket + Jira Dev Skill.
Supports --full (end-to-end) and --step (individual step) modes.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


STEPS = {
    0: ("step_0_setup.py", "Setup & Config"),
    1: ("step_1_analyze.py", "Clone & Analyze Repository"),
    2: ("step_2_jira.py", "Fetch Jira Requirements"),
    3: ("step_3_map.py", "Map Requirements to Code Changes"),
    4: ("step_4_review.py", "Review & Confirm"),
    5: ("step_5_apply.py", "Apply Changes Locally"),
    6: ("step_6_commit.py", "Commit & Push"),
}

SCRIPT_DIR = Path(__file__).parent


def run_step(step_num: int, extra_args: list = None, logs: list = None) -> tuple:
    """Run a single step script. Returns (returncode, output)."""
    if step_num not in STEPS:
        return 1, f"Unknown step: {step_num}"

    script_name, step_label = STEPS[step_num]
    script_path = SCRIPT_DIR / script_name
    cmd = [sys.executable, str(script_path)] + (extra_args or [])

    print(f"\n{'=' * 60}")
    print(f"STEP {step_num}: {step_label}")
    print(f"{'=' * 60}")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=False,  # Let output stream to console
        text=True,
        timeout=300,
    )

    if logs is not None:
        logs.append(f"Step {step_num} ({step_label}): "
                    f"{'OK' if result.returncode == 0 else 'FAILED'}")

    return result.returncode, ""


def run_step_captured(step_num: int, extra_args: list = None) -> tuple:
    """Run a step and capture output. Returns (returncode, output)."""
    if step_num not in STEPS:
        return 1, f"Unknown step: {step_num}"

    script_name, _ = STEPS[step_num]
    script_path = SCRIPT_DIR / script_name
    cmd = [sys.executable, str(script_path)] + (extra_args or [])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = result.stdout + result.stderr
    return result.returncode, output


def check_prerequisites(step_num: int) -> list:
    """Check if prerequisite files exist for a step."""
    prereqs = {
        3: ["analysis_report.json", "requirement.json"],
        4: ["change_proposal.json"],
        5: ["change_proposal.json", "analysis_report.json"],
        6: ["apply_result.json"],
    }
    missing = []
    for fname in prereqs.get(step_num, []):
        if not Path(fname).exists():
            missing.append(fname)
    return missing


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║       Bitbucket + Jira Dev Skill — Orchestrator              ║
║       Automated Development Workflow                         ║
╚══════════════════════════════════════════════════════════════╝
""")


def full_run(args) -> int:
    """Run all steps end-to-end."""
    print_banner()
    logs = []
    overall_rc = 0

    # Step 0: Setup (only if not already configured or --reconfigure)
    if args.reconfigure or not (SCRIPT_DIR / "config" / "config.json").exists():
        rc, _ = run_step(0, logs=logs)
        if rc != 0:
            print(f"\n[ERROR] Step 0 failed. Aborting.")
            return rc

    # Step 1: Clone & Analyze
    step1_args = []
    if args.repo_url:
        step1_args += ["--repo-url", args.repo_url]
    if args.workspace_dir:
        step1_args += ["--workspace-dir", args.workspace_dir]

    rc, _ = run_step(1, step1_args, logs)
    if rc != 0:
        print(f"\n[ERROR] Step 1 failed. Aborting.")
        return rc

    # Step 2: Fetch Jira
    step2_args = []
    if args.ticket:
        step2_args += ["--ticket", args.ticket]

    rc, _ = run_step(2, step2_args, logs)
    if rc != 0:
        print(f"\n[ERROR] Step 2 failed. Aborting.")
        return rc

    # Step 3: Map
    rc, _ = run_step(3, [], logs)
    if rc != 0:
        print(f"\n[ERROR] Step 3 failed. Aborting.")
        return rc

    # Step 4: Review (auto-approve if --auto-apply)
    step4_args = []
    if args.auto_apply:
        step4_args += ["--confirmed-changes", "all"]

    rc, _ = run_step(4, step4_args, logs)
    if rc != 0:
        print(f"\n[ERROR] Step 4 failed. Aborting.")
        return rc

    # Step 5: Apply
    step5_args = []
    if args.no_tests:
        step5_args += ["--no-tests"]

    rc, _ = run_step(5, step5_args, logs)
    if rc != 0:
        print(f"\n[ERROR] Step 5 failed. Aborting.")
        return rc

    # Step 6: Commit & Push (optional)
    if args.push or args.create_pr:
        step6_args = []
        if args.push:
            step6_args.append("--push")
        if args.create_pr:
            step6_args.append("--create-pr")
        if args.target_branch:
            step6_args += ["--target-branch", args.target_branch]

        rc, _ = run_step(6, step6_args, logs)
        overall_rc = rc

    print(f"\n{'=' * 60}")
    print("ORCHESTRATOR SUMMARY")
    print(f"{'=' * 60}")
    for entry in logs:
        print(f"  {entry}")
    print(f"\n{'[OK] All steps completed.' if overall_rc == 0 else '[WARN] Some steps had issues.'}")
    return overall_rc


def single_step_run(step_num: int, extra_args: list) -> int:
    """Run a single step."""
    print_banner()

    missing = check_prerequisites(step_num)
    if missing:
        print(f"[ERROR] Missing prerequisites for step {step_num}:")
        for m in missing:
            print(f"  - {m}")
        print("Run earlier steps first.")
        return 1

    rc, _ = run_step(step_num, extra_args)
    return rc


def main():
    parser = argparse.ArgumentParser(
        description="Bitbucket + Jira Dev Skill — Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full end-to-end run
  python orchestrator.py --full --ticket PROJ-123

  # Full run with auto-apply (skip confirmation)
  python orchestrator.py --full --ticket PROJ-123 --auto-apply

  # Full run + push + create PR
  python orchestrator.py --full --ticket PROJ-123 --auto-apply --push --create-pr

  # Run single step
  python orchestrator.py --step 1
  python orchestrator.py --step 2 --ticket PROJ-123

  # Run from step 3 onward (assumes steps 0-2 already done)
  python orchestrator.py --step 3
  python orchestrator.py --step 4 --confirmed-changes all
  python orchestrator.py --step 5
  python orchestrator.py --step 6 --push
        """
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--full", action="store_true",
                             help="Run all steps end-to-end")
    mode_group.add_argument("--step", type=int, metavar="N",
                             help="Run a single step (0-6)")

    # Common args
    parser.add_argument("--ticket", help="Jira ticket ID")
    parser.add_argument("--repo-url", help="Bitbucket repo URL")
    parser.add_argument("--workspace-dir", help="Workspace directory")

    # --full specific
    parser.add_argument("--auto-apply", action="store_true",
                         help="Skip confirmation in step 4 (confirm all changes)")
    parser.add_argument("--push", action="store_true",
                         help="Push branch after applying changes")
    parser.add_argument("--create-pr", action="store_true",
                         help="Create Bitbucket PR after push")
    parser.add_argument("--target-branch", default="main",
                         help="PR target branch (default: main)")
    parser.add_argument("--no-tests", action="store_true",
                         help="Skip running tests in step 5")
    parser.add_argument("--reconfigure", action="store_true",
                         help="Re-run setup even if config exists")

    # Extra args to pass to individual steps
    parser.add_argument("--confirmed-changes",
                         help='For --step 4: "all" or "1,3,5"')

    args, unknown = parser.parse_known_args()

    if args.full:
        rc = full_run(args)
        sys.exit(rc)
    else:
        # Build extra args for the specific step
        extra = list(unknown)
        if args.ticket and args.step in (2, 6):
            extra += ["--ticket", args.ticket]
        if args.confirmed_changes and args.step == 4:
            extra += ["--confirmed-changes", args.confirmed_changes]
        if args.push and args.step == 6:
            extra.append("--push")
        if args.create_pr and args.step == 6:
            extra.append("--create-pr")
        if args.no_tests and args.step == 5:
            extra.append("--no-tests")

        rc = single_step_run(args.step, extra)
        sys.exit(rc)


if __name__ == "__main__":
    main()
