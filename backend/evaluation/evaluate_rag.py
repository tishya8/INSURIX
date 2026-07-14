import os
import pandas as pd

from evaluation.deepeval_config import (
    evaluation_model,
    EVALUATOR
)
from app.services.rag_service import ask_policy

from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric

# -------------------------------------------------------
# Paths
# -------------------------------------------------------

DATASET_PATH = "evaluation/dataset/test_dataset_day2.csv"
RESULTS_DIR = "evaluation/results"
OUTPUT_FILE = os.path.join(RESULTS_DIR, "day1_results.csv")

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

# faithfulness = FaithfulnessMetric(
#     model=evaluation_model
# )

# for gemini exclude reason
faithfulness = FaithfulnessMetric(
    model=evaluation_model,
    include_reason=False
)

# -------------------------------------------------------
# Store Results
# -------------------------------------------------------

results = []

# -------------------------------------------------------
# Run Evaluation
# -------------------------------------------------------

# for gemini run 5 cases
total_cases = min(5, len(test_cases))

# for ollama run all
# total_cases = len(test_cases)

for index, (_, case) in enumerate(test_cases.iterrows(), start=1):

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

    faithfulness.measure(test_case)

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
        "Category": case["category"],
        "Difficulty": case["difficulty"],
        "Question": case["question"],
        "Expected Answer": case["expected_answer"],
        "Generated Answer": response["answer"],
        "Faithfulness": faithfulness.score,
        "Reason": faithfulness.reason
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

print(f"\nAverage Faithfulness : {results_df['Faithfulness'].mean():.2f}")






# from evaluation.test_cases import TEST_CASES
# from evaluation.deepeval_config import evaluation_model

# from app.services.rag_service import ask_policy

# from deepeval.test_case import LLMTestCase
# from deepeval.metrics import (
#     FaithfulnessMetric,
#     AnswerRelevancyMetric,
#     ContextualRelevancyMetric,
# )

# import pandas as pd

# # -------------------------------------------------------
# # Initialize metrics (create once)
# # -------------------------------------------------------

# faithfulness = FaithfulnessMetric(model=evaluation_model)

# # answer_relevancy = AnswerRelevancyMetric(model=evaluation_model)

# # contextual_relevancy = ContextualRelevancyMetric(model=evaluation_model)

# # -------------------------------------------------------
# # Store evaluation results
# # -------------------------------------------------------

# results = []

# # -------------------------------------------------------
# # Evaluate each test case
# # -------------------------------------------------------

# for index, case in enumerate(TEST_CASES, start=1):

#     print("\n" + "=" * 80)
#     print(f"TEST CASE {index}")
#     print("=" * 80)

#     # Run your RAG pipeline
#     response = ask_policy(
#         policy_id=case["policy_id"],
#         query=case["question"],
#         return_context=True
#     )

#     # Create DeepEval test case
#     test_case = LLMTestCase(
#         input=case["question"],
#         actual_output=response["answer"],
#         expected_output=case["expected_answer"],
#         retrieval_context=response["context"]
#     )

#     # Evaluate
#     faithfulness.measure(test_case)
#     # answer_relevancy.measure(test_case)
#     # contextual_relevancy.measure(test_case)

#     # Print results
#     print(f"\nQuestion:")
#     print(case["question"])

#     print(f"\nExpected Answer:")
#     print(case["expected_answer"])

#     print(f"\nGenerated Answer:")
#     print(response["answer"])

#     print("\nScores")
#     print("-" * 40)

#     print(f"Faithfulness         : {faithfulness.score:.2f}")
#     print(f"Answer Relevancy     : {answer_relevancy.score:.2f}")
#     print(f"Context Relevancy    : {contextual_relevancy.score:.2f}")

#     print("\nReasons")
#     print("-" * 40)

#     print("Faithfulness:")
#     print(faithfulness.reason)

#     print("\nAnswer Relevancy:")
#     print(answer_relevancy.reason)

#     print("\nContext Relevancy:")
#     print(contextual_relevancy.reason)

#     # Save results
#     results.append({
#         "Question": case["question"],
#         "Expected Answer": case["expected_answer"],
#         "Generated Answer": response["answer"],
#         "Faithfulness": faithfulness.score,
#         "Answer Relevancy": answer_relevancy.score,
#         "Contextual Relevancy": contextual_relevancy.score,
#         "Faithfulness Reason": faithfulness.reason,
#         "Answer Relevancy Reason": answer_relevancy.reason,
#         "Contextual Relevancy Reason": contextual_relevancy.reason,
#     })

# # -------------------------------------------------------
# # Export results
# # -------------------------------------------------------

# df = pd.DataFrame(results)

# output_file = "evaluation_results.csv"

# df.to_csv(output_file, index=False)

# print("\n" + "=" * 80)
# print("Evaluation Complete")
# print("=" * 80)

# print(f"\nTotal Test Cases : {len(TEST_CASES)}")
# print(f"CSV Report Saved : {output_file}")

# print("\nAverage Scores")
# print("-" * 40)

# print(f"Faithfulness      : {df['Faithfulness'].mean():.2f}")
# print(f"Answer Relevancy  : {df['Answer Relevancy'].mean():.2f}")
# print(f"Context Relevancy : {df['Contextual Relevancy'].mean():.2f}")


# from evaluation.test_cases import TEST_CASES
# from evaluation.deepeval_config import evaluation_model

# from app.services.rag_service import ask_policy

# from deepeval.test_case import LLMTestCase
# from deepeval.metrics import FaithfulnessMetric

# case = TEST_CASES[0]

# print("=" * 80)
# print("QUESTION:")
# print(case["question"])

# result = ask_policy(
#     policy_id=case["policy_id"],
#     query=case["question"],
#     return_context=True
# )

# print("\nGENERATED ANSWER:")
# print(result["answer"])

# print("\nEXPECTED ANSWER:")
# print(case["expected_answer"])

# print("\nRETRIEVED CHUNKS:")
# for i, chunk in enumerate(result["context"], start=1):
#     print(f"\nChunk {i}")
#     print(chunk)

# test_case = LLMTestCase(
#     input=case["question"],
#     actual_output=result["answer"],
#     expected_output=case["expected_answer"],
#     retrieval_context=result["context"]
# )

# metric = FaithfulnessMetric(
#     model=evaluation_model
# )

# metric.measure(test_case)

# print("\n" + "=" * 80)
# print("FAITHFULNESS SCORE")
# print("=" * 80)

# print(metric.score)
# print(metric.reason)




# from evaluation.test_cases import TEST_CASES
# from app.services.rag_service import ask_policy

# case = TEST_CASES[0]

# result = ask_policy(
#     policy_id=case["policy_id"],
#     query=case["question"],
#     return_context=True
# )

# print("=" * 60)
# print("QUESTION:")
# print(case["question"])

# print("\nEXPECTED ANSWER:")
# print(case["expected_answer"])

# print("\nGENERATED ANSWER:")
# print(result["answer"])

# print("\nRETRIEVED CONTEXT:")

# for i, chunk in enumerate(result["context"], start=1):
#     print(f"\nChunk {i}:")
#     print(chunk)




#     from evaluation.test_cases import TEST_CASES
# from app.rag.policy_rag import ask_policy

# for idx, case in enumerate(TEST_CASES, start=1):

#     print("=" * 80)
#     print(f"TEST CASE {idx}")

#     result = ask_policy(
#         policy_id=case["policy_id"],
#         query=case["question"],
#         return_context=True
#     )

#     print("Question :", case["question"])
#     print("Expected :", case["expected_answer"])
#     print("Answer   :", result["answer"])
#     print("Chunks Retrieved :", len(result["context"]))