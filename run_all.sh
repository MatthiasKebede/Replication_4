#!/usr/bin/env bash
# =============================================================================
# run_all.sh  —  GiantRepair Replication: Master Script
# =============================================================================
# Fill in the variables in the CONFIG section, then run sections one at a time.
# DO NOT run this whole file at once — some steps take hours.
# =============================================================================

# ── CONFIG — Edit these ──────────────────────────────────────────────────────
REPO_ROOT="$HOME/GiantRepair"           # root of the cloned GiantRepair repo
D4J_HOME="$HOME/defects4j"             # path to Defects4J installation
CHECKOUTS="/tmp/d4j_checkouts"          # where D4J bug checkouts will live
SCRIPTS_DIR="$REPO_ROOT/LLM_Inference" # where you put the step*.py scripts
export OPENAI_API_KEY="sk-..."          # your OpenAI key
# ─────────────────────────────────────────────────────────────────────────────

cd "$REPO_ROOT"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 0: Install Python deps
# ═════════════════════════════════════════════════════════════════════════════
# pip install openai tqdm


# ═════════════════════════════════════════════════════════════════════════════
# STEP 1: Call GPT API to generate patches
#
# Do this for EACH model you want to reproduce.
# The paper uses ChatGPT (~gpt-3.5) and GPT-4.
# We map them to: gpt-3.5-turbo-0125  and  gpt-4o
#
# Each run costs roughly:
#   gpt-3.5-turbo: ~$1-2  per D4J version (very cheap)
#   gpt-4o:        ~$15-25 per D4J version
#
# TIP: Test with --bug_limit 5 first to check everything works.
# ═════════════════════════════════════════════════════════════════════════════

# --- Test run first (5 bugs only) ---
# python "$SCRIPTS_DIR/step1_gpt_inference.py" \
#     --d4j_info_dir d4j-info \
#     --output_dir   llm_patches/test_gpt4o \
#     --model        gpt-4o \
#     --n_patches    10 \
#     --bug_limit    5

# --- Full run: gpt-3.5 (approximates "ChatGPT" in paper) ---
python "$SCRIPTS_DIR/step1_gpt_inference.py" \
    --d4j_info_dir d4j-info \
    --output_dir   llm_patches/gpt35 \
    --model        gpt-3.5-turbo-0125 \
    --n_patches    10 \
    --temperature  0.8

# --- Full run: gpt-4o (approximates "GPT-4" in paper) ---
python "$SCRIPTS_DIR/step1_gpt_inference.py" \
    --d4j_info_dir d4j-info \
    --output_dir   llm_patches/gpt4o-mini \
    --model        gpt-4o-mini \
    --n_patches    10 \
    --temperature  0.8


# ═════════════════════════════════════════════════════════════════════════════
# STEP 2: Evaluate raw LLM patches (gives you left columns of Table 2)
#
# This checks if any GPT patch exactly matches the known correct fix
# stored in single_function_repair.json. Fast — no Defects4J needed.
# ═════════════════════════════════════════════════════════════════════════════

mkdir -p eval_results

python "$SCRIPTS_DIR/step2_evaluate_raw_patches.py" \
    --patches_dir llm_patches/gpt35 \
    --output_file eval_results/raw_eval_gpt35.json

python "$SCRIPTS_DIR/step2_evaluate_raw_patches.py" \
    --patches_dir llm_patches/gpt4o-mini \
    --output_file eval_results/raw_eval_gpt4o-mini.json


# ═════════════════════════════════════════════════════════════════════════════
# STEP 3a: Checkout all Defects4J bugs (needed for Java engine)
#
# This takes a LONG time (several hours for all bugs).
# It's safe to interrupt and restart — already-checked-out bugs are skipped.
# ═════════════════════════════════════════════════════════════════════════════

python "$SCRIPTS_DIR/step3a_checkout_all_bugs.py" \
    --d4j_info_dir  d4j-info \
    --d4j_home      "$D4J_HOME" \
    --checkouts_dir "$CHECKOUTS"


# ═════════════════════════════════════════════════════════════════════════════
# STEP 3b: Stage patches for GiantRepair Java engine
#
# This writes full patched source files that the Java engine will diff
# against the originals to extract code modifications.
# ═════════════════════════════════════════════════════════════════════════════

python "$SCRIPTS_DIR/step3_prepare_for_java_engine.py" \
    --patches_dir   llm_patches/gpt35 \
    --d4j_info_dir  d4j-info \
    --checkouts_dir "$CHECKOUTS" \
    --output_dir    giant_input/gpt35

python "$SCRIPTS_DIR/step3_prepare_for_java_engine.py" \
    --patches_dir   llm_patches/gpt4o-mini \
    --d4j_info_dir  d4j-info \
    --checkouts_dir "$CHECKOUTS" \
    --output_dir    giant_input/gpt4o-mini


# ═════════════════════════════════════════════════════════════════════════════
# STEP 4: Run GiantRepair Java engine
#
# First build the Java project, then run it.
# See GiantRepair/README.md for exact config file format.
# ═════════════════════════════════════════════════════════════════════════════

cd "$REPO_ROOT/GiantRepair"
mvn clean package -DskipTests

# Then run the engine (exact command depends on GiantRepair's main class/config)
# Typical command — verify against GiantRepair/README.md:
java -jar artifacts//GiantRepair-1.0-SNAPSHOT-runnable.jar \
    --input  "$REPO_ROOT/giant_input/gpt4o-mini" \
    --output "$REPO_ROOT/giant_output/gpt4o-mini" \
    --d4j    "$D4J_HOME" \
    --checkouts "$CHECKOUTS"

cd "$REPO_ROOT"


# ═════════════════════════════════════════════════════════════════════════════
# STEP 5: Build Table 2
# ═════════════════════════════════════════════════════════════════════════════

python "$SCRIPTS_DIR/step4_build_table2.py" \
    --raw_gpt35   eval_results/raw_eval_gpt35.json \
    --raw_gpt4o   eval_results/raw_eval_gpt4o.json \
    --giant_gpt35 eval_results/giant_eval_gpt35.json \
    --giant_gpt4o eval_results/giant_eval_gpt4o.json
