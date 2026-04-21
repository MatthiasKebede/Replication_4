#!/usr/bin/env bash

REPO_ROOT="$HOME/GiantRepair"           # root of the cloned GiantRepair repo
D4J_HOME="$HOME/defects4j"             # path to Defects4J installation
CHECKOUTS="/tmp/d4j_checkouts"          # where D4J bug checkouts will live
SCRIPTS_DIR="$REPO_ROOT/LLM_Inference" # where you put the step*.py scripts
export OPENAI_API_KEY="sk-..."          # your OpenAI key

cd "$REPO_ROOT"

# step 1 gpt inferenc
python "$SCRIPTS_DIR/step1_gpt_inference.py" \
    --d4j_info_dir d4j-info \
    --output_dir   llm_patches/gpt4o-mini \
    --model        gpt-4o-mini \
    --n_patches    10 \
    --temperature  0.8


# STEP 2: Evaluate raw LLM patches (without running the Java engine)

mkdir -p eval_results

python "$SCRIPTS_DIR/step2_evaluate_raw_patches.py" \
    --patches_dir llm_patches/gpt4o-mini \
    --output_file eval_results/raw_eval_gpt4o-mini.json



# STEP 3a: Checkout all Defects4J bugs (needed for Java engine)


python "$SCRIPTS_DIR/step3a_checkout_all_bugs.py" \
    --d4j_info_dir  d4j-info \
    --d4j_home      "$D4J_HOME" \
    --checkouts_dir "$CHECKOUTS"


# STEP 3b: Stage patches for GiantRepair Java engine


python "$SCRIPTS_DIR/step3_prepare_for_java_engine.py" \
    --patches_dir   llm_patches/gpt4o-mini \
    --d4j_info_dir  d4j-info \
    --checkouts_dir "$CHECKOUTS" \
    --output_dir    giant_input/gpt4o-mini


# STEP 4: Run GiantRepair Java engine


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



# STEP 5: Build Table 2
# this will now work if  expressapr is not workinng

python "$SCRIPTS_DIR/step4_build_table2.py" \
    --raw_gpt35   eval_results/raw_eval_gpt35.json \
    --raw_gpt4o   eval_results/raw_eval_gpt4o.json \
    --giant_gpt35 eval_results/giant_eval_gpt35.json \
    --giant_gpt4o eval_results/giant_eval_gpt4o.json
