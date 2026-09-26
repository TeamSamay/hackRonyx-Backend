from sqlalchemy import Column, String, Integer, Float, Boolean, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class CaseModel(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    entity_type = Column(String(64), default="TRANSACTION")
    entity_id = Column(String(128), nullable=True)
    status = Column(String(32), default="OPEN")
    trust_status = Column(String(32), nullable=True)
    initial_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    evidence_items = relationship("EvidenceModel", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("DocumentModel", back_populates="case", cascade="all, delete-orphan")
    decisions = relationship("DecisionModel", back_populates="case", cascade="all, delete-orphan")
    reviews = relationship("ReviewModel", back_populates="case", cascade="all, delete-orphan")


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False) # PDF, CSV, XLSX, PNG, JPG, DOCX
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    sha256 = Column(String(64), nullable=True)
    status = Column(String(32), default="PROCESSED")
    ocr_applied = Column(Boolean, default=False)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="documents")


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False)
    
    # Source Info
    source_type = Column(String(32), nullable=False) # DATABASE, PDF, IMAGE, CSV, EXCEL, API
    source_system = Column(String(128), nullable=True)
    source_reference = Column(String(255), nullable=True)
    
    # Claim Data
    claim_subject = Column(String(128), nullable=False)
    claim_predicate = Column(String(128), nullable=False)
    claim_value = Column(JSON, nullable=False)
    raw_statement = Column(Text, nullable=True)
    
    # Quality Attributes
    reliability = Column(String(32), default="HIGH")
    freshness = Column(String(32), default="CURRENT")
    completeness = Column(Float, default=1.0)
    ocr_confidence = Column(Float, nullable=True)
    overall_quality = Column(String(32), default="HIGH")
    
    # Traceability
    traceability = Column(JSON, default=dict)
    raw_payload = Column(JSON, default=dict)
    
    # Vector / Embedding for RAG
    embedding_json = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="evidence_items")


class ClaimModel(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False)
    evidence_id = Column(String(64), ForeignKey("evidence.evidence_id"), nullable=False)
    subject = Column(String(128), nullable=False)
    predicate = Column(String(128), nullable=False)
    value = Column(JSON, nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContradictionModel(Base):
    __tablename__ = "contradictions"

    id = Column(Integer, primary_key=True, index=True)
    contradiction_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False)
    subject = Column(String(128), nullable=False)
    predicate = Column(String(128), nullable=False)
    severity = Column(String(32), default="HIGH")
    conflicting_values = Column(JSON, nullable=False)
    evidence_ids = Column(JSON, nullable=False) # list of IDs
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DecisionModel(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False)
    trust_status = Column(String(32), nullable=False) # SUFFICIENT, INCOMPLETE, CONFLICTING, LOW_QUALITY, NEED_MORE_INFO, REFUSE
    fraud_risk_score = Column(Float, nullable=False)
    anomaly_score = Column(Float, default=0.0)
    evidence_quality = Column(String(32), default="MEDIUM")
    completeness = Column(Float, default=1.0)
    recommendation = Column(String(64), nullable=False)
    reasoning = Column(Text, nullable=False)
    packet_json = Column(JSON, nullable=False) # Full Canonical Decision Packet
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="decisions")


class ReviewModel(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False)
    reviewer_name = Column(String(128), nullable=False)
    action_taken = Column(String(64), nullable=False) # OVERRIDE, APPROVE, REJECT, ESCALATE, REQUEST_MORE_DOCS
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="reviews")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), nullable=True)
    action = Column(String(128), nullable=False)
    actor = Column(String(128), default="SYSTEM")
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConnectorModel(Base):
    __tablename__ = "connectors"

    id = Column(Integer, primary_key=True, index=True)
    connector_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    connector_type = Column(String(32), nullable=False)
    config_json = Column(JSON, default=dict)
    read_only = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
