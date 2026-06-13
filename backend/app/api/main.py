from fastapi import FastAPI
from app.services.claim_service import (
    get_user_policies,
    create_claim,
    get_claim_status,
    update_claim_status
)
from app.services.rag_service import ask_policy

from app.services.policy_service import (
    get_user_policies,
    get_policy_document
)

from app.services.intent_service import detect_intent


app = FastAPI()


@app.get("/")
def root():
    return {"message": "INSURIX API Running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/users/{user_id}/policies")
def fetch_user_policies(user_id: int):

    policies = get_user_policies(user_id)

    return policies

@app.post("/claims")
def create_new_claim(
    policy_id: int,
    incident_type: str,
    description: str
):

    claim_id = create_claim(
        policy_id,
        incident_type,
        description
    )

    return {
        "claim_id": claim_id,
        "status": "SUBMITTED"
    }

@app.get("/claims/{claim_id}")
def fetch_claim_status(claim_id: int):

    claim = get_claim_status(claim_id)

    return claim

@app.put("/claims/{claim_id}/status")
def update_status(
    claim_id: int,
    status: str
):

    update_claim_status(
        claim_id,
        status
    )

    return {
        "message": "Claim status updated",
        "claim_id": claim_id,
        "status": status
    }


@app.post("/ask-policy")
def ask_policy_api(request: dict):

    policy_id = request["policy_id"]
    question = request["question"]

    # Detect Intent
    intent = detect_intent(question)

    print("\nDetected Intent:", intent)

    if intent == "POLICY_QUERY":

        answer = ask_policy(
            policy_id,
            question
        )

        return {
            "intent": intent,
            "policy_id": policy_id,
            "question": question,
            "answer": answer
        }

    elif intent == "CREATE_CLAIM":

        return {
            "intent": intent,
            "message": "Claim Creation Workflow Triggered"
        }

    elif intent == "TRACK_CLAIM":

        claim_id = request["claim_id"]

        claim = get_claim_status(claim_id)

        return {
            "intent": intent,
            "claim": claim
        }

    return {
        "intent": "UNKNOWN",
        "message": "Could not determine user intent"
    }

@app.get("/policies/{policy_id}/document")
def get_document(policy_id: int):

    document = get_policy_document(policy_id)

    if document is None:
        return {
            "message": "Policy document not found"
        }

    return document