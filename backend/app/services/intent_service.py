from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="qwen2.5:1.5b",
    temperature=0
)

def detect_intent(query):

    prompt = f"""
Classify the user's intent.

Possible intents:

POLICY_QUERY
CREATE_CLAIM
TRACK_CLAIM

Examples:

User: What is the deductible amount?
Intent: POLICY_QUERY

User: Is engine damage covered?
Intent: POLICY_QUERY

User: My bike was stolen yesterday.
Intent: CREATE_CLAIM

User: I want to raise a claim.
Intent: CREATE_CLAIM

User: What is my claim status?
Intent: TRACK_CLAIM

User: Track claim 101.
Intent: TRACK_CLAIM

User:
{query}

Return ONLY the intent.
"""

    response = llm.invoke(prompt)

    return response.strip()