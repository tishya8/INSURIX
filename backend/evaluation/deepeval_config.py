import os
from dotenv import load_dotenv

from deepeval.models import GeminiModel, OllamaModel, LiteLLMModel

load_dotenv()

EVALUATOR = os.getenv("EVALUATOR", "ollama").lower()

# -------------------------------------------------------
# Metric Configuration
# -------------------------------------------------------

ENABLE_FAITHFULNESS = (
    os.getenv("ENABLE_FAITHFULNESS", "true").lower() == "true"
)

ENABLE_ANSWER_RELEVANCY = (
    os.getenv("ENABLE_ANSWER_RELEVANCY", "false").lower() == "true"
)

ENABLE_CONTEXTUAL_RELEVANCY = (
    os.getenv("ENABLE_CONTEXTUAL_RELEVANCY", "false").lower() == "true"
)

if EVALUATOR == "gemini":

    MODEL_NAME = "gemini-flash-latest"

    evaluation_model = GeminiModel(
        model=MODEL_NAME,
        api_key=os.getenv("GEMINI_API_KEY")
    )

elif EVALUATOR == "groq":

    MODEL_NAME = "groq/qwen/qwen3-32b"

    evaluation_model = LiteLLMModel(
        model=MODEL_NAME,
        api_key=os.getenv("GROQ_API_KEY")
    )

elif EVALUATOR == "ollama":

    MODEL_NAME = "qwen2.5:3b"

    evaluation_model = OllamaModel(
        model=MODEL_NAME
    )

else:
    raise ValueError(f"Unsupported evaluator: {EVALUATOR}")

# ------------------------------------------
# Print the evaluator being used
# ------------------------------------------

print("\n" + "=" * 60)
print(f"Evaluation Backend : {EVALUATOR}")
print(f"Evaluation Model   : {MODEL_NAME}")
print("=" * 60)

# import os
# from dotenv import load_dotenv

# from deepeval.models import GeminiModel

# load_dotenv()

# evaluation_model = GeminiModel(
#     model="gemini-flash-latest",
#     api_key=os.getenv("GEMINI_API_KEY")
# )