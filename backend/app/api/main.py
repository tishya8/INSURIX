"""
INSURIX — FastAPI entry point (refactored)

Summary of all changes from original main.py
─────────────────────────────────────────────
1.  Removed 1600+ lines of commented-out dead code (3 old versions of /ask-policy).
2.  Removed duplicate import of get_user_policies (was imported from both
    claim_service and policy_service — now only policy_service).
3.  Moved `import re` to top level (was re-imported inside 3 functions).
4.  Extracted detect_incident_type() to module level (was an inner function
    inside /ask-policy, could not be reused anywhere else).
5.  Extracted format_claim() — identical f-string was copy-pasted 4 times.
6.  Extracted execute_task() — the POLICY_QUERY / CREATE_CLAIM / TRACK_CLAIM
    if/elif blocks were copy-pasted identically for single-intent and
    multi-intent paths. Now both paths call the same function.
7.  Fixed TRACK_CLAIM in multi-intent: was reading task["query"] which does
    not exist — planner puts the id in task["claim_id"]. Now reads
    task["claim_id"] first, falls back to regex on question text.
8.  Added Pydantic model (ChatRequest) — /ask-policy was raw dict with no
    validation. Renamed endpoint to /chat to match the model name.
9.  Confirmation now accepts "yes", "y", "confirm" (single-intent path
    only accepted "yes" — the commented code had all three, restored here).
10. Added fallback response when plan == [] so the endpoint never crashes
    with IndexError on plan[0].
"""

import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.planner_service import generate_plan

from app.services.claim_service import (
    create_claim,
    get_claim_status,
    update_claim_status,
)
from app.services.rag_service import ask_policy

# FIX 2: was imported from claim_service AND policy_service — one source only
from app.services.policy_service import (
    get_user_policies,
    get_policy_document,
)

from app.services.session_service import conversation_state
from app.services.auth_service import login_user

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

# ── Auth ─────────────────────────────────────────────────────────────────────
 
class LoginRequest(BaseModel):
    email: str
    password: str
 
 
@app.post("/login")
def login(req: LoginRequest):
    result = login_user(req.email, req.password)
    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    return result

# ---------------------------------------------------------------------------
# Request model
# FIX 8: was raw dict — Pydantic gives validation + Swagger docs for free
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    policy_id:  int
    question:   str
    session_id: str = "default_user"

# ---------------------------------------------------------------------------
# Module-level helpers
# FIX 4: detect_incident_type was an inner function — moved here so all
#        paths (single, multi, pending) can call the same implementation.
# FIX 5: format_claim was an inline f-string copy-pasted 4 times.
# ---------------------------------------------------------------------------

# Richer keyword map (restored from commented-out version)
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
    """Strip trailing punctuation."""
    return query.strip().rstrip("?!.")


def detect_incident_type(text: str) -> str | None:
    """
    Return the first matching incident type found in text, or None.
    FIX 4: was redefined as an inner function inside /ask-policy on every
    request. Now defined once at module level and shared everywhere.
    """
    lowered = text.lower()
    for incident_type, keywords in INCIDENT_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return incident_type
    return None


def format_claim(claim: dict) -> str:
    """
    Render a claim dict as a readable string.
    FIX 5: identical f-string was copy-pasted in 4 places.
    """
    return (
        f"Claim ID: {claim['claim_id']}\n"
        f"Status: {claim['claim_status']}\n"
        f"Incident: {claim['incident_type']}\n"
        f"Description: {claim['description']}"
    )

# ---------------------------------------------------------------------------
# Core task executor
# FIX 6: single-intent and multi-intent paths had identical if/elif blocks.
#        Both now call execute_task() — one place to fix bugs.
# ---------------------------------------------------------------------------

def execute_task(
    task:       dict,
    policy_id:  int,
    session_id: str,
    question:   str,
) -> str:
    """
    Execute one plan task and return a plain-text response string.

    task shapes from planner:
      {"intent": "POLICY_QUERY",  "query": "Is flood covered?"}
      {"intent": "TRACK_CLAIM",   "claim_id": 5}
      {"intent": "CREATE_CLAIM",  "incident_type": "THEFT"}
    """
    intent = task.get("intent")

    # -----------------------------------------------------------------------
    # POLICY QUERY — RAG pipeline
    # -----------------------------------------------------------------------
    if intent == "POLICY_QUERY":
        query  = task.get("query", question)
        answer = ask_policy(policy_id, normalize_query(query))
        return f"Policy Answer:\n\n{answer}"

    # -----------------------------------------------------------------------
    # TRACK CLAIM
    # FIX 7: multi-intent path read task["query"] which does not exist on
    #        TRACK_CLAIM tasks — planner puts the id in task["claim_id"].
    #        Now reads task["claim_id"] first, falls back to regex.
    # -----------------------------------------------------------------------
    if intent == "TRACK_CLAIM":
        claim_id = task.get("claim_id")

        if claim_id is None:
            # fallback: extract first number from the raw question
            match = re.search(r"\d+", question)
            if match:
                claim_id = int(match.group())

        if claim_id is None:
            return "Please provide a valid claim ID."

        claim = get_claim_status(int(claim_id))
        if claim:
            return f"Claim Details:\n\n{format_claim(claim)}"
        return f"No claim found with ID {claim_id}."

    # -----------------------------------------------------------------------
    # CREATE CLAIM — starts a multi-turn conversation
    # -----------------------------------------------------------------------
    if intent == "CREATE_CLAIM":
        # planner may have already extracted the incident type
        incident_type = (
            task.get("incident_type")
            or detect_incident_type(question)
        )

        if incident_type:
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

        # incident type not known — ask user
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

    # -----------------------------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------------------------
    return (
        "I could not understand your request.\n\n"
        "You can:\n"
        "• Ask policy questions\n"
        "• Create a claim\n"
        "• Track claim status"
    )

# ---------------------------------------------------------------------------
# Multi-turn conversation state handler
# Handles the WAITING_FOR_INCIDENT_TYPE → WAITING_FOR_DESCRIPTION →
# WAITING_FOR_CONFIRMATION steps for claim creation.
# Returns a response string, or None if no pending state.
# ---------------------------------------------------------------------------

def handle_pending_state(
    session_id: str,
    policy_id:  int,
    question:   str,
) -> str | None:

    if session_id not in conversation_state:
        return None

    pending = conversation_state[session_id]

    if pending.get("action") != "CREATE_CLAIM":
        return None

    step = pending.get("step")

    # -----------------------------------------------------------------------
    # Step 1 — waiting for user to name an incident type
    # -----------------------------------------------------------------------
    if step == "WAITING_FOR_INCIDENT_TYPE":
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

    # -----------------------------------------------------------------------
    # Step 2 — waiting for description
    # -----------------------------------------------------------------------
    if step == "WAITING_FOR_DESCRIPTION":
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

    # -----------------------------------------------------------------------
    # Step 3 — waiting for YES / NO confirmation
    # FIX 9: original live code only accepted "yes" — "y" and "confirm"
    #        were in the commented code but were lost. Restored here.
    # -----------------------------------------------------------------------
    if step == "WAITING_FOR_CONFIRMATION":
        answer = question.strip().lower()

        if answer in CONFIRM_WORDS:
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

        if answer in CANCEL_WORDS:
            del conversation_state[session_id]
            return (
                "Claim creation cancelled.\n\n"
                "You can start again by saying: create a claim."
            )

        return (
            "I did not understand.\n\n"
            "Please reply YES to create the claim or NO to cancel."
        )

    return None

# ---------------------------------------------------------------------------
# Utility REST endpoints (unchanged from original)
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
# FIX 8: renamed /ask-policy → /chat, raw dict → ChatRequest Pydantic model
# ---------------------------------------------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):
    policy_id  = request.policy_id
    question   = request.question.strip()
    session_id = request.session_id

    # -----------------------------------------------------------------------
    # 1. Resume multi-turn conversation if one is in progress
    # -----------------------------------------------------------------------
    pending_response = handle_pending_state(session_id, policy_id, question)
    if pending_response is not None:
        return {"answer": pending_response}

    # -----------------------------------------------------------------------
    # 2. Generate execution plan from LLM planner
    # -----------------------------------------------------------------------
    plan = generate_plan(question)
    print(f"\n[chat] PLAN: {plan}")

    # -----------------------------------------------------------------------
    # 3. Handle empty plan — planner failed or question was unrecognised
    # FIX 10: original code crashed with IndexError on plan[0] when plan=[]
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # 4. Execute plan
    # FIX 6: single and multi paths now both call execute_task() — no
    #        duplication.
    # -----------------------------------------------------------------------
    if len(plan) == 1:
        answer = execute_task(plan[0], policy_id, session_id, question)
        return {"answer": answer}

    # Multi-intent: run every task and join results with a divider
    responses = [
        execute_task(task, policy_id, session_id, question)
        for task in plan
    ]
    return {"answer": "\n\n---\n\n".join(responses)}
