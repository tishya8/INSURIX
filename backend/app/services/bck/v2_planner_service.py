import json
import re
from langchain_ollama import OllamaLLM

# ---------------------------------------------------------------------------
# LLM setup
# ---------------------------------------------------------------------------

llm = OllamaLLM(
    model="qwen2.5:1.5b",
    temperature=0
)

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

PLANNER_PROMPT = """
You are an Insurance Assistant Planner.

Supported intents:

POLICY_QUERY
CREATE_CLAIM
TRACK_CLAIM

Return ONLY valid JSON — no explanation, no markdown, no code fences.

Examples:

User:
Is theft covered?
Output:
[{{"intent":"POLICY_QUERY","query":"Is theft covered?"}}]

User:
Track claim 5
Output:
[{{"intent":"TRACK_CLAIM","claim_id":5}}]

User:
Create a theft claim
Output:
[{{"intent":"CREATE_CLAIM","incident_type":"THEFT"}}]

User:
Create a claim and check if theft is covered
Output:
[
  {{"intent":"CREATE_CLAIM","incident_type":"THEFT"}},
  {{"intent":"POLICY_QUERY","query":"Is theft covered?"}}
]

User:
Track claim 2 and tell me whether engine damage is covered
Output:
[
  {{"intent":"TRACK_CLAIM","claim_id":2}},
  {{"intent":"POLICY_QUERY","query":"Is engine damage covered?"}}
]

User:
{question}
Output:
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(raw: str) -> str:
    """
    Strip markdown code fences if the LLM wraps its output in them.
    e.g.  ```json\n[...]\n```  →  [...]
    FIX: previously the parser crashed when LLM added code fences.
    """
    # remove ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    return cleaned


def _safe_parse(raw: str) -> list:
    """
    Try to parse JSON from raw LLM output.
    Returns empty list on failure instead of crashing.
    FIX: previously called json.loads on raw directly —
         now strips fences first so it handles more LLM outputs.
    """
    try:
        return json.loads(_extract_json(raw))
    except json.JSONDecodeError as e:
        print(f"[planner] JSON parse error: {e}")
        print(f"[planner] Raw output was: {raw!r}")
        return []

# ---------------------------------------------------------------------------
# Public API
# FIX: renamed generate_plan → create_plan to match how main.py imports it
# ---------------------------------------------------------------------------

def create_plan(question: str) -> list:
    """
    Returns a list of task dicts, each with an 'intent' key.
    Examples:
      [{"intent": "POLICY_QUERY", "query": "Is flood covered?"}]
      [{"intent": "TRACK_CLAIM",  "claim_id": 5}]
      [{"intent": "CREATE_CLAIM", "incident_type": "THEFT"}]
    Returns [] if LLM fails or output is unparseable.
    """
    prompt  = PLANNER_PROMPT.format(question=question)
    raw     = llm.invoke(prompt)

    print("\n[planner] RAW OUTPUT:")
    print(raw)

    plan = _safe_parse(raw)

    print("\n[planner] PARSED PLAN:")
    print(plan)

    return plan
