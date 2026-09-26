from fastapi import APIRouter
from datetime import datetime

from app.schemas.decision import DecisionPacket
from app.api.analysis import run_case_analysis
from app.services.evidence.normalizer import normalizer
from app.schemas.evidence import SourceType, ReliabilityLevel, FreshnessLevel
from app.db.repository import repo

router = APIRouter(prefix="/api/demo", tags=["Demo Endpoints"])

@router.post("/seed-tx92831", response_model=DecisionPacket)
async def seed_hackathon_demo_tx92831():
    """
    Seeds the full end-to-end Hackathon Demo Case TX92831 into MongoDB:
    - Case: High-Value Wire Transfer (₹85,000)
    - E001 (Core Banking DB): Amount ₹85,000, Location: Mumbai, Time: 10:42 AM
    - E002 (Device Telemetry): Location: Delhi, IP: 103.21.244.2, Device: iPhone 14
    - E003 (KYC Registry PDF/Image): Registered Address: Mumbai, Status: Verified
    - E004 (Account History CSV): Typical Velocity: ₹5,000 - ₹12,000, Home Location: Mumbai
    Automatically triggers full pipeline analysis and returns the finalized DecisionPacket!
    """
    case_id = "CASE-TX92831"

    # 1. Ensure Case exists in MongoDB
    await repo.create_case({
        "case_id": case_id,
        "title": "High-Value Wire Transfer Dispute - TX92831",
        "description": "Suspicious high-value transfer flagged across divergent telemetry streams.",
        "entity_type": "TRANSACTION",
        "entity_id": "TX92831",
        "status": "OPEN"
    })

    # Clear prior evidence for clean demo replay
    await repo.clear_case_evidence(case_id)

    # 2. Add Standardized Traceable Evidence Items to MongoDB
    
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
    ev1_dict = ev1.dict()
    ev1_dict["evidence_id"] = "E-001"
    ev1_dict["claim"]["raw_statement"] = "Transaction initiated at branch terminal in Mumbai for ₹85,000"
    await repo.add_evidence(ev1_dict)

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
    ev2_dict = ev2.dict()
    ev2_dict["evidence_id"] = "E-002"
    ev2_dict["source"]["type"] = "DEVICE_SIGNAL"
    ev2_dict["claim"]["raw_statement"] = "Device session authenticated via Cellular IP in Delhi at 10:41:52 AM"
    ev2_dict["traceability"] = {"ip": "103.21.244.2", "cell_tower_id": "DEL-4102"}
    await repo.add_evidence(ev2_dict)

    # E003: KYC Verification Document (Mumbai)
    ev3_dict = {
        "evidence_id": "E-003",
        "case_id": case_id,
        "source": {
            "type": "IMAGE",
            "system": "UPLOADED_KYC_DOCUMENT",
            "name": "kyc_registration_acae.jpg",
            "reference": "kyc_registration_acae.jpg"
        },
        "claim": {
            "subject": "TX-92831",
            "predicate": "registered_city",
            "value": "Mumbai",
            "raw_statement": "Official Company & KYC registration address: Nariman Point, Mumbai 400021"
        },
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {
            "reliability": "HIGH",
            "freshness": "RECENT",
            "completeness": 0.95,
            "ocr_confidence": 0.96,
            "is_primary_source": False,
            "overall_quality": "HIGH"
        },
        "traceability": {
            "file": "kyc_registration_acae.jpg",
            "page": 1
        }
    }
    await repo.add_evidence(ev3_dict)

    # E004: Account Historical Baseline (Typical ₹5K-12K)
    ev4_dict = {
        "evidence_id": "E-004",
        "case_id": case_id,
        "source": {
            "type": "CSV",
            "system": "HISTORICAL_LEDGER_FEED",
            "name": "account_history_acc992.csv"
        },
        "claim": {
            "subject": "ACC992",
            "predicate": "avg_monthly_transfer_velocity",
            "value": "₹8,400",
            "raw_statement": "Average monthly transfer size over past 180 days is ₹8,400 with 98% Mumbai affinity."
        },
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {
            "reliability": "HIGH",
            "freshness": "CURRENT",
            "completeness": 1.0,
            "is_primary_source": False,
            "overall_quality": "HIGH"
        },
        "traceability": {
            "file": "account_history_acc992.csv",
            "line_number": 42
        }
    }
    await repo.add_evidence(ev4_dict)

    # Run complete analysis pipeline and store in MongoDB
    return await run_case_analysis(case_id=case_id)
