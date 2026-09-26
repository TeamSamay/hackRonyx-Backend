import uuid
from typing import List
from fastapi import APIRouter, HTTPException

from app.schemas.connector import ConnectorConfig, ConnectorTestResult, QueryPayload
from app.schemas.evidence import EvidenceObject
from app.services.ingestion.gateway import ingestion_gateway
from app.db.repository import repo
from app.core.logging import logger

router = APIRouter(prefix="/api/connectors", tags=["Connectors"])

@router.post("", response_model=ConnectorConfig)
async def register_connector(config: ConnectorConfig):
    conn_id = config.id or f"CONN-{uuid.uuid4().hex[:6].upper()}"
    config.id = conn_id
    
    await repo.save_connector({
        "connector_id": conn_id,
        "name": config.name,
        "connector_type": config.connector_type.value,
        "config": config.dict(),
        "read_only": True,
        "is_active": True
    })
    return config

@router.get("", response_model=List[ConnectorConfig])
async def list_connectors():
    rows = await repo.list_connectors()
    return [ConnectorConfig(**r["config"]) for r in rows if "config" in r]

@router.post("/test", response_model=ConnectorTestResult)
async def test_connector(config: ConnectorConfig):
    """
    Validates read-only connection to external DB / Edge Gateway.
    """
    return ingestion_gateway.test_connection(config)

@router.post("/{connector_id}/query", response_model=List[EvidenceObject])
async def query_connector(
    connector_id: str,
    payload: QueryPayload
):
    """
    Executes an authorized read-only query against the connector and normalizes results into MongoDB case evidence.
    """
    row = await repo.get_connector(connector_id)
    if not row or "config" not in row:
        raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found.")

    cfg = ConnectorConfig(**row["config"])
    evidence_items = ingestion_gateway.fetch_targeted_evidence(
        case_id=payload.case_id,
        connector_config=cfg,
        query_string=payload.query_string
    )

    # Save to MongoDB
    for ev in evidence_items:
        await repo.add_evidence(ev.dict())

    return evidence_items
