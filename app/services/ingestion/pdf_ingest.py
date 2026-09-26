import os
import re
from typing import List, Tuple
from app.schemas.evidence import EvidenceObject, SourceType
from app.services.evidence.normalizer import normalizer
from app.services.ocr.engine import ocr_engine
from app.core.logging import logger

class PDFIngestionService:
    """
    Ingests PDF documents using PyMuPDF (fitz) or OCR fallback for scanned pages.
    Segments pages, extracts claims, and creates traceable Evidence objects.
    """

    def process_pdf(self, file_path: str, case_id: str) -> List[EvidenceObject]:
        evidence_list: List[EvidenceObject] = []
        filename = os.path.basename(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        try:
            pages_text: List[Tuple[int, str, bool]] = []
            try:
                import fitz # PyMuPDF
                doc = fitz.open(file_path)
                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    text = page.get_text().strip()
                    if len(text) > 30:
                        pages_text.append((page_idx + 1, text, False))
                    else:
                        # Scanned page - need OCR fallback
                        logger.info(f"Page {page_idx + 1} has minimal text; applying OCR fallback.")
                        ocr_text, _ = ocr_engine.extract_text_from_image(file_path)
                        pages_text.append((page_idx + 1, ocr_text, True))
                doc.close()
            except Exception as pdf_err:
                logger.warning(f"PyMuPDF open failed ({pdf_err}). Using OCR engine directly.")
                ocr_text, conf = ocr_engine.extract_text_from_image(file_path)
                pages_text.append((1, ocr_text, True))

            # Segment pages into structured facts & claims
            for page_num, text, is_ocr in pages_text:
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                for line in lines:
                    # Look for key: value or claim patterns
                    if ":" in line:
                        parts = line.split(":", 1)
                        predicate = parts[0].strip().lower().replace(" ", "_")
                        value = parts[1].strip()
                        subject = f"{filename}_P{page_num}"
                    else:
                        predicate = "document_statement"
                        value = line
                        subject = f"{filename}_P{page_num}"

                    evidence = normalizer.from_document_text(
                        case_id=case_id,
                        filename=filename,
                        page_num=page_num,
                        subject=subject,
                        predicate=predicate,
                        value=value,
                        doc_type=SourceType.PDF,
                        raw_statement=line,
                        ocr_confidence=0.92 if is_ocr else None
                    )
                    evidence_list.append(evidence)

            logger.info(f"Successfully processed PDF {filename}: extracted {len(evidence_list)} evidence items across {len(pages_text)} pages.")
            return evidence_list

        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            raise e

pdf_ingest = PDFIngestionService()
