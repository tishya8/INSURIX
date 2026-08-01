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

