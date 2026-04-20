#!/usr/bin/env python3
"""
step2_evaluate_raw_patches.py
==============================
Evaluates GPT patches WITHOUT running Defects4J tests.
Instead it uses the ground-truth fix already stored in
single_function_repair.json (the "fix" field) and checks whether
any GPT patch is functionally equivalent to it.

TWO levels of matching are performed:
  1. Exact match  : strip whitespace, compare strings directly
  2. Fuzzy match  : normalize whitespace/formatting differences

This gives you the "LLM raw correct fixes" count — the left half of Table 2.

NOTE: The paper's actual correctness check was done by running the full
Defects4J test suite + manual semantic comparison. This script is a fast
approximation. For full test-suite validation see step2b_test_suite.py.

Usage:
    python step2_evaluate_raw_patches.py \
        --patches_dir llm_patches/gpt4o \
        --output_file results/raw_eval_gpt4o.json
"""

import os
import re
import json
import argparse
from pathlib import Path


# ── Normalisation ─────────────────────────────────────────────────────────────

def normalise(code: str) -> str:
    """Collapse whitespace so minor formatting differences don't count as diffs."""
    # Remove comments
    code = re.sub(r'//[^\n]*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    # Collapse all whitespace to single space
    code = re.sub(r'\s+', ' ', code)
    return code.strip()


def is_match(patch: str, fix: str) -> bool:
    """Return True if patch matches fix (exact or normalised)."""
    if patch.strip() == fix.strip():
        return True
    if normalise(patch) == normalise(fix):
        return True
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patches_dir",  required=True,
                        help="Dir produced by step1_gpt_inference.py")
    parser.add_argument("--output_file",  required=True,
                        help="Where to write evaluation JSON, e.g. results/raw_eval_gpt4o.json")
    args = parser.parse_args()

    patch_files = sorted(Path(args.patches_dir).glob("*.json"))
    print(f"Evaluating {len(patch_files)} bug files in {args.patches_dir}")

    correct_bugs  = []   # bugs where at least one patch matches fix
    total_bugs    = 0

    per_bug = {}

    for pf in patch_files:
        with open(pf) as f:
            data = json.load(f)

        bug_id    = data["bug_id"]
        fix_code  = data.get("fix_code", "")
        patches   = data.get("patches", [])
        total_bugs += 1

        if not fix_code:
            print(f"  [WARN] No fix_code for {bug_id}, skipping")
            per_bug[bug_id] = {"correct": False, "reason": "no_fix_code"}
            continue

        matched_idx = []
        for i, patch in enumerate(patches):
            if is_match(patch, fix_code):
                matched_idx.append(i)

        is_correct = len(matched_idx) > 0
        if is_correct:
            correct_bugs.append(bug_id)

        per_bug[bug_id] = {
            "correct":         is_correct,
            "n_patches":       len(patches),
            "matched_patches": matched_idx,
        }

        status = "✓ CORRECT" if is_correct else "  wrong  "
        print(f"  {status}  {bug_id}  ({len(patches)} patches, {len(matched_idx)} matched)")

    n_correct = len(correct_bugs)
    print()
    print("=" * 50)
    print(f"Bugs with correct patch : {n_correct} / {total_bugs}")
    print("=" * 50)
    print()
    print("Correct bugs:")
    for b in correct_bugs:
        print(f"  {b}")

    os.makedirs(os.path.dirname(args.output_file) or ".", exist_ok=True)
    output = {
        "patches_dir":       args.patches_dir,
        "total_bugs":        total_bugs,
        "n_correct":         n_correct,
        "correct_bugs":      correct_bugs,
        "per_bug":           per_bug,
    }
    with open(args.output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Results saved → {args.output_file}")


if __name__ == "__main__":
    main()
