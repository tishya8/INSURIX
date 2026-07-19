import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

response = completion(
    model="groq/qwen/qwen3-32b",
    messages=[
        {"role": "user", "content": "What is AI?"}
    ],
    api_key=os.getenv("GROQ_API_KEY")
)

print(response.choices[0].message.content)

# import os
# from dotenv import load_dotenv
# import google.generativeai as genai

# # Load variables from .env
# load_dotenv()

# # Configure Gemini API
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# # Use the latest stable Flash model
# model = genai.GenerativeModel("gemini-flash-latest")

# # Test prompt
# response = model.generate_content(
#     "Say hello in one sentence."
# )

# print("\nGemini Response:")
# print(response.text)

