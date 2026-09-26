from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.db.repository import repo

router = APIRouter(prefix="/api/cases", tags=["Reviews"])

class HumanReviewSubmission(BaseModel):
    reviewer_name: str
    action_taken: str # APPROVE, REJECT, ESCALATE, REQUEST_MORE_DOCS, OVERRIDE
    notes: Optional[str] = None

class HumanReviewResponse(BaseModel):
    case_id: str
    reviewer_name: str
    action_taken: str
    notes: Optional[str] = None
    created_at: str

@router.post("/{case_id}/review", response_model=HumanReviewResponse)
async def submit_human_review(case_id: str, submission: HumanReviewSubmission):
    """
    Submits a human fraud analyst's final verdict / escalation into MongoDB.
    """
    case = await repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    review_data = {
        "case_id": case_id,
        "reviewer_name": submission.reviewer_name,
        "action_taken": submission.action_taken,
        "notes": submission.notes,
        "created_at": datetime.utcnow().isoformat()
    }
    await repo.add_review(review_data)

    return HumanReviewResponse(**review_data)

@router.get("/{case_id}/reviews", response_model=List[HumanReviewResponse])
async def list_case_reviews(case_id: str):
    rows = await repo.list_reviews(case_id)
    return [HumanReviewResponse(**r) for r in rows]
