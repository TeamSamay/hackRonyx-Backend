import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import CaseModel, EvidenceModel, DecisionModel
from app.schemas.case import CaseCreate, CaseResponse, CaseListResponse
from app.schemas.decision import DecisionPacket
from app.core.logging import logger

router = APIRouter(prefix="/api/cases", tags=["Cases"])

@router.post("", response_model=CaseResponse)
async def create_case(case_in: CaseCreate, db: AsyncSession = Depends(get_db)):
    case_id = case_in.case_id or f"CASE-{uuid.uuid4().hex[:6].upper()}"
    
    # Check if exists
    result = await db.execute(select(CaseModel).where(CaseModel.case_id == case_id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail=f"Case ID {case_id} already exists.")

    new_case = CaseModel(
        case_id=case_id,
        title=case_in.title,
        description=case_in.description,
        entity_type=case_in.entity_type,
        entity_id=case_in.entity_id or case_id,
        status="OPEN",
        initial_metadata=case_in.initial_metadata or {}
    )
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)

    return CaseResponse(
        case_id=new_case.case_id,
        title=new_case.title,
        description=new_case.description,
        entity_type=new_case.entity_type,
        entity_id=new_case.entity_id,
        status=new_case.status,
        trust_status=None,
        evidence_count=0,
        created_at=new_case.created_at.isoformat(),
        updated_at=new_case.updated_at.isoformat()
    )

@router.get("", response_model=CaseListResponse)
async def list_cases(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(CaseModel).options(selectinload(CaseModel.evidence_items), selectinload(CaseModel.decisions)).offset(offset).limit(limit)
    result = await db.execute(query)
    cases = result.scalars().all()

    case_responses = []
    for c in cases:
        last_decision = None
        if c.decisions:
            last_decision = DecisionPacket(**c.decisions[-1].packet_json)
            
        case_responses.append(CaseResponse(
            case_id=c.case_id,
            title=c.title,
            description=c.description,
            entity_type=c.entity_type,
            entity_id=c.entity_id,
            status=c.status,
            trust_status=c.trust_status,
            evidence_count=len(c.evidence_items),
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
            decision=last_decision
        ))

    return CaseListResponse(total=len(case_responses), cases=case_responses)

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    query = select(CaseModel).options(selectinload(CaseModel.evidence_items), selectinload(CaseModel.decisions)).where(CaseModel.case_id == case_id)
    result = await db.execute(query)
    c = result.scalars().first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    last_decision = None
    if c.decisions:
        last_decision = DecisionPacket(**c.decisions[-1].packet_json)

    return CaseResponse(
        case_id=c.case_id,
        title=c.title,
        description=c.description,
        entity_type=c.entity_type,
        entity_id=c.entity_id,
        status=c.status,
        trust_status=c.trust_status,
        evidence_count=len(c.evidence_items),
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
        decision=last_decision
    )
