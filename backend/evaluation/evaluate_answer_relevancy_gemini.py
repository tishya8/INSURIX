import os
import time
import pandas as pd

from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval.models import GeminiModel, OllamaModel

from app.services.rag_service import ask_policy

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

GEMINI_API_KEY = "GEMINI_API_KEY"

# MODEL_NAME = "gemini-flash-latest"
MODEL_NAME = "qwen2.5:3b"

OUTPUT_FILE = "evaluation/results/answerRelavancy_ollama_validation.csv"

# evaluation_model = GeminiModel(
#     model=MODEL_NAME,
#     api_key=GEMINI_API_KEY,
# )

evaluation_model = OllamaModel(
    model=MODEL_NAME
)

metric = AnswerRelevancyMetric(
    model=evaluation_model,
    include_reason=True
)

# -------------------------------------------------------
# Test Questions
# -------------------------------------------------------

questions = [
    {
        "question": "What is the fuel type?",
        "expected": "Petrol"
    }
]

results = []

# -------------------------------------------------------
# Evaluation
# -------------------------------------------------------

for i, q in enumerate(questions, start=1):

    print("=" * 80)
    print(f"Running Question {i}")
    print("=" * 80)

    response = ask_policy(
        policy_id=1,
        query=q["question"],
        return_context=True
    )

    test_case = LLMTestCase(
        input=q["question"],
        actual_output=response["answer"],
        expected_output=q["expected"],
        retrieval_context=response["context"]
    )

    metric.measure(test_case)

    print("\nQuestion")
    print(q["question"])

    print("\nExpected")
    print(q["expected"])

    print("\nGenerated")
    print(response["answer"])

    print("\nScore")
    print(metric.score)

    print("\nReason")
    print(metric.reason)

    results.append({
        "Question": q["question"],
        "Expected Answer": q["expected"],
        "Generated Answer": response["answer"],
        "Answer Relevancy": metric.score,
        "Reason": metric.reason
    })

    # Stay below Gemini free-tier RPM
    if i < len(questions):
        print("\nWaiting 20 seconds to avoid RPM limit...\n")
        time.sleep(20)

# -------------------------------------------------------
# Save CSV
# -------------------------------------------------------

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 80)
print("Evaluation Complete")
print("=" * 80)

print(f"Results saved to: {OUTPUT_FILE}")

print("\nAverage Answer Relevancy")
print("-" * 40)
print(f"{results_df['Answer Relevancy'].mean():.2f}")