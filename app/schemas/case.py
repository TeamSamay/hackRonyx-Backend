from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.evidence import EvidenceObject
from app.schemas.decision import DecisionPacket, TrustStatus

class CaseCreate(BaseModel):
    case_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    entity_type: str = Field(default="TRANSACTION", description="TRANSACTION, KYC, LOAN, INVOICE, ACCOUNT")
    entity_id: Optional[str] = None
    initial_metadata: Optional[Dict[str, Any]] = None

class CaseResponse(BaseModel):
    case_id: str
    title: str
    description: Optional[str] = None
    entity_type: str
    entity_id: Optional[str] = None
    status: str = "OPEN"
    trust_status: Optional[TrustStatus] = None
    evidence_count: int = 0
    created_at: str
    updated_at: str
    decision: Optional[DecisionPacket] = None

class CaseListResponse(BaseModel):
    total: int
    cases: List[CaseResponse]
