import os
import pandas as pd

from evaluation.deepeval_config import (
    evaluation_model,
    EVALUATOR,
    MODEL_NAME,
    ENABLE_FAITHFULNESS,
    ENABLE_ANSWER_RELEVANCY,
    ENABLE_CONTEXTUAL_RELEVANCY
)
from app.services.rag_service import ask_policy

from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
)

# -------------------------------------------------------
# Paths
# -------------------------------------------------------

DATASET_PATH = os.path.join("evaluation","dataset",os.getenv("DATASET"))
RESULTS_DIR = "evaluation/results"
OUTPUT_FILE = os.path.join(RESULTS_DIR, os.getenv("RESULT_FILE"))

os.makedirs(RESULTS_DIR, exist_ok=True)

# -------------------------------------------------------
# Load Dataset
# -------------------------------------------------------

test_cases = pd.read_csv(DATASET_PATH)

print(test_cases.columns.tolist())
print(test_cases.head())

print("=" * 80)
print(f"Loaded {len(test_cases)} Test Cases")
print("=" * 80)

# -------------------------------------------------------
# Initialize Metric
# -------------------------------------------------------

faithfulness = (
    FaithfulnessMetric(model=evaluation_model, include_reason=False)
    if ENABLE_FAITHFULNESS else None
)

answer_relevancy = (
    AnswerRelevancyMetric(model=evaluation_model, include_reason=False)
    if ENABLE_ANSWER_RELEVANCY else None
)

contextual_relevancy = (
    ContextualRelevancyMetric(model=evaluation_model, include_reason=False)
    if ENABLE_CONTEXTUAL_RELEVANCY else None
)

# -------------------------------------------------------
# Store Results
# -------------------------------------------------------

results = []

# -------------------------------------------------------
# Run Evaluation
# -------------------------------------------------------

# for gemini run 5 cases
if EVALUATOR == "gemini":
    total_cases = min(5, len(test_cases))
else:
    total_cases = len(test_cases)

for index, (_, case) in enumerate(test_cases.head(total_cases).iterrows(), start=1):

    print("\n" + "=" * 80)
    print(f"Running {index}/{total_cases}")
    print("=" * 80)

    # -----------------------------------
    # Ask your RAG pipeline
    # -----------------------------------

    response = ask_policy(
        policy_id=1,
        query=case["question"],
        return_context=True
    )

    # -----------------------------------
    # Build DeepEval Test Case
    # -----------------------------------

    test_case = LLMTestCase(
        input=case["question"],
        actual_output=response["answer"],
        expected_output=case["expected_answer"],
        retrieval_context=response["context"]
    )

    # -----------------------------------
    # Evaluate
    # -----------------------------------

    if faithfulness:
        faithfulness.measure(test_case)

    if answer_relevancy:
        answer_relevancy.measure(test_case)

    if contextual_relevancy:
        contextual_relevancy.measure(test_case)

    # -----------------------------------
    # Print
    # -----------------------------------

    print("\nQuestion")
    print("-" * 40)
    print(case["question"])

    print("\nExpected")
    print("-" * 40)
    print(case["expected_answer"])

    print("\nGenerated")
    print("-" * 40)
    print(response["answer"])

    print("\nFaithfulness Score")
    print("-" * 40)
    print(f"{faithfulness.score:.2f}")

    print("\nReason")
    print("-" * 40)
    print(faithfulness.reason)

    # -----------------------------------
    # Save Result
    # -----------------------------------

    results.append({
        "Evaluator": EVALUATOR,
        "Model": MODEL_NAME,
        "Category": case["category"],
        "Difficulty": case["difficulty"],
        "Question": case["question"],
        "Expected Answer": case["expected_answer"],
        "Generated Answer": response["answer"],
        "Faithfulness": faithfulness.score if faithfulness else None,
        "Answer Relevancy": answer_relevancy.score if answer_relevancy else None,
        "Contextual Relevancy": contextual_relevancy.score if contextual_relevancy else None,
    })
    

# -------------------------------------------------------
# Export Results
# -------------------------------------------------------

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 80)
print("Evaluation Complete")
print("=" * 80)

print(f"\nTotal Test Cases : {total_cases}")

print(f"Results Saved    : {OUTPUT_FILE}")

print("\nAverage Scores")
print("-"*40)
if ENABLE_FAITHFULNESS: print(f"Faithfulness         : {results_df['Faithfulness'].mean():.2f}")
if ENABLE_ANSWER_RELEVANCY: print(f"Answer Relevancy     : {results_df['Answer Relevancy'].mean():.2f}")
if ENABLE_CONTEXTUAL_RELEVANCY: print(f"Context Relevancy    : {results_df['Contextual Relevancy'].mean():.2f}")


