import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.schemas.evidence import (
    EvidenceObject,
    SourceMetadata,
    ClaimPayload,
    QualityMetrics,
    TraceabilityInfo,
    SourceType,
    ReliabilityLevel,
    FreshnessLevel
)
from app.services.evidence.quality_engine import quality_engine

class EvidenceNormalizer:
    """
    Evidence Normalization Layer.
    Converts disparate raw inputs (SQL, CSV, Excel, PDF, OCR images, APIs)
    into standard canonical Evidence Objects.
    """

    @staticmethod
    def generate_evidence_id(prefix: str = "E") -> str:
        short_id = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{short_id}"

    @classmethod
    def from_database_record(
        cls,
        case_id: str,
        table_name: str,
        record_id: str,
        subject: str,
        predicate: str,
        value: Any,
        system_name: str = "BANK_TRANSACTION_DB",
        reliability: ReliabilityLevel = ReliabilityLevel.HIGH,
        raw_payload: Optional[Dict[str, Any]] = None
    ) -> EvidenceObject:
        
        quality = quality_engine.assess_quality(
            source_type=SourceType.DATABASE,
            explicit_reliability=reliability,
            explicit_freshness=FreshnessLevel.CURRENT,
            completeness=1.0,
            has_traceability=True
        )

        return EvidenceObject(
            evidence_id=cls.generate_evidence_id("E-DB"),
            case_id=case_id,
            source=SourceMetadata(
                type=SourceType.DATABASE,
                system=system_name,
                name=f"{table_name}:{record_id}"
            ),
            claim=ClaimPayload(
                subject=str(subject),
                predicate=str(predicate),
                value=value,
                raw_statement=f"{predicate} is {value} in table {table_name}"
            ),
            timestamp=datetime.utcnow().isoformat(),
            quality=quality,
            traceability=TraceabilityInfo(
                table=table_name,
                record_id=str(record_id)
            ),
            raw_payload=raw_payload or {}
        )

    @classmethod
    def from_document_text(
        cls,
        case_id: str,
        filename: str,
        page_num: Optional[int],
        subject: str,
        predicate: str,
        value: Any,
        doc_type: SourceType = SourceType.PDF,
        raw_statement: Optional[str] = None,
        ocr_confidence: Optional[float] = None
    ) -> EvidenceObject:
        
        quality = quality_engine.assess_quality(
            source_type=doc_type,
            ocr_confidence=ocr_confidence,
            completeness=0.9,
            has_traceability=True
        )

        prefix = "E-OCR" if doc_type == SourceType.IMAGE else "E-DOC"

        return EvidenceObject(
            evidence_id=cls.generate_evidence_id(prefix),
            case_id=case_id,
            source=SourceMetadata(
                type=doc_type,
                system="UPLOADED_DOCUMENT",
                name=filename,
                reference=filename
            ),
            claim=ClaimPayload(
                subject=str(subject),
                predicate=str(predicate),
                value=value,
                raw_statement=raw_statement or f"Extracted from {filename} page {page_num}: {predicate} = {value}"
            ),
            timestamp=datetime.utcnow().isoformat(),
            quality=quality,
            traceability=TraceabilityInfo(
                file=filename,
                page=page_num
            )
        )

    @classmethod
    def from_tabular_row(
        cls,
        case_id: str,
        filename: str,
        row_idx: int,
        subject: str,
        predicate: str,
        value: Any,
        source_type: SourceType = SourceType.CSV,
        raw_row_dict: Optional[Dict[str, Any]] = None
    ) -> EvidenceObject:
        
        quality = quality_engine.assess_quality(
            source_type=source_type,
            completeness=1.0,
            has_traceability=True
        )

        prefix = "E-XLS" if source_type == SourceType.EXCEL else "E-CSV"

        return EvidenceObject(
            evidence_id=cls.generate_evidence_id(prefix),
            case_id=case_id,
            source=SourceMetadata(
                type=source_type,
                system="TABULAR_FEED",
                name=filename
            ),
            claim=ClaimPayload(
                subject=str(subject),
                predicate=str(predicate),
                value=value,
                raw_statement=f"Row {row_idx} in {filename}: {predicate} = {value}"
            ),
            timestamp=datetime.utcnow().isoformat(),
            quality=quality,
            traceability=TraceabilityInfo(
                file=filename,
                line_number=row_idx
            ),
            raw_payload=raw_row_dict or {}
        )

normalizer = EvidenceNormalizer()
