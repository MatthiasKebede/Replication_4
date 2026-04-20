#!/usr/bin/env python3
"""
read_precomputed_results.py
============================
The GiantRepair repo's results/ directory contains the authors'
pre-computed patch counts. This script reads them and builds Table 2,
combining them with YOUR raw LLM results from step2.

This is the practical path when ExpressAPR is not installed.

Usage:
    python read_precomputed_results.py \
        --repo_root      ~/GiantRepair \
        --your_raw_eval  eval_results/raw_eval_gpt4o-mini.json
"""

import os
import json
import argparse
from pathlib import Path


def explore_results_dir(results_dir: str):
    """Read and display everything in the results/ directory."""
    print(f"=== Contents of {results_dir} ===\n")

    all_results = {}

    for f in sorted(Path(results_dir).rglob("*")):
        if f.is_dir():
            print(f"DIR: {f.relative_to(results_dir)}/")
            continue

        rel = str(f.relative_to(results_dir))
        print(f"\nFILE: {rel}")

        if f.suffix == ".json":
            try:
                with open(f) as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())}")
                    # Look for bug lists
                    for key, val in data.items():
                        if isinstance(val, list) and len(val) > 0:
                            print(f"  {key}: {len(val)} items → e.g. {val[:3]}")
                        elif isinstance(val, (int, float, str)):
                            print(f"  {key}: {val}")
                elif isinstance(data, list):
                    print(f"  List of {len(data)} items → e.g. {data[:3]}")
                all_results[rel] = data
            except Exception as e:
                print(f"  (could not parse: {e})")
        elif f.suffix == ".txt":
            try:
                content = f.read_text()[:200]
                print(f"  Content preview: {content!r}")
            except Exception:
                pass

    return all_results


def extract_correct_counts(results_dir: str) -> dict:
    """
    Try to extract per-model correct fix counts from results/.
    Returns: {model_label: {version: count, bugs: [...]}}
    """
    counts = {}

    for f in sorted(Path(results_dir).rglob("*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
        except Exception:
            continue

        fname = f.stem.lower()

        # Try to identify model and version from filename
        for model in ["gpt4", "gpt35", "chatgpt", "codex", "incoder",
                       "starcoder", "codellama", "llama"]:
            if model in fname:
                for ver in ["v1.2", "v12", "v2.0", "v20"]:
                    v = ver.replace(".", "")
                    if v in fname.replace(".", ""):
                        key = f"{model}_{ver}"
                        # Extract count
                        n = data.get("n_correct",
                            data.get("correct_count",
                            data.get("count",
                            data.get("total", None))))
                        bugs = data.get("correct_bugs",
                               data.get("correct_fixes",
                               data.get("bugs", [])))
                        if n is None and isinstance(bugs, list):
                            n = len(bugs)
                        if n is not None:
                            counts[key] = {"n": n, "bugs": bugs}
                            break

    return counts


def print_table2(counts: dict, your_raw: dict = None):
    """Print Table 2 comparing paper results with your results."""
    # Paper's ground truth numbers
    paper = {
        "codex_v1.2":   {"raw": 43, "gr": 53},
        "chatgpt_v1.2": {"raw": 42, "gr": 55},
        "gpt4_v1.2":    {"raw": 40, "gr": 51},
        "incoder_v1.2": {"raw": 19, "gr": 25},
        "codex_v2.0":   {"raw": 45, "gr": 53},
        "chatgpt_v2.0": {"raw": 44, "gr": 54},
        "gpt4_v2.0":    {"raw": 34, "gr": 43},
        "incoder_v2.0": {"raw": 18, "gr": 24},
    }

    print()
    print("=" * 72)
    print("  TABLE 2  —  Correct Fixes on Defects4J")
    print("=" * 72)
    print(f"{'Method':<22} {'D4J v1.2 raw':>12} {'D4J v1.2 +GR':>13} "
          f"{'D4J v2.0 raw':>12} {'D4J v2.0 +GR':>13}")
    print("-" * 72)

    # Paper rows
    models = [("CodeX",   "codex"),
              ("ChatGPT", "chatgpt"),
              ("GPT-4",   "gpt4"),
              ("InCoder", "incoder")]

    for label, key in models:
        r12  = paper.get(f"{key}_v1.2", {}).get("raw", "?")
        gr12 = paper.get(f"{key}_v1.2", {}).get("gr",  "?")
        r20  = paper.get(f"{key}_v2.0", {}).get("raw", "?")
        gr20 = paper.get(f"{key}_v2.0", {}).get("gr",  "?")
        print(f"  {label+' (paper)':<20} {str(r12):>12} {str(gr12):>13} "
              f"{str(r20):>12} {str(gr20):>13}")

    print("-" * 72)
    print("  [YOUR RESULTS]")

    # Your raw results
    if your_raw:
        n_raw = your_raw.get("n_correct", "?")
        model = your_raw.get("patches_dir", "your model").split("/")[-1]
        print(f"  {model:<20} {str(n_raw):>12} {'(need ExpressAPR)':>13} "
              f"{'(run v2.0)':>12} {'(need ExpressAPR)':>13}")

    # Any results found in repo
    for key, val in sorted(counts.items()):
        print(f"  {key:<20} {str(val['n']):>12}")

    print("=" * 72)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_root",     default=".")
    parser.add_argument("--your_raw_eval", default=None,
                        help="Path to your step2 eval results JSON")
    args = parser.parse_args()

    repo_root   = os.path.expanduser(args.repo_root)
    results_dir = os.path.join(repo_root, "results")

    your_raw = None
    if args.your_raw_eval and os.path.exists(args.your_raw_eval):
        with open(args.your_raw_eval) as f:
            your_raw = json.load(f)

    if not os.path.exists(results_dir):
        print(f"results/ directory not found at {results_dir}")
        print("Looking for results in current directory...")
        results_dir = "results"

    if os.path.exists(results_dir):
        all_results = explore_results_dir(results_dir)
        counts = extract_correct_counts(results_dir)
    else:
        print("No results directory found.")
        all_results = {}
        counts = {}

    print_table2(counts, your_raw)


    if your_raw:
        n = your_raw.get("n_correct", 0)
        bugs = your_raw.get("correct_bugs", [])
        paper_chatgpt = 42
        print(f"Your gpt4o-mini raw correct fixes: {n}")
        print(f"Paper's ChatGPT raw correct fixes: {paper_chatgpt}")
        print(f"Difference: {n - paper_chatgpt:+d}")
        if bugs:
            print(f"\nYour correctly fixed bugs:")
            for b in sorted(bugs)[:20]:
                print(f"  {b}")
            if len(bugs) > 20:
                print(f"  ... and {len(bugs)-20} more")


if __name__ == "__main__":
    main()
