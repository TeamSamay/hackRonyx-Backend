from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class SourceType(str, Enum):
    DATABASE = "DATABASE"
    PDF = "PDF"
    IMAGE = "IMAGE"
    CSV = "CSV"
    EXCEL = "EXCEL"
    API = "API"
    MANUAL = "MANUAL"
    DEVICE_SIGNAL = "DEVICE_SIGNAL"
    EXTERNAL = "EXTERNAL"

class ReliabilityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNVERIFIED = "UNVERIFIED"

class FreshnessLevel(str, Enum):
    CURRENT = "CURRENT"
    RECENT = "RECENT"
    OUTDATED = "OUTDATED"
    HISTORICAL = "HISTORICAL"

class SourceMetadata(BaseModel):
    type: SourceType
    system: Optional[str] = None
    name: Optional[str] = None
    reference: Optional[str] = None
    connector_id: Optional[str] = None

class ClaimPayload(BaseModel):
    subject: str = Field(..., description="Entity or ID, e.g. TX-92831 or ACC992")
    predicate: str = Field(..., description="Property, e.g. transaction_location, revenue, device_id")
    value: Any = Field(..., description="Observed value, e.g. Mumbai, 12.4 Cr, iPhone 14")
    raw_statement: Optional[str] = None
    confidence: float = 1.0

class QualityMetrics(BaseModel):
    reliability: ReliabilityLevel = ReliabilityLevel.HIGH
    freshness: FreshnessLevel = FreshnessLevel.CURRENT
    completeness: float = 1.0
    ocr_confidence: Optional[float] = None
    is_primary_source: bool = True
    overall_quality: str = "HIGH"

class TraceabilityInfo(BaseModel):
    file: Optional[str] = None
    page: Optional[int] = None
    table: Optional[str] = None
    record_id: Optional[str] = None
    line_number: Optional[int] = None
    bounding_box: Optional[List[float]] = None
    sha256: Optional[str] = None

class EvidenceObject(BaseModel):
    evidence_id: str = Field(..., description="Standardized ID e.g. E-001")
    case_id: str = Field(..., description="Case identifier e.g. CASE-92831")
    source: SourceMetadata
    claim: ClaimPayload
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    quality: QualityMetrics = Field(default_factory=QualityMetrics)
    traceability: TraceabilityInfo = Field(default_factory=TraceabilityInfo)
    raw_payload: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class EvidenceCreateRequest(BaseModel):
    case_id: str
    source_type: SourceType
    source_system: Optional[str] = "Manual Ingestion"
    claim_subject: str
    claim_predicate: str
    claim_value: Any
    reliability: ReliabilityLevel = ReliabilityLevel.HIGH
    freshness: FreshnessLevel = FreshnessLevel.CURRENT
    traceability: Optional[Dict[str, Any]] = None

class EvidenceUploadResponse(BaseModel):
    status: str = "processed"
    document_id: Optional[str] = None
    filename: Optional[str] = None
    evidence_count: int
    evidence_ids: List[str]
    evidence_objects: List[EvidenceObject]
