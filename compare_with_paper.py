#!/usr/bin/env python3

import os
import json
import argparse
from pathlib import Path


def load_paper_correct_bugs(paper_results_dir: str, version: str, model_label: str) -> set:

    results_path = Path(paper_results_dir)

    # Try common filename patterns
    candidates = list(results_path.glob(f"*{version}*")) + \
                 list(results_path.glob(f"*{model_label}*")) + \
                 list(results_path.glob("*.json"))

    for candidate in candidates:
        try:
            with open(candidate) as f:
                data = json.load(f)
            # Look for a list or dict containing bug IDs
            if isinstance(data, list):
                return set(data)
            if isinstance(data, dict):
                # Could be {"correct": [...]} or {bug_id: {...}}
                for key in ["correct", "correct_fixes", model_label]:
                    if key in data and isinstance(data[key], list):
                        return set(data[key])
        except Exception:
            continue

    print(f"[WARN] Could not load paper results from {paper_results_dir}")
    return set()


def compare(your_results_file: str, paper_results_dir: str,
            version: str, model: str):
    with open(your_results_file) as f:
        your_data = json.load(f)

    your_plausible = {bug_id for bug_id, r in your_data["results"].items()
                      if r["has_plausible"]}

    paper_correct = load_paper_correct_bugs(paper_results_dir, version, model)

    print(f"\n=== Comparison: {version} / {model} ===")
    print(f"Your plausible bugs : {len(your_plausible)}")
    print(f"Paper correct bugs  : {len(paper_correct)}")

    overlap = your_plausible & paper_correct
    print(f"Overlap (you found & paper correct): {len(overlap)}")

    print(f"\nBugs paper marks correct but you missed:")
    missed = paper_correct - your_plausible
    for b in sorted(missed):
        print(f"  - {b}")

    print(f"\nBugs you found plausible but paper doesn't mark correct:")
    extra = your_plausible - paper_correct
    for b in sorted(extra):
        print(f"  + {b}")

    print(f"\n--- Table 2 contribution ---")
    print(f"'LLM raw' correct fixes ≈ {len(overlap)} (of paper's {len(paper_correct)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--your_results", required=True)
    parser.add_argument("--paper_results_dir", default="../results")
    parser.add_argument("--version", default="v1.2")
    parser.add_argument("--model", default="gpt-4o")
    args = parser.parse_args()

    compare(args.your_results, args.paper_results_dir, args.version, args.model)
