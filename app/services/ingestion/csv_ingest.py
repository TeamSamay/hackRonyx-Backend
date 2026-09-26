import csv
import os
from typing import List
from app.schemas.evidence import EvidenceObject, SourceType
from app.services.evidence.normalizer import normalizer
from app.core.logging import logger

class CSVIngestionService:
    """
    Ingests CSV files, automatically maps schema headers to predicates,
    and normalizes every record into standard Evidence Objects.
    """

    def process_csv(self, file_path: str, case_id: str) -> List[EvidenceObject]:
        evidence_list: List[EvidenceObject] = []
        filename = os.path.basename(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found at: {file_path}")

        try:
            with open(file_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                row_idx = 1
                for row in reader:
                    # Determine primary subject (e.g. tx_id, account_id, customer_id or fallback to row index)
                    subject = (
                        row.get("tx_id") or 
                        row.get("transaction_id") or 
                        row.get("id") or 
                        row.get("account_id") or 
                        row.get("user_id") or 
                        f"ROW_{row_idx}"
                    )

                    for col_name, col_value in row.items():
                        if col_name and col_value and col_name.strip() != "":
                            # Clean field names
                            predicate = col_name.strip().lower().replace(" ", "_")
                            evidence = normalizer.from_tabular_row(
                                case_id=case_id,
                                filename=filename,
                                row_idx=row_idx,
                                subject=str(subject),
                                predicate=predicate,
                                value=col_value.strip(),
                                source_type=SourceType.CSV,
                                raw_row_dict=dict(row)
                            )
                            evidence_list.append(evidence)
                    row_idx += 1

            logger.info(f"Successfully processed CSV {filename}: generated {len(evidence_list)} evidence objects.")
            return evidence_list

        except Exception as e:
            logger.error(f"Error processing CSV {filename}: {e}")
            raise e

csv_ingest = CSVIngestionService()
