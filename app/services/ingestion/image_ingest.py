import os
from typing import List
from app.schemas.evidence import EvidenceObject, SourceType
from app.services.evidence.normalizer import normalizer
from app.services.ocr.engine import ocr_engine
from app.core.logging import logger

class ImageIngestionService:
    """
    Ingests image documents (PNG, JPG, JPEG), runs OCR, extracts key-value pairs/claims,
    and returns standardized Evidence objects with OCR confidence metrics.
    """

    def process_image(self, file_path: str, case_id: str) -> List[EvidenceObject]:
        evidence_list: List[EvidenceObject] = []
        filename = os.path.basename(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found at: {file_path}")

        try:
            ocr_text, confidence = ocr_engine.extract_text_from_image(file_path)
            lines = [line.strip() for line in ocr_text.split("\n") if line.strip()]

            subject = filename.rsplit(".", 1)[0]
            for line in lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    predicate = parts[0].strip().lower().replace(" ", "_")
                    value = parts[1].strip()
                else:
                    predicate = "image_extracted_text"
                    value = line

                evidence = normalizer.from_document_text(
                    case_id=case_id,
                    filename=filename,
                    page_num=1,
                    subject=subject,
                    predicate=predicate,
                    value=value,
                    doc_type=SourceType.IMAGE,
                    raw_statement=line,
                    ocr_confidence=confidence
                )
                evidence_list.append(evidence)

            logger.info(f"Successfully processed image {filename}: OCR confidence {confidence}, generated {len(evidence_list)} evidence objects.")
            return evidence_list

        except Exception as e:
            logger.error(f"Error processing image {filename}: {e}")
            raise e

image_ingest = ImageIngestionService()
