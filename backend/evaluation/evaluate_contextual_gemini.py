import time
import pandas as pd

from app.services.rag_service import ask_policy

from deepeval.metrics import ContextualRelevancyMetric
from deepeval.models import GeminiModel
from deepeval.test_case import LLMTestCase


# ==========================================================
# Configuration
# ==========================================================

# GEMINI_API_KEY = ""

MODEL_NAME = "gemini-flash-latest"

REQUEST_DELAY = 25      # seconds (≈2.4 RPM)

questions = [
    "Who is the policyholder?",
    "Is theft covered?",
    "What is the manufacturing year?"
]

# ==========================================================
# Gemini Judge
# ==========================================================

evaluation_model = GeminiModel(
    model=MODEL_NAME,
    api_key=GEMINI_API_KEY,
)

metric = ContextualRelevancyMetric(
    model=evaluation_model,
    include_reason=True,
)

results = []

# ==========================================================
# Evaluation
# ==========================================================

for i, question in enumerate(questions, start=1):

    print("\n" + "=" * 80)
    print(f"Question {i}/{len(questions)}")
    print("=" * 80)

    response = ask_policy(
        policy_id=1,
        query=question,
        return_context=True
    )

    test_case = LLMTestCase(
        input=question,
        retrieval_context=response["context"],
    )

    metric.measure(test_case)

    print("\nQuestion")
    print("-" * 40)
    print(question)

    print("\nRetrieved Chunks")
    print("-" * 40)

    for idx, chunk in enumerate(response["context"], start=1):
        print(f"\nChunk {idx}")
        print(chunk[:300])

    print("\nContextual Relevancy")
    print("-" * 40)
    print(metric.score)

    print("\nReason")
    print("-" * 40)
    print(metric.reason)

    results.append({
        "Question": question,
        "Contextual Relevancy": metric.score,
        "Reason": metric.reason,
    })

    if i != len(questions):
        print(f"\nWaiting {REQUEST_DELAY} seconds before next request...")
        time.sleep(REQUEST_DELAY)


# ==========================================================
# Save Results
# ==========================================================

df = pd.DataFrame(results)

df.to_csv(
    "evaluation/results/contextual_gemini_validation.csv",
    index=False
)

print("\nDone!")
print(df)