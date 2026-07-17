import os
import sys
import pandas as pd

from evaluation.deepeval_config import (
    evaluation_model,
    EVALUATOR,
    MODEL_NAME,
    ENABLE_FAITHFULNESS,
    ENABLE_ANSWER_RELEVANCY,
    ENABLE_CONTEXTUAL_RELEVANCY,
)
from app.services.rag_service import ask_policy

from deepeval import evaluate
from deepeval.evaluate.configs import CacheConfig
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
)

# -------------------------------------------------------
# Config knobs
# -------------------------------------------------------

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Cap how many cases run against paid/rate-limited evaluators (e.g. Gemini).
# Configurable instead of hardcoded so you're not editing code to change cost.
GEMINI_CASE_LIMIT = int(os.getenv("GEMINI_CASE_LIMIT", "5"))

# -------------------------------------------------------
# Paths
# -------------------------------------------------------

DATASET = os.getenv("DATASET")
RESULT_FILE = os.getenv("RESULT_FILE")

if not DATASET or not RESULT_FILE:
    raise ValueError(
        "Both DATASET and RESULT_FILE environment variables must be set "
        "(e.g. DATASET=policy_questions.csv RESULT_FILE=run1.csv)."
    )

DATASET_PATH = os.path.join("evaluation", "dataset", DATASET)
RESULTS_DIR = "evaluation/results"
OUTPUT_FILE = os.path.join(RESULTS_DIR, RESULT_FILE)

os.makedirs(RESULTS_DIR, exist_ok=True)

# -------------------------------------------------------
# Load Dataset
# -------------------------------------------------------

if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

test_cases_df = pd.read_csv(DATASET_PATH)

REQUIRED_COLUMNS = {"question", "expected_answer", "category", "difficulty"}
missing_cols = REQUIRED_COLUMNS - set(test_cases_df.columns)
if missing_cols:
    raise ValueError(f"Dataset is missing required columns: {missing_cols}")

if DEBUG:
    print(test_cases_df.columns.tolist())
    print(test_cases_df.head())

print("=" * 80)
print(f"Loaded {len(test_cases_df)} Test Cases")
print("=" * 80)

# -------------------------------------------------------
# Initialize Metrics
# -------------------------------------------------------
# include_reason=True so the reasons we print later actually exist.
# Reasons cost one extra judge call per metric per case -- set back to
# False if you want to trade explainability for speed/cost.

faithfulness = (
    FaithfulnessMetric(model=evaluation_model, include_reason=True)
    if ENABLE_FAITHFULNESS else None
)

answer_relevancy = (
    AnswerRelevancyMetric(model=evaluation_model, include_reason=True)
    if ENABLE_ANSWER_RELEVANCY else None
)

contextual_relevancy = (
    ContextualRelevancyMetric(model=evaluation_model, include_reason=True)
    if ENABLE_CONTEXTUAL_RELEVANCY else None
)

active_metrics = [m for m in (faithfulness, answer_relevancy, contextual_relevancy) if m]

if not active_metrics:
    raise ValueError(
        "No metrics are enabled. Set at least one of ENABLE_FAITHFULNESS, "
        "ENABLE_ANSWER_RELEVANCY, ENABLE_CONTEXTUAL_RELEVANCY to true."
    )

# -------------------------------------------------------
# Determine how many cases to run
# -------------------------------------------------------

if EVALUATOR == "gemini":
    total_cases = min(GEMINI_CASE_LIMIT, len(test_cases_df))
else:
    total_cases = len(test_cases_df)

# -------------------------------------------------------
# Step 1: Run the RAG pipeline and build LLMTestCases
# -------------------------------------------------------
# Kept separate from evaluation so a RAG failure on one case doesn't
# discard the test cases already built for every other case.

llm_test_cases = []
case_metadata = []  # keeps question/category/etc. aligned with llm_test_cases
failed_cases = []   # cases that errored out, recorded separately

for index, (_, case) in enumerate(test_cases_df.head(total_cases).iterrows(), start=1):
    print("\n" + "=" * 80)
    print(f"Generating answer {index}/{total_cases}")
    print("=" * 80)

    try:
        response = ask_policy(
            policy_id=1,
            query=case["question"],
            return_context=True,
        )

        retrieval_context = response["context"]
        if not retrieval_context:
            print(f"[WARN] Case {index}: empty retrieval_context returned by ask_policy")

        test_case = LLMTestCase(
            input=case["question"],
            actual_output=response["answer"],
            expected_output=case["expected_answer"],
            retrieval_context=retrieval_context,
        )

        llm_test_cases.append(test_case)
        case_metadata.append({
            "Category": case["category"],
            "Difficulty": case["difficulty"],
        })

    except Exception as e:
        print(f"[ERROR] Case {index} failed during RAG generation: {e}", file=sys.stderr)
        failed_cases.append({
            "Evaluator": EVALUATOR,
            "Model": MODEL_NAME,
            "Category": case.get("category"),
            "Difficulty": case.get("difficulty"),
            "Question": case.get("question"),
            "Expected Answer": case.get("expected_answer"),
            "Generated Answer": None,
            "Faithfulness": None,
            "Answer Relevancy": None,
            "Contextual Relevancy": None,
            "Error": str(e),
        })

print("\n" + "=" * 80)
print(f"Generated {len(llm_test_cases)}/{total_cases} answers "
      f"({len(failed_cases)} failed)")
print("=" * 80)

# -------------------------------------------------------
# Step 2: Evaluate all test cases in one batch
# -------------------------------------------------------
# Uses deepeval's evaluate() instead of calling .measure() one metric at a
# time in a Python loop -- this runs metrics concurrently and supports
# caching so a re-run doesn't re-pay for cases already scored.

results = list(failed_cases)  # start with any RAG-generation failures

if llm_test_cases:
    eval_output = evaluate(
        test_cases=llm_test_cases,
        metrics=active_metrics,
        cache_config=CacheConfig(write_cache=True, use_cache=False),
    )

    for meta, test_result in zip(case_metadata, eval_output.test_results):
        scores = {}
        reasons = {}
        for metric_data in test_result.metrics_data:
            scores[metric_data.name] = metric_data.score
            reasons[metric_data.name] = metric_data.reason

        print("\n" + "-" * 80)
        print(f"Question   : {test_result.input}")
        print(f"Expected   : {test_result.expected_output}")
        print(f"Generated  : {test_result.actual_output}")
        for name, score in scores.items():
            score_str = f"{score:.2f}" if score is not None else "N/A"
            print(f"{name:<22}: {score_str}  ({reasons.get(name) or 'no reason recorded'})")

        results.append({
            "Evaluator": EVALUATOR,
            "Model": MODEL_NAME,
            "Category": meta["Category"],
            "Difficulty": meta["Difficulty"],
            "Question": test_result.input,
            "Expected Answer": test_result.expected_output,
            "Generated Answer": test_result.actual_output,
            "Faithfulness": scores.get("Faithfulness"),
            "Answer Relevancy": scores.get("Answer Relevancy"),
            "Contextual Relevancy": scores.get("Contextual Relevancy"),
            "Error": None,
        })

# -------------------------------------------------------
# Export Results
# -------------------------------------------------------

results_df = pd.DataFrame(results)
results_df.to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 80)
print("Evaluation Complete")
print("=" * 80)

print(f"\nTotal Test Cases Attempted : {total_cases}")
print(f"Successfully Evaluated     : {len(llm_test_cases)}")
print(f"Failed                     : {len(failed_cases)}")
print(f"Results Saved              : {OUTPUT_FILE}")

print("\nAverage Scores (successful cases only)")
print("-" * 40)
if ENABLE_FAITHFULNESS and results_df["Faithfulness"].notna().any():
    print(f"Faithfulness         : {results_df['Faithfulness'].mean():.2f}")
if ENABLE_ANSWER_RELEVANCY and results_df["Answer Relevancy"].notna().any():
    print(f"Answer Relevancy     : {results_df['Answer Relevancy'].mean():.2f}")
if ENABLE_CONTEXTUAL_RELEVANCY and results_df["Contextual Relevancy"].notna().any():
    print(f"Contextual Relevancy : {results_df['Contextual Relevancy'].mean():.2f}")

if failed_cases:
    print(f"\n[WARN] {len(failed_cases)} case(s) failed and were logged with an Error "
          f"message in {OUTPUT_FILE}. Review those before trusting the averages above.")