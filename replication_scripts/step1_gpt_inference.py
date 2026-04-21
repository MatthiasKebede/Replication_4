
import os
import json
import time
import argparse
from pathlib import Path
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from environment


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are an expert Java developer specializing in automated program repair. "
    "You will be given a buggy Java method. Your task is to produce a fixed version. "
    "Return ONLY the complete fixed method — no explanation, no markdown fences, "
    "no preamble. The output must be valid Java that can replace the original method directly."
)


def build_user_prompt(bug_id: str, buggy_code: str) -> str:
    return (
        f"Bug ID: {bug_id}\n\n"
        f"The following Java method contains a bug. Fix it:\n\n"
        f"{buggy_code}\n\n"
        f"Return only the fixed Java method, nothing else."
    )



def call_gpt(bug_id: str, buggy_code: str, model: str,
             n_patches: int, temperature: float) -> list[str]:
    """Call OpenAI chat API, return list of patch strings."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(bug_id, buggy_code)},
            ],
            n=n_patches,
            temperature=temperature,
            max_tokens=2048,
        )
        return [choice.message.content for choice in response.choices]
    except Exception as e:
        print(f"    [API ERROR] {e}")
        return []


def clean_patch(raw: str) -> str:
    """Strip markdown fences if the model added them despite instructions."""
    s = raw.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        lines = lines[1:]                           
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]                      
        s = "\n".join(lines).strip()
    return s



def main():
    parser = argparse.ArgumentParser(
        description="Generate GPT patches for Defects4J bugs"
    )
    parser.add_argument("--d4j_info_dir",  default="d4j-info",
                        help="Path to the d4j-info/ folder (default: d4j-info)")
    parser.add_argument("--output_dir",    required=True,
                        help="Where to save patch JSONs, e.g. llm_patches/gpt4o/v1.2")
    parser.add_argument("--model",         default="gpt-4o",
                        help="OpenAI model (default: gpt-4o)")
    parser.add_argument("--n_patches",     type=int, default=10,
                        help="Patches to generate per bug (paper uses 10)")
    parser.add_argument("--temperature",   type=float, default=0.8,
                        help="Sampling temperature (paper uses 0.8)")
    parser.add_argument("--delay",         type=float, default=1.0,
                        help="Seconds to wait between bugs (rate limiting)")
    parser.add_argument("--bug_limit",     type=int,   default=None,
                        help="Only process this many bugs (for quick tests)")
    args = parser.parse_args()

    sfr_path = os.path.join(args.d4j_info_dir, "single_function_repair.json")
    with open(sfr_path) as f:
        sfr = json.load(f)        

    os.makedirs(args.output_dir, exist_ok=True)

    bug_ids = list(sfr.keys())
    if args.bug_limit:
        bug_ids = bug_ids[:args.bug_limit]

    print(f"Model          : {args.model}")
    print(f"Patches per bug: {args.n_patches}")
    print(f"Temperature    : {args.temperature}")
    print(f"Total bugs     : {len(bug_ids)}")
    print(f"Output dir     : {args.output_dir}")
    print()

    succeeded, skipped, failed = 0, 0, 0

    for i, bug_id in enumerate(bug_ids, 1):
        out_file = os.path.join(args.output_dir, f"{bug_id}.json")

        if os.path.exists(out_file):
            print(f"[{i:>4}/{len(bug_ids)}] SKIP  {bug_id}")
            skipped += 1
            continue

        entry      = sfr[bug_id]
        buggy_code = entry["buggy"]
        fix_code   = entry.get("fix", "")   # ground-truth (used later for correctness check)

        print(f"[{i:>4}/{len(bug_ids)}] {bug_id} ...", end=" ", flush=True)

        raw_patches = call_gpt(
            bug_id=bug_id,
            buggy_code=buggy_code,
            model=args.model,
            n_patches=args.n_patches,
            temperature=args.temperature,
        )

        if not raw_patches:
            print("FAIL")
            failed += 1
            continue

        patches = [clean_patch(p) for p in raw_patches]

        result = {
            "bug_id":       bug_id,
            "model":        args.model,
            "buggy_code":   buggy_code,
            "fix_code":     fix_code,           # ground truth stored here for step 2
            "start_line":   entry.get("start"),
            "end_line":     entry.get("end"),
            "patches":      patches,
        }

        with open(out_file, "w") as f:
            json.dump(result, f, indent=2)

        print(f"OK  ({len(patches)} patches)")
        succeeded += 1
        time.sleep(args.delay)

    print()
    print(f"Done — succeeded: {succeeded}, skipped: {skipped}, failed: {failed}")
    if failed:
        print("Check your API key and network; re-run the script to retry failed bugs.")


if __name__ == "__main__":
    main()
