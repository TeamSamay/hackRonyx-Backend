from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class ConnectorType(str, Enum):
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    CSV_DIRECTORY = "CSV_DIRECTORY"
    EXCEL_FILE = "EXCEL_FILE"
    REST_API = "REST_API"

class ConnectorConfig(BaseModel):
    id: Optional[str] = None
    name: str
    connector_type: ConnectorType
    host: Optional[str] = "localhost"
    port: Optional[int] = 5432
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    file_path: Optional[str] = None
    api_endpoint: Optional[str] = None
    read_only: bool = True
    is_active: bool = True

class ConnectorTestResult(BaseModel):
    success: bool
    message: str
    sample_records_count: int = 0
    sample_columns: List[str] = []

class QueryPayload(BaseModel):
    connector_id: str
    case_id: str
    query_string: str = Field(..., description="Targeted SELECT query e.g. SELECT * FROM transactions WHERE tx_id = 'TX92831'")
