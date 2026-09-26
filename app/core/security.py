import re
import hashlib
from typing import Tuple

FORBIDDEN_SQL_PATTERNS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCREATE\b",
    r"\bREPLACE\b"
]

def sanitize_readonly_sql(query: str) -> Tuple[bool, str]:
    """
    Enforces enterprise read-only policy for database connectors.
    Ensures VERDICT can only SELECT data and never mutate customer systems.
    """
    cleaned = query.strip()
    if not cleaned:
        return False, "Query cannot be empty"
    
    # Must start with SELECT or WITH
    if not (cleaned.upper().startswith("SELECT") or cleaned.upper().startswith("WITH")):
        return False, "Only SELECT or WITH queries are permitted on enterprise connectors."
    
    for pattern in FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return False, f"Forbidden non-read-only SQL keyword detected: {pattern.replace(r'\b', '')}"
            
    return True, "Query authorized as Read-Only"

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
