"""
INSURIX — FastAPI entry point

Bug fixes in this version
──────────────────────────
FIX-1  CREATE_CLAIM in multi-intent now deferred: if CREATE_CLAIM is one of
       several intents, all non-claim tasks run first, then the claim flow
       starts. Previously it ran inline and left a pending state mid-response
       that corrupted the very next message.

FIX-2  Escape hatch in pending state: if the user sends a message that clearly
       maps to TRACK_CLAIM or POLICY_QUERY while a CREATE_CLAIM flow is in
       progress, the pending state is cancelled and the new intent is handled.
       Previously "track claim 2" during confirmation got the response
       "I did not understand. Please reply YES or NO."

FIX-3  INCIDENT_KEYWORDS now includes "flood" → FLOOD (was missing in the
       planner prompt; detect_incident_type already had it but planner
       returned UNKNOWN which then got stored as the incident type).

FIX-4  Planner now strips hallucinated CREATE_CLAIM(UNKNOWN) when user never
       used a claim-creation trigger word. Fixes "What documents are required
       and track claim 1" producing a spurious CREATE_CLAIM.

FIX-5  Multiple coverage questions ("Does it cover flood AND fire?") now
       generate a single POLICY_QUERY, not two, and never trigger CREATE_CLAIM.

FIX-6  session_service is now a SessionStore class with named methods instead
       of a raw dict — prevents accidental stale-state bugs.
"""

import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.planner_service import generate_plan
from app.services.claim_service   import (
    create_claim, get_claim_status, update_claim_status,
)
from app.services.rag_service     import ask_policy
from app.services.policy_service  import get_user_policies, get_policy_document
from app.services.session_service import sessions          # SessionStore instance
from app.services.auth_service    import login_user
from app.rag.policy_loader        import build_full_vectorstore

# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI(title="INSURIX API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup — build ChromaDB once
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup_build_chroma():
    import os
    chroma_dir = "./chroma_db"
    if os.path.exists(chroma_dir) and os.listdir(chroma_dir):
        print("[Startup] ChromaDB already exists — skipping rebuild.")
    else:
        print("[Startup] ChromaDB not found — building now…")
        build_full_vectorstore()
        print("[Startup] ChromaDB ready.")

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

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
# Constants
# ---------------------------------------------------------------------------

INCIDENT_KEYWORDS: dict[str, list[str]] = {
    "THEFT":    ["theft", "stolen", "steal", "robbery", "rob"],
    "ACCIDENT": ["accident", "crash", "crashed", "collision", "hit", "collide"],
    "FLOOD":    ["flood", "flooding", "water damage", "rain damage", "rain"],
    "FIRE":     ["fire", "burn", "burned", "flame", "blaze"],
    "OTHER":    ["other"],
}

CONFIRM_WORDS = {"yes", "y", "confirm", "ok", "okay", "sure"}
CANCEL_WORDS  = {"no",  "n", "cancel",  "stop", "abort", "quit", "exit"}

# Intents that should override a pending CREATE_CLAIM flow
OVERRIDE_INTENTS = {"TRACK_CLAIM", "POLICY_QUERY"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
# Task executor — handles one plan item
# ---------------------------------------------------------------------------

def execute_task(task: dict, policy_id: int, session_id: str, question: str) -> str:
    intent = task.get("intent")

    # ── POLICY QUERY ─────────────────────────────────────────────────────────
    if intent == "POLICY_QUERY":
        query  = task.get("query", question)
        answer = ask_policy(policy_id, normalize_query(query))
        return f"Policy Answer:\n\n{answer}"

    # ── TRACK CLAIM ──────────────────────────────────────────────────────────
    if intent == "TRACK_CLAIM":
        claim_id = task.get("claim_id")
        if claim_id is None:
            match = re.search(r"\d+", question)
            claim_id = int(match.group()) if match else None
        if claim_id is None:
            return "Please provide a valid claim ID. Example: track claim 5"

        claim = get_claim_status(int(claim_id))
        if claim:
            return f"Claim Details:\n\n{format_claim(claim)}"
        return f"No claim found with ID {claim_id}."

    # ── CREATE CLAIM — starts multi-turn flow ─────────────────────────────────
    if intent == "CREATE_CLAIM":
        incident_type = task.get("incident_type")

        # FIX-3: if planner returned UNKNOWN, try detecting from raw question
        if not incident_type or incident_type == "UNKNOWN":
            incident_type = detect_incident_type(question)

        if incident_type and incident_type != "UNKNOWN":
            sessions.set_waiting_for_description(session_id, incident_type)
            return (
                f"Claim creation started.\n\n"
                f"Incident Type: {incident_type}\n\n"
                f"Please provide a brief description of the incident."
            )

        # Incident type still unknown — ask user
        sessions.set_waiting_for_incident_type(session_id)
        return (
            "Please select the incident type:\n\n"
            "1. Theft\n"
            "2. Accident\n"
            "3. Flood\n"
            "4. Fire\n"
            "5. Other\n\n"
            "Reply with the incident type."
        )

    # ── UNKNOWN ───────────────────────────────────────────────────────────────
    return (
        "I could not understand your request.\n\n"
        "You can:\n"
        "• Ask policy questions\n"
        "• Create a claim\n"
        "• Track claim status"
    )

# ---------------------------------------------------------------------------
# Pending state handler — resumes a CREATE_CLAIM multi-turn flow
# FIX-2: checks if the new message maps to an override intent first
# ---------------------------------------------------------------------------

def handle_pending_state(
    session_id: str,
    policy_id:  int,
    question:   str,
    plan:       list,           # FIX-2: pass the fresh plan so we can escape
) -> str | None:

    if not sessions.has_pending(session_id):
        return None

    # ── FIX-2: Escape hatch ──────────────────────────────────────────────────
    # If the new message clearly maps to a different intent (TRACK_CLAIM or
    # POLICY_QUERY), cancel the pending CREATE_CLAIM and handle the new intent.
    # This fixes: "track claim 2" during confirmation getting "I did not
    # understand. Please reply YES or NO."
    if plan and all(t.get("intent") in OVERRIDE_INTENTS for t in plan):
        sessions.override_with_new_intent(session_id)
        return None  # fall through to normal plan execution

    pending = sessions.get(session_id)
    if not pending or pending.get("action") != "CREATE_CLAIM":
        return None

    step = pending.get("step")

    # ── Step 1: waiting for incident type ────────────────────────────────────
    if step == "WAITING_FOR_INCIDENT_TYPE":
        incident_type = detect_incident_type(question)
        if incident_type:
            sessions.set_waiting_for_description(session_id, incident_type)
            return "Please provide a brief description of the incident."

        return (
            "Please select a valid incident type:\n\n"
            "1. Theft\n2. Accident\n3. Flood\n4. Fire\n5. Other\n\n"
            "Reply with the incident type."
        )

    # ── Step 2: waiting for description ──────────────────────────────────────
    if step == "WAITING_FOR_DESCRIPTION":
        sessions.set_waiting_for_confirmation(
            session_id,
            pending["incident_type"],
            question,
        )
        return (
            f"Please confirm:\n\n"
            f"Incident Type: {pending['incident_type']}\n"
            f"Description: {question}\n\n"
            f"Reply YES to create the claim or NO to cancel."
        )

    # ── Step 3: waiting for YES / NO ─────────────────────────────────────────
    if step == "WAITING_FOR_CONFIRMATION":
        answer = question.strip().lower()

        if answer in CONFIRM_WORDS:
            claim_id = create_claim(
                policy_id,
                pending["incident_type"],
                pending["description"],
            )
            sessions.clear(session_id)
            return (
                f"Claim created successfully.\n\n"
                f"Claim ID: {claim_id}\n"
                f"Status: SUBMITTED\n"
                f"Incident Type: {pending['incident_type']}\n"
                f"Description: {pending['description']}"
            )

        if answer in CANCEL_WORDS:
            sessions.clear(session_id)
            return "Claim creation cancelled.\n\nYou can start again by saying: create a claim."

        # FIX-2: if user typed something that isn't yes/no AND it looks like
        # a new intent, escape. Otherwise give the usual retry prompt.
        return (
            "Please reply YES to confirm or NO to cancel the claim.\n\n"
            f"Incident Type: {pending['incident_type']}\n"
            f"Description: {pending['description']}"
        )

    return None

# ---------------------------------------------------------------------------
# Chat request model
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    policy_id:  int
    question:   str
    session_id: str = "default_user"

# ---------------------------------------------------------------------------
# Main chat endpoint
# ---------------------------------------------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):
    policy_id  = request.policy_id
    question   = request.question.strip()
    session_id = request.session_id

    # 1. Generate plan first (needed for escape-hatch check in handle_pending)
    plan = generate_plan(question)
    print(f"\n[chat] PLAN: {plan}")

    # 2. Resume multi-turn flow if one is in progress
    #    Pass the fresh plan so handle_pending can escape if needed (FIX-2)
    pending_response = handle_pending_state(session_id, policy_id, question, plan)
    if pending_response is not None:
        return {"answer": pending_response}

    # 3. Empty plan — unrecognised input
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

    # 4. FIX-1: Separate CREATE_CLAIM from other intents.
    #    Run TRACK_CLAIM and POLICY_QUERY tasks immediately.
    #    If CREATE_CLAIM is also in the plan, start it AFTER the others
    #    so the multi-turn state doesn't clobber the same response.
    other_tasks  = [t for t in plan if t.get("intent") != "CREATE_CLAIM"]
    create_tasks = [t for t in plan if t.get("intent") == "CREATE_CLAIM"]

    responses = []

    for task in other_tasks:
        responses.append(execute_task(task, policy_id, session_id, question))

    # Start claim creation last (it sets pending state for next message)
    if create_tasks:
        responses.append(execute_task(create_tasks[0], policy_id, session_id, question))

    return {"answer": "\n\n---\n\n".join(responses)}

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
    return {"message": "Claim status updated", "claim_id": claim_id, "status": status}