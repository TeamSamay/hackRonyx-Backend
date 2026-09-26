import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Query

from app.schemas.case import CaseCreate, CaseResponse, CaseListResponse
from app.schemas.decision import DecisionPacket
from app.db.repository import repo
from app.core.logging import logger

router = APIRouter(prefix="/api/cases", tags=["Cases"])

@router.post("", response_model=CaseResponse)
async def create_case(case_in: CaseCreate):
    case_id = case_in.case_id or f"CASE-{uuid.uuid4().hex[:6].upper()}"
    
    # Check if exists
    existing = await repo.get_case(case_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Case ID {case_id} already exists.")

    case_data = {
        "case_id": case_id,
        "title": case_in.title,
        "description": case_in.description,
        "entity_type": case_in.entity_type,
        "entity_id": case_in.entity_id or case_id,
        "status": "OPEN",
        "trust_status": None,
        "initial_metadata": case_in.initial_metadata or {}
    }
    await repo.create_case(case_data)

    return CaseResponse(
        case_id=case_data["case_id"],
        title=case_data["title"],
        description=case_data["description"],
        entity_type=case_data["entity_type"],
        entity_id=case_data["entity_id"],
        status=case_data["status"],
        trust_status=None,
        evidence_count=0,
        created_at=case_data["created_at"],
        updated_at=case_data["updated_at"]
    )

@router.get("", response_model=CaseListResponse)
async def list_cases(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    cases = await repo.list_cases(limit=limit, offset=offset)

    case_responses = []
    for c in cases:
        decision_raw = await repo.get_latest_decision(c["case_id"])
        last_decision = DecisionPacket(**decision_raw) if decision_raw else None
        evidence_items = await repo.get_case_evidence(c["case_id"])
            
        case_responses.append(CaseResponse(
            case_id=c["case_id"],
            title=c["title"],
            description=c.get("description"),
            entity_type=c.get("entity_type", "TRANSACTION"),
            entity_id=c.get("entity_id"),
            status=c.get("status", "OPEN"),
            trust_status=c.get("trust_status"),
            evidence_count=len(evidence_items),
            created_at=c.get("created_at", datetime.utcnow().isoformat()),
            updated_at=c.get("updated_at", datetime.utcnow().isoformat()),
            decision=last_decision
        ))

    return CaseListResponse(total=len(case_responses), cases=case_responses)

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str):
    c = await repo.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    decision_raw = await repo.get_latest_decision(case_id)
    last_decision = DecisionPacket(**decision_raw) if decision_raw else None
    evidence_items = await repo.get_case_evidence(case_id)

    return CaseResponse(
        case_id=c["case_id"],
        title=c["title"],
        description=c.get("description"),
        entity_type=c.get("entity_type", "TRANSACTION"),
        entity_id=c.get("entity_id"),
        status=c.get("status", "OPEN"),
        trust_status=c.get("trust_status"),
        evidence_count=len(evidence_items),
        created_at=c.get("created_at", datetime.utcnow().isoformat()),
        updated_at=c.get("updated_at", datetime.utcnow().isoformat()),
        decision=last_decision
    )
