from fastapi import APIRouter
from app.schemas.decision import DecisionPacket
from app.api.analysis import run_case_analysis
from app.db.repository import repo

router = APIRouter(prefix="/api/cases", tags=["Decisions"])

@router.get("/{case_id}/decision", response_model=DecisionPacket)
async def get_latest_decision(case_id: str):
    """
    Returns the canonical DecisionPacket for a case from MongoDB.
    """
    decision_raw = await repo.get_latest_decision(case_id)
    if not decision_raw:
        return await run_case_analysis(case_id=case_id)

    return DecisionPacket(**decision_raw)
