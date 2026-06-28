import json
import re
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5:1.5b", temperature=0)

# ---------------------------------------------------------------------------
# Valid incident types — single source of truth shared with main.py
# ---------------------------------------------------------------------------

VALID_INCIDENT_TYPES = {"THEFT", "ACCIDENT", "FLOOD", "FIRE", "OTHER"}

# ---------------------------------------------------------------------------
# Prompt
# FIX 3: Added FLOOD/FIRE/OTHER examples so planner stops returning UNKNOWN.
# FIX 4: Added negative examples so coverage questions don't trigger CREATE_CLAIM.
# FIX 5: Added rule that multiple coverage questions = one POLICY_QUERY, not split.
# ---------------------------------------------------------------------------

PLANNER_PROMPT = """
You are an Insurance Assistant Planner. Classify the user message into intents.

RULES:
- Return ONLY a JSON array. No explanation. No markdown. No code fences.
- Use ONLY these intents: POLICY_QUERY, CREATE_CLAIM, TRACK_CLAIM
- For CREATE_CLAIM, incident_type must be one of: THEFT, ACCIDENT, FLOOD, FIRE, OTHER
  If the message does not explicitly request creating/filing/submitting a claim, do NOT use CREATE_CLAIM.
- For TRACK_CLAIM, claim_id must be an integer extracted from the message.
- For POLICY_QUERY, combine all coverage/policy questions into ONE query string.
- If the message contains TRACK_CLAIM or POLICY_QUERY together with no explicit claim creation request, do NOT add CREATE_CLAIM.
- If incident type is unclear for CREATE_CLAIM, use "UNKNOWN" — never omit the intent.

EXAMPLES:

User: Is theft covered?
Output: [{{"intent":"POLICY_QUERY","query":"Is theft covered?"}}]

User: Does the policy cover flood damage and fire damage?
Output: [{{"intent":"POLICY_QUERY","query":"Does the policy cover flood damage and fire damage?"}}]

User: Track claim 5
Output: [{{"intent":"TRACK_CLAIM","claim_id":5}}]

User: Create a theft claim
Output: [{{"intent":"CREATE_CLAIM","incident_type":"THEFT"}}]

User: File a flood claim
Output: [{{"intent":"CREATE_CLAIM","incident_type":"FLOOD"}}]

User: I want to create a fire claim
Output: [{{"intent":"CREATE_CLAIM","incident_type":"FIRE"}}]

User: Create a claim
Output: [{{"intent":"CREATE_CLAIM","incident_type":"UNKNOWN"}}]

User: Track claim 2 and tell me whether engine damage is covered
Output: [{{"intent":"TRACK_CLAIM","claim_id":2}},{{"intent":"POLICY_QUERY","query":"Is engine damage covered?"}}]

User: Is theft covered and track claim 2
Output: [{{"intent":"POLICY_QUERY","query":"Is theft covered?"}},{{"intent":"TRACK_CLAIM","claim_id":2}}]

User: What documents are required for claim submission and track claim 1?
Output: [{{"intent":"POLICY_QUERY","query":"What documents are required for claim submission?"}},{{"intent":"TRACK_CLAIM","claim_id":1}}]

User: Create a claim and check if theft is covered
Output: [{{"intent":"CREATE_CLAIM","incident_type":"UNKNOWN"}},{{"intent":"POLICY_QUERY","query":"Is theft covered?"}}]

User: {question}
Output:
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_fences(raw: str) -> str:
    return re.sub(r"```(?:json)?", "", raw).strip()


def _safe_parse(raw: str) -> list:
    try:
        return json.loads(_strip_fences(raw))
    except json.JSONDecodeError as e:
        print(f"[planner] JSON parse error: {e}")
        print(f"[planner] Raw output: {raw!r}")
        return []


def _validate_plan(plan: list) -> list:
    """
    FIX 3+4: Post-process the plan to catch issues the LLM might still make.

    Rules applied:
    1. TRACK_CLAIM must have integer claim_id — drop if missing.
    2. CREATE_CLAIM incident_type must be in VALID_INCIDENT_TYPES or UNKNOWN.
    3. If plan has TRACK_CLAIM or POLICY_QUERY but NO explicit claim creation
       keyword in the original, strip rogue CREATE_CLAIM(UNKNOWN) entries
       that were hallucinated. (Handled by caller using raw question.)
    4. Deduplicate identical intents.
    """
    seen   = set()
    result = []

    for task in plan:
        intent = task.get("intent")

        if intent == "TRACK_CLAIM":
            cid = task.get("claim_id")
            if cid is None:
                continue  # malformed — skip
            task["claim_id"] = int(cid)

        if intent == "CREATE_CLAIM":
            itype = str(task.get("incident_type", "UNKNOWN")).upper()
            if itype not in VALID_INCIDENT_TYPES:
                itype = "UNKNOWN"
            task["incident_type"] = itype

        key = (intent, task.get("claim_id"), task.get("incident_type"))
        if key in seen:
            continue
        seen.add(key)
        result.append(task)

    return result


# Keywords that signal the user EXPLICITLY wants to create/file a claim
_CLAIM_CREATION_TRIGGERS = [
    "create", "file", "submit", "make", "open", "start", "raise", "log",
    "new claim", "a claim",
]


def _user_explicitly_wants_claim(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in _CLAIM_CREATION_TRIGGERS)


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------

def generate_plan(question: str) -> list:
    """
    Returns a validated list of task dicts each containing an 'intent' key.

    Possible shapes:
      {"intent": "POLICY_QUERY",  "query": "Is flood covered?"}
      {"intent": "TRACK_CLAIM",   "claim_id": 5}
      {"intent": "CREATE_CLAIM",  "incident_type": "THEFT"}

    Returns [] when the LLM fails or output is unparseable.
    """
    prompt = PLANNER_PROMPT.format(question=question)
    raw    = llm.invoke(prompt)

    print("\n[planner] RAW OUTPUT:")
    print(raw)

    plan = _safe_parse(raw)
    plan = _validate_plan(plan)

    # FIX 4 + 5: Remove hallucinated CREATE_CLAIM(UNKNOWN) when the user
    # never asked to create a claim. This fixes "What documents are required
    # and track claim 1" producing a spurious CREATE_CLAIM.
    if not _user_explicitly_wants_claim(question):
        plan = [t for t in plan if t.get("intent") != "CREATE_CLAIM"]

    print("\n[planner] VALIDATED PLAN:")
    print(plan)

    return plan