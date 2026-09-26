import os
from typing import List
from app.db.session import async_session
from app.db.models import DocumentModel, EvidenceModel, DecisionModel, CaseModel
from app.services.documents.parser import document_parser
from app.core.logging import logger

async def process_document_background(file_path: str, case_id: str, document_id: str):
    """
    Background worker task to parse uploaded files without blocking the API request.
    Extracts text/OCR, creates evidence objects, and saves them to the database.
    """
    logger.info(f"Background task started for document {document_id} (case: {case_id})")
    try:
        evidence_objects = document_parser.parse_file(file_path, case_id)
        
        async with async_session() as session:
            # Store extracted evidence in DB
            for ev in evidence_objects:
                ev_db = EvidenceModel(
                    evidence_id=ev.evidence_id,
                    case_id=case_id,
                    source_type=ev.source.type.value,
                    source_system=ev.source.system,
                    source_reference=ev.source.reference or ev.source.name,
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
                session.add(ev_db)

            # Update document status
            doc = await session.get(DocumentModel, document_id)
            if doc:
                doc.status = "COMPLETED"
                doc.ocr_applied = any(ev.quality.ocr_confidence is not None for ev in evidence_objects)
            
            await session.commit()
            logger.info(f"Background processing completed for doc {document_id}: inserted {len(evidence_objects)} evidence records.")

    except Exception as e:
        logger.error(f"Background processing error for document {document_id}: {e}")
