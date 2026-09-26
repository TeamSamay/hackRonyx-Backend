import os
from typing import List
from app.schemas.evidence import EvidenceObject
from app.services.ingestion.pdf_ingest import pdf_ingest
from app.services.ingestion.image_ingest import image_ingest
from app.services.ingestion.csv_ingest import csv_ingest
from app.services.ingestion.excel_ingest import excel_ingest
from app.core.logging import logger

class DocumentParser:
    """
    Unified Document and File Ingestion Dispatcher.
    Detects file format and routes to the appropriate pipeline.
    """

    def parse_file(self, file_path: str, case_id: str) -> List[EvidenceObject]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        logger.info(f"Parsing file {file_path} with extension {ext} for case {case_id}")

        if ext == ".pdf":
            return pdf_ingest.process_pdf(file_path, case_id)
        elif ext in [".csv", ".tsv"]:
            return csv_ingest.process_csv(file_path, case_id)
        elif ext in [".xlsx", ".xls"]:
            return excel_ingest.process_excel(file_path, case_id)
        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            return image_ingest.process_image(file_path, case_id)
        elif ext in [".txt", ".json", ".log"]:
            return csv_ingest.process_csv(file_path, case_id)
        else:
            logger.warning(f"Unsupported file extension {ext}, treating as image/generic document.")
            return image_ingest.process_image(file_path, case_id)

document_parser = DocumentParser()
