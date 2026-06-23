"""
INSURIX — FastAPI entry point (refactored)

Changes from original:
  1. Removed 1800+ lines of commented-out dead code
  2. Removed duplicate import of get_user_policies (was imported from
     both claim_service and policy_service — now only policy_service)
  3. Moved `import re` to top level (was re-imported inside 3 functions)
  4. Added missing import for detect_incident_type (was used but never imported)
  5. Extracted execute_task() — single function that handles one plan task,
     called by both single-intent and multi-intent paths.
     Previously the identical POLICY_QUERY / CREATE_CLAIM / TRACK_CLAIM
     blocks were copy-pasted twice (single + multi), which meant any bug
     fix had to be applied in two places.
  6. Added Pydantic request model (ChatRequest) so /chat has proper
     validation instead of a raw dict with no type safety.
  7. Normalised TRACK_CLAIM to read task["claim_id"] (integer from planner)
     instead of regex-searching task["query"] which didn't exist on that task.
  8. Added fallback when plan is empty (LLM / parse failure).
"""

import re
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.planner_service import create_plan
from app.services.claim_service import (
    create_claim,
    get_claim_status,
    update_claim_status,
)
from app.services.rag_service import ask_policy

# FIX: was imported from both claim_service AND policy_service — pick one
from app.services.policy_service import (
    get_user_policies,
    get_policy_document,
)

from app.services.intent_service import detect_intent        # kept for future use
from app.services.session_service import conversation_state

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

# ---------------------------------------------------------------------------
# Request / response models
# FIX: was raw dict — Pydantic gives validation + auto Swagger docs
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    policy_id:  int
    question:   str
    session_id: str = "default_user"

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

INCIDENT_KEYWORDS = {
    "theft":    "THEFT",
    "accident": "ACCIDENT",
    "flood":    "FLOOD",
    "fire":     "FIRE",
    "other":    "OTHER",
}

def normalize_query(query: str) -> str:
    """Strip trailing punctuation from a question string."""
    return query.strip().rstrip("?!.")


def detect_incident_type(text: str) -> str | None:
    """
    Return the first matching incident type found in text, or None.
    FIX: was defined inline with if/elif chains duplicated in 3 places —
         now one function used everywhere.
    """
    lowered = text.lower()
    for keyword, incident_type in INCIDENT_KEYWORDS.items():
        if keyword in lowered:
            return incident_type
    return None


def format_claim(claim: dict) -> str:
    """
    Render a claim dict as a readable string.
    FIX: identical f-string was copy-pasted in 4 places — now one function.
    """
    return (
        f"Claim ID: {claim['claim_id']}\n"
        f"Status: {claim['claim_status']}\n"
        f"Incident: {claim['incident_type']}\n"
        f"Description: {claim['description']}"
    )

# ---------------------------------------------------------------------------
# Core task executor
# FIX: was copy-pasted for single-intent AND multi-intent — now one function.
#      Both paths call execute_task() so logic only lives in one place.
# ---------------------------------------------------------------------------

def execute_task(
    task:       dict,
    policy_id:  int,
    session_id: str,
    question:   str,
) -> str:
    """
    Execute a single plan task and return a response string.

    task examples:
      {"intent": "POLICY_QUERY",  "query": "Is flood covered?"}
      {"intent": "TRACK_CLAIM",   "claim_id": 5}
      {"intent": "CREATE_CLAIM",  "incident_type": "THEFT"}
    """
    intent = task.get("intent")

    # -------------------------------------------------------------------
    # POLICY QUERY — RAG pipeline
    # -------------------------------------------------------------------
    if intent == "POLICY_QUERY":
        query  = task.get("query", question)
        answer = ask_policy(policy_id, normalize_query(query))
        return f"Policy Answer:\n\n{answer}"

    # -------------------------------------------------------------------
    # TRACK CLAIM
    # FIX: original multi-intent path read task["query"] which does not
    #      exist on TRACK_CLAIM tasks — planner puts the id in task["claim_id"]
    # -------------------------------------------------------------------
    if intent == "TRACK_CLAIM":
        # Prefer the structured claim_id from the planner
        claim_id = task.get("claim_id")

        # Fallback: extract digits from question if planner didn't parse it
        if claim_id is None:
            match = re.search(r"\d+", question)
            if match:
                claim_id = int(match.group())

        if claim_id is None:
            return "Please provide a valid claim ID."

        claim = get_claim_status(int(claim_id))
        if claim:
            return f"Claim Details:\n\n{format_claim(claim)}"
        return f"No claim found with ID {claim_id}."

    # -------------------------------------------------------------------
    # CREATE CLAIM — multi-step conversation
    # -------------------------------------------------------------------
    if intent == "CREATE_CLAIM":
        # Planner may have already extracted the incident type
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

        # Incident type unknown — ask user
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

    # -------------------------------------------------------------------
    # UNKNOWN intent
    # -------------------------------------------------------------------
    return (
        "I could not understand your request.\n\n"
        "You can:\n"
        "• Ask policy questions\n"
        "• Create a claim\n"
        "• Track claim status"
    )

# ---------------------------------------------------------------------------
# Conversation state handlers (multi-turn claim creation flow)
# ---------------------------------------------------------------------------

def handle_pending_state(
    session_id: str,
    policy_id:  int,
    question:   str,
) -> str | None:
    """
    If a multi-turn conversation is in progress, advance its state.
    Returns the response string, or None if no pending state exists.
    """
    if session_id not in conversation_state:
        return None

    pending = conversation_state[session_id]
    action  = pending.get("action")
    step    = pending.get("step")

    if action != "CREATE_CLAIM":
        return None

    # ---------------------------------------------------------------
    # Step 1 — waiting for the user to name an incident type
    # ---------------------------------------------------------------
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

    # ---------------------------------------------------------------
    # Step 2 — waiting for a description
    # ---------------------------------------------------------------
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
            f"Reply YES to create the claim."
        )

    # ---------------------------------------------------------------
    # Step 3 — waiting for YES/NO confirmation
    # ---------------------------------------------------------------
    if step == "WAITING_FOR_CONFIRMATION":
        if question.strip().lower() == "yes":
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

        del conversation_state[session_id]
        return "Claim creation cancelled. You can start again by saying: create a claim."

    return None

# ---------------------------------------------------------------------------
# REST endpoints — utility
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

    # -----------------------------------------------------------------------
    # 1. Check if a multi-turn conversation is already in progress
    # -----------------------------------------------------------------------
    pending_response = handle_pending_state(session_id, policy_id, question)
    if pending_response is not None:
        return {"answer": pending_response}

    # -----------------------------------------------------------------------
    # 2. Generate execution plan from LLM planner
    # -----------------------------------------------------------------------
    plan = create_plan(question)
    print(f"\n[chat] PLAN: {plan}")

    # -----------------------------------------------------------------------
    # 3. Fallback if planner returned nothing
    # FIX: original code crashed with IndexError on plan[0] when plan == []
    # -----------------------------------------------------------------------
    if not plan:
        return {
            "answer": (
                "I could not understand your request.\n\n"
                "You can:\n"
                "• Ask policy questions\n"
                "• Create a claim\n"
                "• Track claim status"
            )
        }

    # -----------------------------------------------------------------------
    # 4. Execute plan
    # FIX: single and multi-intent paths both call execute_task()
    #      instead of duplicating the same if/elif blocks
    # -----------------------------------------------------------------------
    if len(plan) == 1:
        answer = execute_task(plan[0], policy_id, session_id, question)
        return {"answer": answer}

    # Multi-intent — execute each task and join responses
    responses = [
        execute_task(task, policy_id, session_id, question)
        for task in plan
    ]
    return {"answer": "\n\n---\n\n".join(responses)}
