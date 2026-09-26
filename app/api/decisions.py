from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import DecisionModel
from app.schemas.decision import DecisionPacket
from app.api.analysis import run_case_analysis

router = APIRouter(prefix="/api/cases", tags=["Decisions"])

@router.get("/{case_id}/decision", response_model=DecisionPacket)
async def get_latest_decision(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the canonical DecisionPacket for a case (React Frontend Contract).
    """
    result = await db.execute(
        select(DecisionModel).where(DecisionModel.case_id == case_id).order_by(DecisionModel.id.desc())
    )
    decision = result.scalars().first()
    if not decision:
        return await run_case_analysis(case_id=case_id, db=db)

    return DecisionPacket(**decision.packet_json)
