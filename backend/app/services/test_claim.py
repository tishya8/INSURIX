from app.services.claim_service import (
    update_claim_status,
    get_claim_status
)

update_claim_status(
    2,
    "UNDER_REVIEW"
)

claim = get_claim_status(2)

print("\nUPDATED CLAIM")

print(claim)