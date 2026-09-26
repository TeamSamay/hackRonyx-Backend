from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.db.session import get_db
from app.db.models import CaseModel, EvidenceModel, ConnectorModel
from app.schemas.decision import DecisionPacket
from app.api.analysis import run_case_analysis
from app.services.evidence.normalizer import normalizer
from app.schemas.evidence import SourceType, ReliabilityLevel, FreshnessLevel

router = APIRouter(prefix="/api/demo", tags=["Demo Endpoints"])

@router.post("/seed-tx92831", response_model=DecisionPacket)
async def seed_hackathon_demo_tx92831(db: AsyncSession = Depends(get_db)):
    """
    Seeds the full end-to-end Hackathon Demo Case TX92831:
    - Case: High-Value Wire Transfer (₹85,000)
    - E001 (Core Banking DB): Amount ₹85,000, Location: Mumbai, Time: 10:42 AM
    - E002 (Device Telemetry): Location: Delhi, IP: 103.21.244.2, Device: iPhone 14
    - E003 (KYC Registry PDF/Image): Registered Address: Mumbai, Status: Verified
    - E004 (Account History CSV): Typical Velocity: ₹5,000 - ₹12,000, Home Location: Mumbai
    Automatically triggers full pipeline analysis and returns the finalized DecisionPacket!
    """
    case_id = "CASE-TX92831"

    # 1. Ensure Case exists
    case_res = await db.execute(select(CaseModel).where(CaseModel.case_id == case_id))
    case = case_res.scalars().first()
    if not case:
        case = CaseModel(
            case_id=case_id,
            title="High-Value Wire Transfer Dispute - TX92831",
            description="Suspicious high-value transfer flagged across divergent telemetry streams.",
            entity_type="TRANSACTION",
            entity_id="TX92831",
            status="OPEN"
        )
        db.add(case)
        await db.commit()

    # Clear prior evidence for clean demo replay
    existing_ev = await db.execute(select(EvidenceModel).where(EvidenceModel.case_id == case_id))
    for ev in existing_ev.scalars().all():
        await db.delete(ev)
    await db.commit()

    # 2. Add Standardized Traceable Evidence Items
    
    # E001: Core Banking Transaction DB
    ev1 = normalizer.from_database_record(
        case_id=case_id,
        table_name="transactions",
        record_id="TX-92831",
        subject="TX-92831",
        predicate="transaction_location",
        value="Mumbai",
        system_name="BANK_TRANSACTION_DB",
        reliability=ReliabilityLevel.HIGH,
        raw_payload={"amount": 85000, "currency": "INR", "account": "ACC992", "location": "Mumbai", "timestamp": "2026-09-26T10:42:00"}
    )
    ev1_db = EvidenceModel(
        evidence_id="E-001",
        case_id=case_id,
        source_type=ev1.source.type.value,
        source_system=ev1.source.system,
        source_reference="transactions:TX-92831",
        claim_subject="TX-92831",
        claim_predicate="transaction_location",
        claim_value="Mumbai",
        raw_statement="Transaction initiated at branch terminal in Mumbai for ₹85,000",
        reliability="HIGH",
        freshness="CURRENT",
        completeness=1.0,
        overall_quality="HIGH",
        traceability={"table": "transactions", "record_id": "TX-92831"},
        raw_payload=ev1.raw_payload
    )
    db.add(ev1_db)

    # E002: Device Telemetry (Delhi mismatch)
    ev2 = normalizer.from_database_record(
        case_id=case_id,
        table_name="device_telemetry",
        record_id="DEV-92831",
        subject="TX-92831",
        predicate="device_location",
        value="Delhi",
        system_name="MOBILE_TELEMETRY_DB",
        reliability=ReliabilityLevel.HIGH,
        raw_payload={"ip": "103.21.244.2", "device_model": "iPhone 14", "location": "Delhi"}
    )
    ev2_db = EvidenceModel(
        evidence_id="E-002",
        case_id=case_id,
        source_type="DEVICE_SIGNAL",
        source_system="MOBILE_TELEMETRY_DB",
        source_reference="telemetry_stream:DEV-92831",
        claim_subject="TX-92831",
        claim_predicate="device_location",
        claim_value="Delhi",
        raw_statement="Device session authenticated via Cellular IP in Delhi at 10:41:52 AM",
        reliability="HIGH",
        freshness="CURRENT",
        completeness=1.0,
        overall_quality="HIGH",
        traceability={"ip": "103.21.244.2", "cell_tower_id": "DEL-4102"},
        raw_payload=ev2.raw_payload
    )
    db.add(ev2_db)

    # E003: KYC Verification Document (Mumbai)
    ev3_db = EvidenceModel(
        evidence_id="E-003",
        case_id=case_id,
        source_type="IMAGE",
        source_system="UPLOADED_KYC_DOCUMENT",
        source_reference="kyc_registration_acae.jpg",
        claim_subject="TX-92831",
        claim_predicate="registered_city",
        claim_value="Mumbai",
        raw_statement="Official Company & KYC registration address: Nariman Point, Mumbai 400021",
        reliability="HIGH",
        freshness="RECENT",
        completeness=0.95,
        ocr_confidence=0.96,
        overall_quality="HIGH",
        traceability={"file": "kyc_registration_acae.jpg", "page": 1, "ocr_engine": "Tesseract-v5"}
    )
    db.add(ev3_db)

    # E004: Account Historical Baseline (Typical ₹5K-12K)
    ev4_db = EvidenceModel(
        evidence_id="E-004",
        case_id=case_id,
        source_type="CSV",
        source_system="HISTORICAL_LEDGER_FEED",
        source_reference="account_history_acc992.csv",
        claim_subject="ACC992",
        claim_predicate="avg_monthly_transfer_velocity",
        claim_value="₹8,400",
        raw_statement="Average monthly transfer size over past 180 days is ₹8,400 with 98% Mumbai affinity.",
        reliability="HIGH",
        freshness="CURRENT",
        completeness=1.0,
        overall_quality="HIGH",
        traceability={"file": "account_history_acc992.csv", "line_number": 42}
    )
    db.add(ev4_db)

    await db.commit()

    # Run complete analysis pipeline
    return await run_case_analysis(case_id=case_id, db=db)
