import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import CaseModel, DocumentModel, EvidenceModel
from app.schemas.evidence import (
    EvidenceObject,
    EvidenceCreateRequest,
    EvidenceUploadResponse,
    SourceMetadata,
    ClaimPayload,
    QualityMetrics,
    TraceabilityInfo,
    SourceType,
    ReliabilityLevel,
    FreshnessLevel
)
from app.services.documents.parser import document_parser
from app.services.evidence.normalizer import normalizer
from app.services.evidence.quality_engine import quality_engine
from app.workers.tasks import process_document_background
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/api", tags=["Evidence"])

@router.post("/evidence/upload", response_model=EvidenceUploadResponse)
async def upload_evidence_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    case_id: str = Form(...),
    source_type: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Multi-format file upload API:
    Supports PDF, CSV, XLSX, PNG, JPG, JPEG, TXT, DOCX.
    Extracts text, applies OCR if needed, normalizes claims into Evidence objects.
    """
    # 1. Verify case exists (or auto-create)
    result = await db.execute(select(CaseModel).where(CaseModel.case_id == case_id))
    case = result.scalars().first()
    if not case:
        case = CaseModel(
            case_id=case_id,
            title=f"Case {case_id}",
            description="Auto-created case from file upload.",
            entity_type="TRANSACTION",
            entity_id=case_id
        )
        db.add(case)
        await db.commit()

    # 2. Save file to storage
    doc_id = f"DOC-{uuid.uuid4().hex[:6].upper()}"
    filename = file.filename or "uploaded_file"
    file_ext = os.path.splitext(filename)[1].lower()
    save_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(save_path)

    # 3. Create Document DB record
    doc_record = DocumentModel(
        document_id=doc_id,
        case_id=case_id,
        filename=filename,
        file_type=file_ext.replace(".", "").upper(),
        file_path=save_path,
        file_size_bytes=file_size,
        status="PROCESSED"
    )
    db.add(doc_record)
    await db.commit()

    # 4. Synchronously parse for immediate availability
    evidence_objects = document_parser.parse_file(save_path, case_id)

    evidence_ids = []
    for ev in evidence_objects:
        ev_db = EvidenceModel(
            evidence_id=ev.evidence_id,
            case_id=case_id,
            source_type=ev.source.type.value,
            source_system=ev.source.system,
            source_reference=ev.source.reference or filename,
            claim_subject=ev.claim.subject,
            claim_predicate=ev.claim.predicate,
            claim_value=ev.claim.value,
            raw_statement=ev.claim.raw_statement,
            reliability=ev.quality.reliability.value,
            freshness=ev.quality.freshness.value,
            completeness=ev.quality.completeness,
            ocr_confidence=ev.quality.ocr_confidence,
            overall_quality=ev.quality.overall_quality,
            traceability=ev.traceability.dict(),
            raw_payload=ev.raw_payload or {}
        )
        db.add(ev_db)
        evidence_ids.append(ev.evidence_id)

    await db.commit()

    return EvidenceUploadResponse(
        status="processed",
        document_id=doc_id,
        filename=filename,
        evidence_count=len(evidence_objects),
        evidence_ids=evidence_ids,
        evidence_objects=evidence_objects
    )

@router.post("/evidence/manual", response_model=EvidenceObject)
async def create_manual_evidence(
    req: EvidenceCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually ingest an evidence claim into a case.
    """
    quality = quality_engine.assess_quality(
        source_type=req.source_type,
        explicit_reliability=req.reliability,
        explicit_freshness=req.freshness
    )

    ev_id = normalizer.generate_evidence_id("E-MAN")
    
    ev_obj = EvidenceObject(
        evidence_id=ev_id,
        case_id=req.case_id,
        source=SourceMetadata(
            type=req.source_type,
            system=req.source_system,
            name="Manual Ingestion"
        ),
        claim=ClaimPayload(
            subject=req.claim_subject,
            predicate=req.claim_predicate,
            value=req.claim_value,
            raw_statement=f"{req.claim_predicate} = {req.claim_value}"
        ),
        quality=quality,
        traceability=TraceabilityInfo(
            file="manual_entry",
            table=req.traceability.get("table") if req.traceability else None,
            record_id=req.traceability.get("record_id") if req.traceability else None
        )
    )

    ev_db = EvidenceModel(
        evidence_id=ev_obj.evidence_id,
        case_id=req.case_id,
        source_type=ev_obj.source.type.value,
        source_system=ev_obj.source.system,
        source_reference="Manual Input",
        claim_subject=ev_obj.claim.subject,
        claim_predicate=ev_obj.claim.predicate,
        claim_value=ev_obj.claim.value,
        raw_statement=ev_obj.claim.raw_statement,
        reliability=ev_obj.quality.reliability.value,
        freshness=ev_obj.quality.freshness.value,
        completeness=ev_obj.quality.completeness,
        ocr_confidence=ev_obj.quality.ocr_confidence,
        overall_quality=ev_obj.quality.overall_quality,
        traceability=ev_obj.traceability.dict()
    )
    db.add(ev_db)
    await db.commit()

    return ev_obj

@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceObject])
async def get_case_evidence(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches all normalized Evidence Objects attached to a case.
    """
    result = await db.execute(select(EvidenceModel).where(EvidenceModel.case_id == case_id))
    rows = result.scalars().all()

    evidence_objects = []
    for r in rows:
        ev = EvidenceObject(
            evidence_id=r.evidence_id,
            case_id=r.case_id,
            source=SourceMetadata(
                type=SourceType(r.source_type) if r.source_type in SourceType.__members__ else SourceType.DATABASE,
                system=r.source_system,
                name=r.source_reference
            ),
            claim=ClaimPayload(
                subject=r.claim_subject,
                predicate=r.claim_predicate,
                value=r.claim_value,
                raw_statement=r.raw_statement
            ),
            timestamp=r.timestamp.isoformat() if r.timestamp else "",
            quality=QualityMetrics(
                reliability=ReliabilityLevel(r.reliability) if r.reliability in ReliabilityLevel.__members__ else ReliabilityLevel.HIGH,
                freshness=FreshnessLevel(r.freshness) if r.freshness in FreshnessLevel.__members__ else FreshnessLevel.CURRENT,
                completeness=r.completeness or 1.0,
                ocr_confidence=r.ocr_confidence,
                overall_quality=r.overall_quality or "HIGH"
            ),
            traceability=TraceabilityInfo(**(r.traceability or {})),
            raw_payload=r.raw_payload or {},
            created_at=r.created_at.isoformat() if r.created_at else ""
        )
        evidence_objects.append(ev)

    return evidence_objects
