import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import ConnectorModel, EvidenceModel
from app.schemas.connector import ConnectorConfig, ConnectorTestResult, QueryPayload
from app.schemas.evidence import EvidenceObject
from app.services.ingestion.gateway import ingestion_gateway
from app.core.logging import logger

router = APIRouter(prefix="/api/connectors", tags=["Connectors"])

@router.post("", response_model=ConnectorConfig)
async def register_connector(config: ConnectorConfig, db: AsyncSession = Depends(get_db)):
    conn_id = config.id or f"CONN-{uuid.uuid4().hex[:6].upper()}"
    
    model = ConnectorModel(
        connector_id=conn_id,
        name=config.name,
        connector_type=config.connector_type.value,
        config_json=config.dict(),
        read_only=True,
        is_active=True
    )
    db.add(model)
    await db.commit()
    config.id = conn_id
    return config

@router.get("", response_model=List[ConnectorConfig])
async def list_connectors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConnectorModel))
    rows = result.scalars().all()
    
    connectors = []
    for r in rows:
        cfg = ConnectorConfig(**r.config_json)
        cfg.id = r.connector_id
        connectors.append(cfg)
    return connectors

@router.post("/test", response_model=ConnectorTestResult)
async def test_connector(config: ConnectorConfig):
    """
    Validates read-only connection to external DB / Edge Gateway.
    """
    return ingestion_gateway.test_connection(config)

@router.post("/{connector_id}/query", response_model=List[EvidenceObject])
async def query_connector(
    connector_id: str,
    payload: QueryPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes an authorized read-only query against the connector and normalizes results into case evidence.
    """
    result = await db.execute(select(ConnectorModel).where(ConnectorModel.connector_id == connector_id))
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found.")

    cfg = ConnectorConfig(**row.config_json)
    evidence_items = ingestion_gateway.fetch_targeted_evidence(
        case_id=payload.case_id,
        connector_config=cfg,
        query_string=payload.query_string
    )

    # Save to database
    for ev in evidence_items:
        ev_db = EvidenceModel(
            evidence_id=ev.evidence_id,
            case_id=payload.case_id,
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
        db.add(ev_db)

    await db.commit()
    return evidence_items
