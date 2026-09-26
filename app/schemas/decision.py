from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.evidence import EvidenceObject

class TrustStatus(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    INCOMPLETE = "INCOMPLETE"
    CONFLICTING = "CONFLICTING"
    LOW_QUALITY = "LOW_QUALITY"
    NEED_MORE_INFO = "NEED_MORE_INFO"
    REFUSE = "REFUSE"

class RecommendationAction(str, Enum):
    APPROVE = "APPROVE"
    PROCEED = "PROCEED"
    REQUEST_DATA = "REQUEST_DATA"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REQUEST_BETTER_SOURCES = "REQUEST_BETTER_SOURCES"
    SPECIFY_REQUIRED_EVIDENCE = "SPECIFY_REQUIRED_EVIDENCE"
    REFUSE_ESCALATE = "REFUSE_ESCALATE"

class ContradictionSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ContradictionItem(BaseModel):
    contradiction_id: str = Field(default_factory=lambda: f"CONTRA-{int(datetime.utcnow().timestamp())}")
    evidence_ids: List[str]
    subject: str
    predicate: str
    conflicting_values: List[Any]
    severity: ContradictionSeverity
    description: str
    resolution_suggestion: Optional[str] = None

class MissingInformationItem(BaseModel):
    item: str
    reason: str
    priority: str = "HIGH"
    suggested_source: Optional[str] = None

class MLFraudModel(BaseModel):
    risk_score: float = Field(..., description="0.0 to 1.0 probability")
    model: str = "xgboost"
    anomaly_score: Optional[float] = None
    feature_contributions: Optional[Dict[str, float]] = None

class ChallengePacket(BaseModel):
    performed: bool = True
    hypothesis: Optional[str] = None
    counter_evidence_found: bool = False
    counter_evidence_ids: List[str] = []
    challenge_summary: str = ""
    original_risk_state: Optional[str] = None
    adjusted_risk_state: Optional[str] = None

class DecisionPacket(BaseModel):
    case_id: str = Field(..., description="Target Case ID")
    trust_status: TrustStatus = Field(..., description="One of 6 Deterministic Final States")
    fraud_model: MLFraudModel
    evidence_quality: str = Field(default="MEDIUM", description="HIGH, MEDIUM, LOW")
    completeness: float = Field(default=1.0, description="0.0 to 1.0 completeness ratio")
    
    evidence: List[EvidenceObject] = Field(default_factory=list)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    missing_information: List[MissingInformationItem] = Field(default_factory=list)
    
    reasoning: str = Field(..., description="Evidence-backed reasoning")
    challenge: ChallengePacket = Field(default_factory=ChallengePacket)
    recommendation: RecommendationAction = Field(..., description="Direct actionable outcome")
    
    audit: Dict[str, Any] = Field(default_factory=lambda: {
        "timestamp": datetime.utcnow().isoformat(),
        "engine_version": "2.0.0",
        "gate": "DETERMINISTIC_DECISION_GATE"
    })
