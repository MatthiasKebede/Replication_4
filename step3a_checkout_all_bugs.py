#!/usr/bin/env python3
"""
step3a_checkout_all_bugs.py
============================
Helper: checks out every bug from single_function_repair.json that
isn't already checked out. Run this BEFORE step3_prepare_for_java_engine.py.

Usage:
    python step3a_checkout_all_bugs.py \
        --d4j_info_dir  d4j-info \
        --d4j_home      /path/to/defects4j \
        --checkouts_dir /tmp/d4j_checkouts \
        [--dry_run]
"""

import os
import json
import subprocess
import argparse
from pathlib import Path


def checkout_bug(d4j_bin: str, project: str, bug_num: str,
                 dest_path: str, timeout: int = 180) -> bool:
    """Run defects4j checkout. Returns True on success."""
    cmd = [d4j_bin, "checkout",
           "-p", project,
           "-v", f"{bug_num}b",
           "-w", dest_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--d4j_info_dir",  default="d4j-info")
    parser.add_argument("--d4j_home",      required=True,
                        help="Path to Defects4J installation root")
    parser.add_argument("--checkouts_dir", default="/tmp/d4j_checkouts")
    parser.add_argument("--dry_run",       action="store_true",
                        help="Print commands without executing")
    args = parser.parse_args()

    d4j_bin = os.path.join(args.d4j_home, "framework", "bin", "defects4j")
    if not args.dry_run and not os.path.exists(d4j_bin):
        raise FileNotFoundError(f"defects4j binary not found at {d4j_bin}")

    # Load bug list from single_function_repair.json
    # Keys are like "Chart-1" → project=Chart, bug_num=1
    sfr_path = os.path.join(args.d4j_info_dir, "single_function_repair.json")
    with open(sfr_path) as f:
        sfr = json.load(f)

    os.makedirs(args.checkouts_dir, exist_ok=True)

    bugs = list(sfr.keys())
    print(f"Total bugs to checkout: {len(bugs)}")
    print()

    succeeded, skipped, failed_list = 0, 0, []

    for i, bug_id_hyphen in enumerate(bugs, 1):
        # "Chart-1" → project="Chart", num="1"
        parts   = bug_id_hyphen.rsplit("-", 1)
        project = parts[0]
        bug_num = parts[1]

        # Checkout dir uses underscore: Chart_1_buggy
        bug_id_underscore = f"{project}_{bug_num}"
        dest_path = os.path.join(args.checkouts_dir, f"{bug_id_underscore}_buggy")

        if os.path.exists(dest_path):
            print(f"[{i:>4}/{len(bugs)}] SKIP  {bug_id_hyphen}  (already at {dest_path})")
            skipped += 1
            continue

        print(f"[{i:>4}/{len(bugs)}] CHECKOUT  {bug_id_hyphen}  → {dest_path}")

        if args.dry_run:
            print(f"           CMD: {d4j_bin} checkout -p {project} -v {bug_num}b -w {dest_path}")
            skipped += 1
            continue

        try:
            ok = checkout_bug(d4j_bin, project, bug_num, dest_path)
            if ok:
                print(f"           OK")
                succeeded += 1
            else:
                print(f"           FAIL (non-zero exit)")
                failed_list.append(bug_id_hyphen)
        except subprocess.TimeoutExpired:
            print(f"           TIMEOUT")
            failed_list.append(bug_id_hyphen)
        except Exception as e:
            print(f"           ERROR: {e}")
            failed_list.append(bug_id_hyphen)

    print()
    print(f"Done — checked out: {succeeded}, skipped: {skipped}, failed: {len(failed_list)}")
    if failed_list:
        print("Failed bugs:", failed_list)


if __name__ == "__main__":
    main()
