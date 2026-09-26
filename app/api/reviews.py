from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import CaseModel, ReviewModel, AuditLogModel
from datetime import datetime

router = APIRouter(prefix="/api/cases", tags=["Reviews"])

class HumanReviewSubmission(BaseModel):
    reviewer_name: str
    action_taken: str # APPROVE, REJECT, ESCALATE, REQUEST_MORE_DOCS, OVERRIDE
    notes: Optional[str] = None

class HumanReviewResponse(BaseModel):
    id: int
    case_id: str
    reviewer_name: str
    action_taken: str
    notes: Optional[str] = None
    created_at: str

@router.post("/{case_id}/review", response_model=HumanReviewResponse)
async def submit_human_review(
    case_id: str,
    submission: HumanReviewSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a human fraud analyst's final verdict / escalation.
    """
    case_res = await db.execute(select(CaseModel).where(CaseModel.case_id == case_id))
    case = case_res.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    review = ReviewModel(
        case_id=case_id,
        reviewer_name=submission.reviewer_name,
        action_taken=submission.action_taken,
        notes=submission.notes
    )
    db.add(review)

    # Log to audit trail
    audit = AuditLogModel(
        case_id=case_id,
        action=f"HUMAN_REVIEW_{submission.action_taken}",
        actor=submission.reviewer_name,
        details={"notes": submission.notes}
    )
    db.add(audit)

    case.status = f"RESOLVED_{submission.action_taken}"
    await db.commit()
    await db.refresh(review)

    return HumanReviewResponse(
        id=review.id,
        case_id=review.case_id,
        reviewer_name=review.reviewer_name,
        action_taken=review.action_taken,
        notes=review.notes,
        created_at=review.created_at.isoformat()
    )

@router.get("/{case_id}/reviews", response_model=List[HumanReviewResponse])
async def list_case_reviews(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReviewModel).where(ReviewModel.case_id == case_id))
    rows = result.scalars().all()
    return [
        HumanReviewResponse(
            id=r.id,
            case_id=r.case_id,
            reviewer_name=r.reviewer_name,
            action_taken=r.action_taken,
            notes=r.notes,
            created_at=r.created_at.isoformat()
        )
        for r in rows
    ]
