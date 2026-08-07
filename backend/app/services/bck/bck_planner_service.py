"""
planner_service.py — Intent planner for INSURIX chatbot.

Architecture
────────────
1.  Rule-based parser (fast, deterministic, no hallucination).
    Handles >95 % of real traffic reliably.
2.  LLM fallback for genuinely ambiguous messages.

Supported intents
──────────────────
  POLICY_QUERY  — {intent, query}
  TRACK_CLAIM   — {intent, claim_id}          # one per claim ID
  CREATE_CLAIM  — {intent, incident_type}      # only when user EXPLICITLY asks

Key invariants
──────────────
• CREATE_CLAIM is NEVER emitted unless the user explicitly uses a
  creation verb ("create", "raise", "file", "submit", "open", "log",
  "start", "report").
• Multiple claim IDs produce one TRACK_CLAIM per ID.
• Multiple policy questions produce one POLICY_QUERY per question.
• No duplicate intents for identical (intent, key) pairs.
"""

import json
import re
from typing import Optional

# ── Optional LLM (used as fallback only) ─────────────────────────────────────
try:
    from langchain_ollama import OllamaLLM
    _llm = OllamaLLM(model="qwen2.5:1.5b", temperature=0)
    _LLM_AVAILABLE = True
except Exception:
    _llm = None
    _LLM_AVAILABLE = False

# ── Constants ─────────────────────────────────────────────────────────────────

# Verbs that signal the user WANTS to create a new claim.
# We require these to be present to emit CREATE_CLAIM.
_CREATE_VERBS = re.compile(
    r"\b(create|raise|file|submit|open|log|start|report|initiate|make)\b"
    r"(?!\s+a?\s*claim\s+\d)",       # exclude "create claim 5" = track
    re.IGNORECASE,
)

# "a claim" / "claim" preceded by a create verb — the actual claim noun
_CLAIM_NOUN = re.compile(r"\b(a\s+)?claim\b", re.IGNORECASE)

# Track-claim patterns — extract every numeric claim ID mentioned
_TRACK_PATTERNS = [
    # "track claim 3", "check claim 5", "status of claim 7"
    re.compile(
        r"\b(?:track|check|status\s+of|show|get|view|find|look\s+up)"
        r"\s+(?:claim|claims)?\s*(\d+)\b",
        re.IGNORECASE,
    ),
    # "claim 3 and claim 5" — bare "claim N" references (after filtering
    # create verbs and coverage questions)
    re.compile(r"\bclaim[s]?\s+(\d+)\b", re.IGNORECASE),
    # "claims 3, 5 and 7"
    re.compile(r"\bclaims?\s+([\d]+(?:\s*[,&]\s*[\d]+)*(?:\s+and\s+[\d]+)?)\b", re.IGNORECASE),
]

# Incident types for CREATE_CLAIM
_INCIDENT_KEYWORDS: dict[str, list[str]] = {
    "THEFT":    ["theft", "stolen", "steal", "robbery", "threft"],
    "ACCIDENT": ["accident", "crash", "crashed", "collision", "hit"],
    "FLOOD":    ["flood", "water damage", "rain"],
    "FIRE":     ["fire", "burn", "flame"],
    "OTHER":    ["other"],
}

# Policy / coverage question signals
_POLICY_SIGNALS = re.compile(
    r"\b(cover(?:ed|age|s)?|policy|deductible|premium|waiting\s+period"
    r"|document[s]?|claim\s+process|what\s+is|does\s+(my|the)\s+policy"
    r"|is\s+.+\s+covered|how\s+(much|long)|eligible|exclusion[s]?"
    r"|benefit[s]?|include[s]?)\b",
    re.IGNORECASE,
)

# Question words that strongly suggest a policy question
_QUESTION_WORDS = re.compile(
    r"\b(what|does|is|are|can|how|which|when|why)\b",
    re.IGNORECASE,
)

# Words that split a single message into multiple sub-questions
_SPLITTERS = re.compile(r"\b(and|also|as\s+well(?:\s+as)?|additionally|plus)\b", re.IGNORECASE)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_incident_type(text: str) -> Optional[str]:
    lo = text.lower()
    for itype, kws in _INCIDENT_KEYWORDS.items():
        if any(kw in lo for kw in kws):
            return itype
    return None


def _extract_all_claim_ids(text: str) -> list[int]:
    """Return every unique claim ID found in text, in order of appearance."""
    ids: list[int] = []
    seen: set[int] = set()

    # First look for "claims 3, 5 and 7" style
    multi = re.findall(r"\bclaims?\s+([\d]+(?:\s*[,&]\s*[\d]+)*(?:\s+and\s+[\d]+)?)\b", text, re.IGNORECASE)
    for group in multi:
        for n in re.findall(r"\d+", group):
            cid = int(n)
            if cid not in seen:
                seen.add(cid)
                ids.append(cid)

    # Then individual "claim N"
    for m in re.finditer(r"\bclaim[s]?\s+(\d+)\b", text, re.IGNORECASE):
        cid = int(m.group(1))
        if cid not in seen:
            seen.add(cid)
            ids.append(cid)

    return ids


def _has_create_intent(text: str) -> bool:
    """
    Return True ONLY if the user explicitly asks to create / raise / file a claim.
    Requires a creation verb AND the word 'claim'.
    """
    if not _CREATE_VERBS.search(text):
        return False
    if not _CLAIM_NOUN.search(text):
        return False
    return True


def _has_track_intent(text: str) -> bool:
    """Return True if any claim ID can be extracted."""
    return bool(_extract_all_claim_ids(text))


def _looks_like_policy_question(segment: str) -> bool:
    """
    Heuristic: does this segment ask about policy coverage / details?
    True if it contains a question word or a policy signal keyword.
    """
    return bool(_POLICY_SIGNALS.search(segment) or _QUESTION_WORDS.search(segment))


def _split_policy_questions(text: str) -> list[str]:
    """
    Split a message into individual policy sub-questions.

    Examples handled:
      "Is theft covered and what is the deductible?"
        → ["Is theft covered", "what is the deductible?"]
      "Does the policy cover flood damage and fire damage?"
        → ["Does the policy cover flood damage?",
           "Does the policy cover fire damage?"]

    Strategy
    ────────
    1. Remove track-claim and create-claim fragments.
    2. Try to detect the "Does X cover A and B?" pattern and expand it.
    3. Split on conjunctions.
    4. Keep only segments that look like policy questions.
    """
    # Remove "track claim N" fragments
    cleaned = re.sub(
        r"\b(?:track|check|status\s+of|show|get|view|find|look\s+up)"
        r"\s+(?:claim|claims?)?\s*\d+\b",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Remove "claim N" references that remain
    cleaned = re.sub(r"\bclaims?\s+\d+\b", "", cleaned, flags=re.IGNORECASE)
    # Remove create-claim fragments
    if _has_create_intent(cleaned):
        cleaned = re.sub(
            r"\b(?:create|raise|file|submit|open|log|start|report|initiate|make)\b"
            r"(?:\s+a)?\s+(?:claim|new\s+claim)\b[^.?!]*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

    cleaned = cleaned.strip().strip(",").strip()

    if not cleaned:
        return []

    # ── Expand "Does X cover [A] and [B]?" into two questions ────────────
    # Pattern: <question-prefix> cover <topic1> and <topic2>
    # where topic2 looks like a continuation (no verb of its own)
    cover_expand = re.match(
        r"^((?:does|is|are|can|will)\s+.{0,30}?\s+cover(?:ed|s)?)\s+"
        r"(.+?)\s+and\s+(.+?)\??$",
        cleaned.rstrip("?"),
        re.IGNORECASE,
    )
    if cover_expand:
        prefix = cover_expand.group(1)
        topic_a = cover_expand.group(2).strip()
        topic_b = cover_expand.group(3).strip()
        # Only expand if topic_b has no verb (it's a bare noun/phrase, not
        # a full sub-question like "what is the deductible")
        if not re.search(r"\b(is|are|does|what|how|when|which|can)\b", topic_b, re.IGNORECASE):
            return [
                f"{prefix} {topic_a}?",
                f"{prefix} {topic_b}?",
            ]

    # ── General split on "and", "also", etc. ─────────────────────────────
    parts = _SPLITTERS.split(cleaned)
    questions: list[str] = []
    seen_q: set[str] = set()

    for part in parts:
        part = part.strip().strip(",").strip()
        if not part:
            continue
        if not _looks_like_policy_question(part):
            continue
        normed = " ".join(part.split())
        if normed.lower() in seen_q:
            continue
        seen_q.add(normed.lower())
        questions.append(normed)

    return questions


# ── LLM fallback prompt ───────────────────────────────────────────────────────

_LLM_PROMPT = """\
You are an insurance assistant intent planner. Return ONLY valid JSON — no explanation, no markdown, no code fences.

RULES (non-negotiable):
1. Only emit CREATE_CLAIM if the user explicitly uses a creation verb: create, raise, file, submit, open, log, start, report.
2. Never emit CREATE_CLAIM for policy coverage questions like "Is X covered?" or "Does the policy cover X?".
3. Emit one TRACK_CLAIM per claim ID.
4. Emit one POLICY_QUERY per distinct question.
5. Never invent intents the user did not express.

Intents: POLICY_QUERY, CREATE_CLAIM, TRACK_CLAIM

Examples:
User: Is theft covered?
Output: [{{"intent":"POLICY_QUERY","query":"Is theft covered?"}}]

User: Track claim 5
Output: [{{"intent":"TRACK_CLAIM","claim_id":5}}]

User: Create a theft claim
Output: [{{"intent":"CREATE_CLAIM","incident_type":"THEFT"}}]

User: Is theft covered and track claim 2
Output: [{{"intent":"POLICY_QUERY","query":"Is theft covered?"}},{{"intent":"TRACK_CLAIM","claim_id":2}}]

User: Does the policy cover flood damage and fire damage?
Output: [{{"intent":"POLICY_QUERY","query":"Does the policy cover flood damage?"}},{{"intent":"POLICY_QUERY","query":"Does the policy cover fire damage?"}}]

User: Track claim 1 and claim 2
Output: [{{"intent":"TRACK_CLAIM","claim_id":1}},{{"intent":"TRACK_CLAIM","claim_id":2}}]

User: What documents are required for claim submission and track claim 1?
Output: [{{"intent":"POLICY_QUERY","query":"What documents are required for claim submission?"}},{{"intent":"TRACK_CLAIM","claim_id":1}}]

User: {question}
Output:"""


def _llm_fallback(question: str) -> list:
    if not _LLM_AVAILABLE or _llm is None:
        return []
    try:
        raw = _llm.invoke(_LLM_PROMPT.format(question=question))
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[planner] LLM fallback error: {e}")
        return []


# ── Rule-based core ───────────────────────────────────────────────────────────

def _rule_based_plan(question: str) -> list:
    """
    Pure rule-based planner. Never hallucinates. Returns [] only when the
    input is genuinely unrecognised.
    """
    plan: list[dict] = []

    # ── 1. TRACK_CLAIM — one intent per claim ID ──────────────────────────
    claim_ids = _extract_all_claim_ids(question)
    for cid in claim_ids:
        plan.append({"intent": "TRACK_CLAIM", "claim_id": cid})

    # ── 2. CREATE_CLAIM — only on explicit create verb ────────────────────
    if _has_create_intent(question):
        incident_type = _detect_incident_type(question) or "UNKNOWN"
        plan.append({"intent": "CREATE_CLAIM", "incident_type": incident_type})

    # ── 3. POLICY_QUERY — one intent per sub-question ────────────────────
    policy_questions = _split_policy_questions(question)
    for q in policy_questions:
        plan.append({"intent": "POLICY_QUERY", "query": q})

    return plan


# ── Public API ────────────────────────────────────────────────────────────────

def generate_plan(question: str) -> list:
    """
    Returns a list of task dicts with an 'intent' key.

    Possible shapes:
      {"intent": "POLICY_QUERY",  "query": "Is flood covered?"}
      {"intent": "TRACK_CLAIM",   "claim_id": 5}
      {"intent": "CREATE_CLAIM",  "incident_type": "THEFT"}

    Returns [] when the input is unrecognised.
    """
    plan = _rule_based_plan(question)

    if not plan and _LLM_AVAILABLE:
        print("[planner] Rule-based returned empty — trying LLM fallback")
        plan = _llm_fallback(question)

    print(f"\n[planner] PLAN: {plan}")
    return plan