from langchain_ollama import OllamaLLM
import json

llm = OllamaLLM(
    model="qwen2.5:1.5b",
    temperature=0
)


def generate_plan(question):

    prompt = f"""
You are an Insurance Assistant Planner.

Supported intents:

POLICY_QUERY
CREATE_CLAIM
TRACK_CLAIM

Return ONLY valid JSON.

Examples:

User:
Is theft covered?

Output:
[
  {{
    "intent":"POLICY_QUERY",
    "query":"Is theft covered?"
  }}
]


User:
Track claim 5

Output:
[
  {{
    "intent":"TRACK_CLAIM",
    "claim_id":5
  }}
]


User:
Create a theft claim

Output:
[
  {{
    "intent":"CREATE_CLAIM",
    "incident_type":"THEFT"
  }}
]


User:
Create a claim and check if theft is covered

Output:
[
  {{
    "intent":"CREATE_CLAIM",
    "incident_type":"THEFT"
  }},
  {{
    "intent":"POLICY_QUERY",
    "query":"Is theft covered?"
  }}
]


User:
Track claim 2 and tell me whether engine damage is covered

Output:
[
  {{
    "intent":"TRACK_CLAIM",
    "claim_id":2
  }},
  {{
    "intent":"POLICY_QUERY",
    "query":"Is engine damage covered?"
  }}
]


User:
{question}

Output:
"""

    response = llm.invoke(prompt)

    print("\nRAW PLAN:")
    print(response)

    try:

        return json.loads(response)

    except Exception as e:

        print("Planner Error:", e)

        return []