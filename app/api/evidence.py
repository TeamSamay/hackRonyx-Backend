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

@router.post("/evidence/upload-multiple")
async def upload_multiple_evidence_files(
    files: List[UploadFile] = File(...),
    case_id: str = Form(...)
):
    """
    Batch multi-file upload API:
    Upload and parse multiple PDF/CSV/Excel/Image documents simultaneously.
    """
    case = await repo.get_case(case_id)
    if not case:
        await repo.create_case({
            "case_id": case_id,
            "title": f"Case {case_id}",
            "description": "Auto-created case from multi-file upload.",
            "entity_type": "ORGANIZATION",
            "entity_id": case_id,
            "status": "OPEN"
        })

    results = []
    all_evidence = []

    for file in files:
        doc_id = f"DOC-{uuid.uuid4().hex[:6].upper()}"
        filename = file.filename or "uploaded_file"
        file_ext = os.path.splitext(filename)[1].lower()
        save_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(save_path)

        # Parse document
        evidence_objects = document_parser.parse_file(save_path, case_id)
        evidence_ids = []
        for ev in evidence_objects:
            await repo.add_evidence(ev.dict())
            evidence_ids.append(ev.evidence_id)
            all_evidence.append(ev)

        # Save document in MongoDB
        doc_record = {
            "document_id": doc_id,
            "case_id": case_id,
            "filename": filename,
            "file_type": file_ext.replace(".", "").upper(),
            "file_path": save_path,
            "file_size_bytes": file_size,
            "evidence_count": len(evidence_objects),
            "status": "PROCESSED"
        }
        await repo.create_document(doc_record)
        results.append(doc_record)

    return {
        "status": "SUCCESS",
        "case_id": case_id,
        "files_processed": len(results),
        "documents": results,
        "total_evidence_count": len(all_evidence),
        "evidence_objects": all_evidence
    }

@router.get("/cases/{case_id}/documents")
async def get_case_documents(case_id: str):
    """
    Fetches all uploaded and processed documents for a company/case from MongoDB.
    """
    docs = await repo.get_case_documents(case_id)
    return {
        "case_id": case_id,
        "count": len(docs),
        "documents": docs
    }

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

@router.post("/evidence/search-web")
async def search_and_ingest_web_evidence(
    query: str = Form(...),
    case_id: Optional[str] = Form("CASE-TX92831")
):
    """
    Real-Time Web Search & Live Evidence Ingestion API:
    Searches the live web, extracts claim snippets, and indexes into RAG vector store & evidence repository.
    """
    from app.services.ingestion.web_search import web_search_service
    evidence_list = await web_search_service.fetch_and_index_web_evidence(query, case_id)
    
    # Store evidence objects in MongoDB
    for ev in evidence_list:
        try:
            await repo.add_evidence(ev.dict())
        except Exception:
            pass

    return {
        "status": "SUCCESS",
        "query": query,
        "evidence_count": len(evidence_list),
        "evidence_objects": evidence_list
    }

@router.post("/evidence/remote-vault/sync")
async def sync_remote_vault_documents(
    vault_url: str = Form(...),
    case_id: str = Form("CASE-TX92831")
):
    """
    Connects to remote branch vault (e.g. Laptop 2 via Ngrok URL),
    downloads all documents over HTTP, parses them with OCR, and indexes into case.
    """
    clean_url = vault_url.strip().rstrip("/")
    import httpx
    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            docs_resp = await client.get(f"{clean_url}/api/documents")
            if docs_resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Remote vault returned status {docs_resp.status_code}")
            vault_data = docs_resp.json()
            remote_docs = vault_data.get("documents", [])

            results = []
            all_evidence = []
            for r_doc in remote_docs:
                dl_path = r_doc.get("download_url", "")
                fname = r_doc.get("filename", "remote_file.pdf")
                file_url = f"{clean_url}{dl_path}" if dl_path.startswith("/") else f"{clean_url}/{dl_path}"

                file_resp = await client.get(file_url)
                if file_resp.status_code == 200:
                    doc_id = f"DOC-REM-{uuid.uuid4().hex[:6].upper()}"
                    save_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{fname}")
                    with open(save_path, "wb") as f:
                        f.write(file_resp.content)

                    file_size = os.path.getsize(save_path)
                    file_ext = os.path.splitext(fname)[1].lower()

                    evidence_objects = document_parser.parse_file(save_path, case_id)
                    for ev in evidence_objects:
                        await repo.add_evidence(ev.dict())
                        all_evidence.append(ev)

                    doc_record = {
                        "document_id": doc_id,
                        "case_id": case_id,
                        "filename": f"{fname} (Remote Vault)",
                        "file_type": file_ext.replace(".", "").upper(),
                        "file_path": save_path,
                        "file_size_bytes": file_size,
                        "evidence_count": len(evidence_objects),
                        "status": "INGESTED & VERIFIED",
                        "sha256": r_doc.get("sha256")
                    }
                    await repo.create_document(doc_record)
                    results.append(doc_record)

            return {
                "status": "SUCCESS",
                "remote_vault_url": clean_url,
                "branch_id": vault_data.get("branch_id", "BRANCH-REMOTE-01"),
                "files_synced": len(results),
                "documents": results,
                "evidence_count": len(all_evidence)
            }
    except Exception as e:
        logger.error(f"Failed to sync remote vault: {e}")
        raise HTTPException(status_code=500, detail=f"Remote vault connection failed: {str(e)}")

