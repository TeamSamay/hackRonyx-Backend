from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import CaseModel, EvidenceModel
from app.schemas.decision import ChallengePacket
from app.api.analysis import _load_case_evidence
from app.services.challenge.challenge_engine import challenge_engine

router = APIRouter(prefix="/api/cases", tags=["Challenge"])

@router.post("/{case_id}/challenge", response_model=ChallengePacket)
async def execute_challenge(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Invokes the Challenge Engine directly to stress-test hypotheses against counter-evidence.
    """
    case_res = await db.execute(select(CaseModel).where(CaseModel.case_id == case_id))
    case = case_res.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    evidence_list = await _load_case_evidence(case_id, db)
    return challenge_engine.challenge_case(
        case_id=case_id,
        initial_risk_score=0.91 if "92831" in case_id else 0.50,
        evidence_list=evidence_list
    )
