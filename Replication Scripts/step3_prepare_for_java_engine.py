#!/usr/bin/env python3
"""
step3_prepare_for_java_engine.py
=================================
Takes GPT patch JSONs (from step 1) and the Defects4J bug checkouts and
produces the directory structure that GiantRepair's Java engine expects:

  giant_input/
    Chart-1/
      patch_0.java   ← full source file with GPT patch applied
      patch_1.java
      ...
      meta.json      ← bug metadata for the Java engine
    Chart-3/
      ...

The Java engine diffs each patch_N.java against the original to extract
the code modification, builds skeletons, and generates refined patches.

KEY FACTS about the data format:
  - single_function_repair.json keys: "Chart-1"  (hyphen)
  - filelist.json keys             : "Chart_1"   (underscore)
  - Defects4J checkout dirs        : Chart_1_buggy/  (underscore)

This script handles that translation.

Usage:
    python step3_prepare_for_java_engine.py \
        --patches_dir   llm_patches/gpt4o \
        --d4j_info_dir  d4j-info \
        --checkouts_dir /tmp/d4j_checkouts \
        --output_dir    giant_input/gpt4o
"""

import os

import json

import argparse
from pathlib import Path


# ── Key format helpers ────────────────────────────────────────────────────────

def hyphen_to_underscore(bug_id: str) -> str:
    """'Chart-1' → 'Chart_1'"""
    return bug_id.replace("-", "_", 1)


def underscore_to_hyphen(bug_id: str) -> str:
    """'Chart_1' → 'Chart-1'"""
    return bug_id.replace("_", "-", 1)


# ── Patch application ─────────────────────────────────────────────────────────

def apply_patch_to_source(original_content: str,
                           buggy_function: str,
                           patched_function: str) -> str | None:
    """
    Replace buggy_function with patched_function inside original_content.
    Returns the modified file content, or None if the function wasn't found.
    """
    # Try exact match first
    if buggy_function.strip() in original_content:
        return original_content.replace(buggy_function.strip(), patched_function.strip(), 1)

    # Fuzzy: normalise internal whitespace and try again
    # (sometimes leading spaces differ slightly)
    original_lines = original_content.splitlines()
    buggy_lines    = buggy_function.strip().splitlines()

    # Find the block in original_lines that best matches buggy_lines
    for start_idx in range(len(original_lines)):
        window = original_lines[start_idx: start_idx + len(buggy_lines)]
        if len(window) < len(buggy_lines):
            break
        if [l.strip() for l in window] == [l.strip() for l in buggy_lines]:
            # Found it — replace
            new_lines = (original_lines[:start_idx]
                         + patched_function.strip().splitlines()
                         + original_lines[start_idx + len(buggy_lines):])
            return "\n".join(new_lines)

    return None   # could not locate function


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patches_dir",   required=True,
                        help="Dir produced by step1 (contains Chart-1.json, ...)")
    parser.add_argument("--d4j_info_dir",  default="d4j-info")
    parser.add_argument("--checkouts_dir", default="/tmp/d4j_checkouts",
                        help="Where defects4j checkouts live (Chart_1_buggy/ etc.)")
    parser.add_argument("--output_dir",    required=True,
                        help="Where to write staged files for Java engine")
    args = parser.parse_args()

    # Load filelist  (keys: "Chart_1")
    with open(os.path.join(args.d4j_info_dir, "filelist.json")) as f:
        filelist = json.load(f)

    patch_files = sorted(Path(args.patches_dir).glob("*.json"))
    print(f"Staging {len(patch_files)} bugs → {args.output_dir}")
    print()

    skipped, staged, failed = 0, 0, 0

    for pf in patch_files:
        bug_id_hyphen    = pf.stem                          # "Chart-1"
        bug_id_underscore = hyphen_to_underscore(bug_id_hyphen)  # "Chart_1"

        out_bug_dir = os.path.join(args.output_dir, bug_id_hyphen)

        if os.path.exists(out_bug_dir):
            print(f"  SKIP  {bug_id_hyphen} (already staged)")
            skipped += 1
            continue

        # ── Source file path ─────────────────────────────────────────────────
        src_rel = filelist.get(bug_id_underscore)
        if not src_rel:
            print(f"  WARN  {bug_id_hyphen}: not in filelist.json, skipping")
            failed += 1
            continue

        # ── Defects4J checkout path ──────────────────────────────────────────
        checkout_path = os.path.join(args.checkouts_dir, f"{bug_id_underscore}_buggy")
        original_src  = os.path.join(checkout_path, src_rel)

        if not os.path.exists(original_src):
            print(f"  WARN  {bug_id_hyphen}: checkout not found at {checkout_path}")
            print(f"        Run: defects4j checkout -p {bug_id_underscore.split('_')[0]} "
                  f"-v {bug_id_underscore.split('_')[1]}b -w {checkout_path}")
            failed += 1
            continue

        with open(original_src, "r", encoding="utf-8", errors="replace") as f:
            original_content = f.read()

        # ── Load patch data ──────────────────────────────────────────────────
        with open(pf) as f:
            data = json.load(f)

        buggy_function = data.get("buggy_code", "")
        patches        = data.get("patches", [])

        if not patches:
            print(f"  WARN  {bug_id_hyphen}: no patches, skipping")
            failed += 1
            continue

        os.makedirs(out_bug_dir, exist_ok=True)
        n_applied = 0

        for i, patch_code in enumerate(patches):
            patched_content = apply_patch_to_source(
                original_content, buggy_function, patch_code
            )
            if patched_content is None:
                # write a copy of original — Java engine will see no diff
                patched_content = original_content

            # The Java engine expects the full patched source file
            out_patch_file = os.path.join(out_bug_dir, f"patch_{i}.java")
            with open(out_patch_file, "w", encoding="utf-8") as f:
                f.write(patched_content)
            n_applied += 1

        # Write meta.json for Java engine
        project, bug_num = bug_id_underscore.split("_", 1)
        meta = {
            "bug_id":           bug_id_hyphen,
            "bug_id_d4j":       bug_id_underscore,
            "project":          project,
            "bug_number":       bug_num,
            "source_file":      src_rel,
            "checkout_path":    checkout_path,
            "original_source":  original_src,
            "n_patches":        n_applied,
        }
        with open(os.path.join(out_bug_dir, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

        print(f"  OK    {bug_id_hyphen}  →  {n_applied} patch files")
        staged += 1

    print()
    print(f"Done — staged: {staged}, skipped: {skipped}, failed: {failed}")
    if failed:
        print("Bugs that failed need their Defects4J checkouts. Run:")
        print("  defects4j checkout -p <Project> -v <N>b -w /tmp/d4j_checkouts/<Project>_<N>_buggy")


if __name__ == "__main__":
    main()
