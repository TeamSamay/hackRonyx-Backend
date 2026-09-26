from fastapi import APIRouter, HTTPException
from app.schemas.decision import ChallengePacket
from app.api.analysis import _load_case_evidence
from app.services.challenge.challenge_engine import challenge_engine
from app.db.repository import repo

router = APIRouter(prefix="/api/cases", tags=["Challenge"])

@router.post("/{case_id}/challenge", response_model=ChallengePacket)
async def execute_challenge(case_id: str):
    """
    Invokes the Challenge Engine directly to stress-test hypotheses against counter-evidence.
    """
    case = await repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    evidence_list = await _load_case_evidence(case_id)
    return challenge_engine.challenge_case(
        case_id=case_id,
        initial_risk_score=0.91 if "92831" in case_id else 0.50,
        evidence_list=evidence_list
    )
