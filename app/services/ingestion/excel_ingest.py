import os
from typing import List
from app.schemas.evidence import EvidenceObject, SourceType
from app.services.evidence.normalizer import normalizer
from app.core.logging import logger

class ExcelIngestionService:
    """
    Ingests Excel (.xlsx, .xls) files using openpyxl / pandas.
    Normalizes spreadsheet rows into structured Evidence Objects.
    """

    def process_excel(self, file_path: str, case_id: str) -> List[EvidenceObject]:
        evidence_list: List[EvidenceObject] = []
        filename = os.path.basename(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found at: {file_path}")

        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                rows = list(sheet.iter_rows(values_only=True))
                if not rows or len(rows) < 2:
                    continue

                headers = [str(h).strip().lower().replace(" ", "_") if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]

                for row_idx, row_values in enumerate(rows[1:], start=2):
                    row_dict = {}
                    for col_idx, val in enumerate(row_values):
                        if col_idx < len(headers):
                            row_dict[headers[col_idx]] = val

                    subject = (
                        row_dict.get("tx_id") or 
                        row_dict.get("transaction_id") or 
                        row_dict.get("account_id") or 
                        row_dict.get("customer_id") or 
                        f"ROW_{row_idx}"
                    )

                    for col_key, val in row_dict.items():
                        if val is not None and str(val).strip() != "":
                            evidence = normalizer.from_tabular_row(
                                case_id=case_id,
                                filename=f"{filename}#{sheet_name}",
                                row_idx=row_idx,
                                subject=str(subject),
                                predicate=col_key,
                                value=str(val).strip(),
                                source_type=SourceType.EXCEL,
                                raw_row_dict=row_dict
                            )
                            evidence_list.append(evidence)

            logger.info(f"Successfully processed Excel {filename}: generated {len(evidence_list)} evidence objects.")
            return evidence_list

        except Exception as e:
            logger.error(f"Error processing Excel file {filename}: {e}")
            raise e

excel_ingest = ExcelIngestionService()
