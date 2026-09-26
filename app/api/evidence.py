import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks

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
from app.db.repository import repo
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/api", tags=["Evidence"])

@router.post("/evidence/upload", response_model=EvidenceUploadResponse)
async def upload_evidence_file(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    source_type: Optional[str] = Form(None)
):
    """
    Multi-format file upload API:
    Supports PDF, CSV, XLSX, PNG, JPG, JPEG, TXT, DOCX.
    Extracts text, applies OCR if needed, normalizes claims into Evidence objects, stores in MongoDB.
    """
    # 1. Ensure case exists in MongoDB
    case = await repo.get_case(case_id)
    if not case:
        await repo.create_case({
            "case_id": case_id,
            "title": f"Case {case_id}",
            "description": "Auto-created case from file upload.",
            "entity_type": "TRANSACTION",
            "entity_id": case_id,
            "status": "OPEN"
        })

    # 2. Save file to storage
    doc_id = f"DOC-{uuid.uuid4().hex[:6].upper()}"
    filename = file.filename or "uploaded_file"
    file_ext = os.path.splitext(filename)[1].lower()
    save_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(save_path)

    # 3. Create Document DB record in MongoDB
    await repo.create_document({
        "document_id": doc_id,
        "case_id": case_id,
        "filename": filename,
        "file_type": file_ext.replace(".", "").upper(),
        "file_path": save_path,
        "file_size_bytes": file_size,
        "status": "PROCESSED"
    })

    # 4. Synchronously parse for immediate availability
    evidence_objects = document_parser.parse_file(save_path, case_id)

    evidence_ids = []
    for ev in evidence_objects:
        await repo.add_evidence(ev.dict())
        evidence_ids.append(ev.evidence_id)

    return EvidenceUploadResponse(
        status="processed",
        document_id=doc_id,
        filename=filename,
        evidence_count=len(evidence_objects),
        evidence_ids=evidence_ids,
        evidence_objects=evidence_objects
    )

@router.post("/evidence/manual", response_model=EvidenceObject)
async def create_manual_evidence(req: EvidenceCreateRequest):
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

    await repo.add_evidence(ev_obj.dict())
    return ev_obj

@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceObject])
async def get_case_evidence(case_id: str):
    """
    Fetches all normalized Evidence Objects attached to a case from MongoDB.
    """
    raw_evidence = await repo.get_case_evidence(case_id)
    return [EvidenceObject(**r) for r in raw_evidence]
