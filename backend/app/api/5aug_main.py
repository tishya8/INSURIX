"""
INSURIX — FastAPI entry point

Changes from previous version
──────────────────────────────
A.  planner_service.py completely rewritten — rule-based, no LLM hallucination.
B.  handle_pending_state() now detects unrelated new intents while claim
    creation is in progress and auto-cancels the pending workflow before
    processing the new request (fixes Issue 6).
C.  State is always cleared on successful creation OR cancellation (was
    already correct; confirmed unchanged).
D.  execute_task() properly resets state so re-starting claim creation after
    a completed one always begins at WAITING_FOR_INCIDENT_TYPE (fixes Issue 1).
"""

import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.planner_service import generate_plan

from app.services.claim_service import (
    create_claim,
    get_claim_status,
    get_claim_status_for_policy,
    update_claim_status,
)
from app.services.rag_service import ask_policy

from app.services.policy_service import (
    get_user_policies,
    get_policy_document,
)

from app.services.session_service import conversation_state
from app.services.auth_service import login_user
from app.rag.policy_loader import build_full_vectorstore

# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI(title="INSURIX API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_build_chroma():
    import os
    chroma_dir = "./chroma_db"
    if os.path.exists(chroma_dir) and os.listdir(chroma_dir):
        print("[Startup] ChromaDB already exists — skipping rebuild.")
    else:
        print("[Startup] ChromaDB not found — building now…")
        # Pending below testing
        build_full_vectorstore() 
        print("[Startup] ChromaDB ready.")

# ── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/login")
def login(req: LoginRequest):
    result = login_user(req.email, req.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return result

# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    policy_id:  int
    question:   str
    session_id: str = "default_user"

# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

INCIDENT_KEYWORDS: dict[str, list[str]] = {
    "THEFT":    ["theft", "threft", "stolen", "steal", "robbery"],
    "ACCIDENT": ["accident", "crash", "crashed", "collision", "hit"],
    "FLOOD":    ["flood", "water damage", "rain"],
    "FIRE":     ["fire", "burn", "flame"],
    "OTHER":    ["other"],
}

CONFIRM_WORDS = {"yes", "y", "confirm"}
CANCEL_WORDS  = {"no",  "n", "cancel"}


def normalize_query(query: str) -> str:
    return query.strip().rstrip("?!.")


def detect_incident_type(text: str) -> str | None:
    lowered = text.lower()
    for incident_type, keywords in INCIDENT_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return incident_type
    return None


def format_claim(claim: dict) -> str:
    return (
        f"Claim ID: {claim['claim_id']}\n"
        f"Status: {claim['claim_status']}\n"
        f"Incident: {claim['incident_type']}\n"
        f"Description: {claim['description']}"
    )

# ---------------------------------------------------------------------------
# Accident guidance response builder
# ---------------------------------------------------------------------------

_ACCIDENT_SAFETY_STEPS = (
    "1. Move the vehicle off active traffic lanes if possible and switch on hazard lights.\n"
    "2. If anyone is injured, call 108 (Ambulance) or 112 (Emergency) before anything else.\n"
    "3. Photograph the damage, the other vehicle's plate (if any), and the scene.\n"
    "4. If there is third-party injury or property damage, file a police GD/FIR.\n"
    "5. Do not attempt repairs yourself — hand the vehicle over at an authorized garage."
)

_ACCIDENT_BENEFITS_FALLBACK = (
    "- Emergency flatbed towing is generally available for accident-damaged vehicles.\n"
    "- A courtesy replacement car may be provided if repairs take longer than a few days.\n"
    "- A compulsory deductible applies to each Own Damage claim — check your policy schedule for the exact amount."
)

# The RAG prompt (rag_service.py) instructs the LLM to emit this exact
# sentence when it can't answer. On multi-part questions the model may
# answer some parts and still append this phrase for the part it couldn't
# find — so we can't treat "phrase present anywhere" as "response useless".
# Instead: strip the phrase out and check how much real content is left.
_NO_INFO_PHRASE = re.compile(
    r"i\s+could\s+not\s+find\s+this\s+information\s+in\s+the\s+policy\.?",
    re.IGNORECASE,
)
_MIN_MEANINGFUL_CHARS = 15  # residual shorter than this ⇒ treat as no real answer


def _has_meaningful_content(benefits: str | None) -> bool:
    """True if `benefits` contains real information beyond the
    'could not find' boilerplate (which may appear alongside real answers
    for other parts of a multi-topic question)."""
    if not benefits or not benefits.strip():
        return False
    residual = _NO_INFO_PHRASE.sub("", benefits).strip(" .,\n-")
    return len(residual) >= _MIN_MEANINGFUL_CHARS


def build_accident_guidance(policy_id: int) -> str:
    """
    Structured first-response for a reported accident:
    empathetic opening + static safety checklist + one RAG lookup for
    policy-specific benefits (towing / courtesy car / deductible) + CTA.
    Falls back to generic benefit text if the RAG call fails or finds nothing,
    so this never breaks the demo even if the vector store / LLM hiccups.
    """
    try:
        benefits = ask_policy(
            policy_id,
            "What towing assistance, courtesy replacement car, and deductible apply "
            "for an accidental damage claim?",
        )
    except Exception as e:
        print(f"[accident_guidance] RAG lookup failed: {e}")
        benefits = None

    if not _has_meaningful_content(benefits):
        benefits = _ACCIDENT_BENEFITS_FALLBACK

    return (
        "I'm sorry to hear you've been in an accident — let's get you and your vehicle sorted out.\n\n"
        "Immediate steps:\n"
        f"{_ACCIDENT_SAFETY_STEPS}\n\n"
        "Your policy benefits that may apply:\n"
        f"{benefits}\n\n"
        "Need help right now?\n"
        "Call the INSURIX 24/7 Emergency Helpline or message the WhatsApp Assistance Bot to dispatch towing.\n\n"
        "Would you like to create a claim for this accident?\n"
        "Type 'Create a claim' to begin your claim."
    )

# ---------------------------------------------------------------------------
# Core task executor
# ---------------------------------------------------------------------------

def execute_task(
    task:       dict,
    policy_id:  int,
    session_id: str,
    question:   str,
) -> str:
    intent = task.get("intent")

    # ── ACCIDENT GUIDANCE ────────────────────────────────────────────────
    if intent == "ACCIDENT_GUIDANCE":
        # Hint the incident type for a subsequent "create a claim" message,
        # without starting the actual claim workflow yet (user hasn't
        # confirmed they want to file one). handle_pending_state ignores
        # this dict since it has no "action" key.
        conversation_state[session_id] = {"hint_incident_type": "ACCIDENT"}
        return build_accident_guidance(policy_id)

    # ── POLICY QUERY ─────────────────────────────────────────────────────
    if intent == "POLICY_QUERY":
        query  = task.get("query", question)
        answer = ask_policy(policy_id, normalize_query(query))
        return f"Policy Answer:\n\n{answer}"

    # ── TRACK CLAIM ──────────────────────────────────────────────────────
    if intent == "TRACK_CLAIM":
        claim_id = task.get("claim_id")
        if claim_id is None:
            match = re.search(r"\d+", question)
            if match:
                claim_id = int(match.group())
        if claim_id is None:
            return "Please provide a valid claim ID."
        claim = get_claim_status_for_policy(int(claim_id), policy_id)
        if claim:
            return f"Claim Details:\n\n{format_claim(claim)}"
        return (
            f"No claim with ID {claim_id} was found for the selected policy.\n"
            f"Please select the correct policy or provide a valid claim ID."
        )

    # ── CREATE CLAIM ─────────────────────────────────────────────────────
    if intent == "CREATE_CLAIM":
        # Always clear any stale state before starting fresh (fixes Issue 1).
        # Capture it first so a prior ACCIDENT_GUIDANCE hint isn't lost.
        prior_state = conversation_state.pop(session_id, None)
        hinted_incident_type = (
            prior_state.get("hint_incident_type") if prior_state else None
        )

        incident_type = (
            task.get("incident_type")
            or detect_incident_type(question)
            or hinted_incident_type
        )

        # If the planner returned "UNKNOWN" treat it the same as missing
        if incident_type and incident_type != "UNKNOWN":
            conversation_state[session_id] = {
                "action":        "CREATE_CLAIM",
                "step":          "WAITING_FOR_DESCRIPTION",
                "incident_type": incident_type,
            }
            return (
                f"Claim creation started.\n\n"
                f"Incident Type: {incident_type}\n\n"
                f"Please provide a brief description of the incident."
            )

        conversation_state[session_id] = {
            "action": "CREATE_CLAIM",
            "step":   "WAITING_FOR_INCIDENT_TYPE",
        }
        return (
            "Please select the incident type:\n\n"
            "1. Theft\n"
            "2. Accident\n"
            "3. Flood\n"
            "4. Fire\n"
            "5. Other\n\n"
            "Reply with the incident type."
        )

    # ── UNKNOWN ──────────────────────────────────────────────────────────
    return (
        "I could not understand your request.\n\n"
        "You can:\n"
        "• Ask policy questions\n"
        "• Create a claim\n"
        "• Track claim status"
    )

# ---------------------------------------------------------------------------
# Multi-turn conversation state handler
# ---------------------------------------------------------------------------

def _looks_like_new_intent(question: str) -> bool:
    """
    Heuristic: does this message look like a completely new request
    rather than a step in the claim-creation workflow?
    Returns True if the planner would produce at least one intent.
    We check here without calling generate_plan to avoid recursion.
    """
    lo = question.lower().strip()

    # Explicit track-claim mention
    if re.search(r"\bclaim\s*\d+\b|\btrack\b|\bcheck\s+claim\b", lo):
        return True

    # Explicit create-claim mention (different from yes/no/description)
    create_verbs = r"\b(create|raise|file|submit|open|log|start|report)\b"
    if re.search(create_verbs, lo) and re.search(r"\bclaim\b", lo):
        return True

    # Policy question signals
    policy_signals = r"\b(cover(ed|age)?|deductible|premium|waiting|document|policy)\b"
    question_words = r"^(what|does|is|are|can|how|which|when)"
    if re.search(policy_signals, lo) or re.search(question_words, lo):
        return True

    return False


def handle_pending_state(
    session_id: str,
    policy_id:  int,
    question:   str,
) -> str | None:
    """
    Handle a step in an in-progress claim creation workflow.

    if the user sends an unrelated request while claim
    creation is pending, the workflow is automatically cancelled and the
    new request is processed normally (returns None so the main handler
    takes over).
    """
    if session_id not in conversation_state:
        return None

    pending = conversation_state[session_id]

    if pending.get("action") != "CREATE_CLAIM":
        return None

    step = pending.get("step")
    answer_lo = question.strip().lower()

    # ── Step 1 — waiting for incident type ───────────────────────────────
    if step == "WAITING_FOR_INCIDENT_TYPE":
        # Unrelated new intent → cancel and let main handler process
        if _looks_like_new_intent(question):
            del conversation_state[session_id]
            return None  # fall through to main handler

        incident_type = detect_incident_type(question)
        if incident_type:
            conversation_state[session_id] = {
                "action":        "CREATE_CLAIM",
                "step":          "WAITING_FOR_DESCRIPTION",
                "incident_type": incident_type,
            }
            return "Please provide a brief description of the incident."

        return (
            "Please select a valid incident type:\n\n"
            "1. Theft\n2. Accident\n3. Flood\n4. Fire\n5. Other\n\n"
            "Reply with the incident type."
        )

    # ── Step 2 — waiting for description ─────────────────────────────────
    if step == "WAITING_FOR_DESCRIPTION":
        # Unrelated new intent → cancel and let main handler process
        if _looks_like_new_intent(question):
            del conversation_state[session_id]
            return None

        conversation_state[session_id] = {
            "action":        "CREATE_CLAIM",
            "step":          "WAITING_FOR_CONFIRMATION",
            "incident_type": pending["incident_type"],
            "description":   question,
        }
        return (
            f"Please confirm:\n\n"
            f"Incident Type: {pending['incident_type']}\n"
            f"Description: {question}\n\n"
            f"Reply YES to create the claim or NO to cancel."
        )

    # ── Step 3 — waiting for YES / NO ────────────────────────────────────
    if step == "WAITING_FOR_CONFIRMATION":
        if answer_lo in CONFIRM_WORDS:
            claim_id = create_claim(
                policy_id,
                pending["incident_type"],
                pending["description"],
            )
            del conversation_state[session_id]
            return (
                f"Claim created successfully.\n\n"
                f"Claim ID: {claim_id}\n"
                f"Status: SUBMITTED\n"
                f"Incident Type: {pending['incident_type']}\n"
                f"Description: {pending['description']}"
            )

        if answer_lo in CANCEL_WORDS:
            del conversation_state[session_id]
            return (
                "Claim creation cancelled.\n\n"
                "You can start again by saying: create a claim."
            )

        # Unrelated request while awaiting confirmation → cancel workflow
        if _looks_like_new_intent(question):
            del conversation_state[session_id]
            return None  # fall through to main handler

        return (
            "I did not understand.\n\n"
            "Please reply YES to create the claim or NO to cancel."
        )

    return None

# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "INSURIX API Running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/users/{user_id}/policies")
def fetch_user_policies(user_id: int):
    return get_user_policies(user_id)


@app.get("/policies/{policy_id}/document")
def get_document(policy_id: int):
    document = get_policy_document(policy_id)
    if document is None:
        return {"message": "Policy document not found"}
    return document


@app.post("/claims")
def create_new_claim(policy_id: int, incident_type: str, description: str):
    claim_id = create_claim(policy_id, incident_type, description)
    return {"claim_id": claim_id, "status": "SUBMITTED"}


@app.get("/claims/{claim_id}")
def fetch_claim_status(claim_id: int):
    return get_claim_status(claim_id)


@app.put("/claims/{claim_id}/status")
def update_status(claim_id: int, status: str):
    update_claim_status(claim_id, status)
    return {
        "message":  "Claim status updated",
        "claim_id": claim_id,
        "status":   status,
    }

# ---------------------------------------------------------------------------
# Main chat endpoint
# ---------------------------------------------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):
    policy_id  = request.policy_id
    question   = request.question.strip()
    session_id = request.session_id

    # 1. Resume multi-turn conversation if one is in progress.
    #    Returns None if the user sent an unrelated request → fall through.
    pending_response = handle_pending_state(session_id, policy_id, question)
    if pending_response is not None:
        return {"answer": pending_response}

    # 2. Generate execution plan
    plan = generate_plan(question)
    print(f"\n[chat] PLAN: {plan}")

    # 3. Handle empty plan
    if not plan:
        return {
            "answer": (
                "I could not understand your request.\n\n"
                "Currently I can help with:\n\n"
                "• Policy coverage questions\n"
                "• Claim creation\n"
                "• Claim status tracking\n\n"
                "Examples:\n"
                "• Is theft covered?\n"
                "• Create a theft claim\n"
                "• Track claim 7"
            )
        }

    # 4. Execute plan — single or multi-intent
    if len(plan) == 1:
        answer = execute_task(plan[0], policy_id, session_id, question)
        return {"answer": answer}

    responses = [
        execute_task(task, policy_id, session_id, question)
        for task in plan
    ]
    return {"answer": "\n\n---\n\n".join(responses)}