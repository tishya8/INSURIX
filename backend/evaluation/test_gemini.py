import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load variables from .env
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use the latest stable Flash model
model = genai.GenerativeModel("gemini-flash-latest")

# Test prompt
response = model.generate_content(
    "Say hello in one sentence."
)

print("\nGemini Response:")
print(response.text)

