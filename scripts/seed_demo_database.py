import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL") or "mongodb://localhost:27017"
DB_NAME = os.getenv("MONGODB_DB_NAME", "verdict_db")

async def seed_database():
    print(f"Connecting to MongoDB Atlas at: {MONGODB_URI} ...")
    client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    db = client[DB_NAME]

    await client.admin.command('ping')
    print("[OK] Connected to MongoDB Atlas successfully!")

    # Clear existing collections for a pristine, beautiful demo state
    await db.cases.delete_many({})
    await db.evidence.delete_many({})
    await db.decisions.delete_many({})
    await db.reviews.delete_many({})
    await db.documents.delete_many({})
    await db.connectors.delete_many({})

    print("[*] Seeding Comprehensive Multi-Domain Evidence & Decisions...")

    # =========================================================================
    # CASE 1: BANKING — Transaction Dispute (CONFLICTING -> HUMAN_REVIEW)
    # =========================================================================
    case1 = {
        "case_id": "CASE-TX92831",
        "title": "High-Value Wire Transfer Dispute - TX-92831",
        "description": "Suspicious high-value transfer flagged across divergent physical branch terminal and cellular telemetry streams.",
        "entity_type": "TRANSACTION",
        "entity_id": "TX-92831",
        "status": "OPEN",
        "trust_status": "CONFLICTING",
        "initial_metadata": {"amount": 85000, "currency": "INR", "account": "ACC-92831"},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    await db.cases.insert_one(case1)

    ev1_1 = {
        "evidence_id": "E-001",
        "case_id": "CASE-TX92831",
        "source": {"type": "DATABASE", "system": "CORE_BANKING_DB", "name": "transactions:TX-92831"},
        "claim": {"subject": "TX-92831", "predicate": "transaction_location", "value": "Mumbai", "raw_statement": "Transaction initiated at branch terminal in Mumbai for ₹85,000", "confidence": 1.0},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "is_primary_source": True, "overall_quality": "HIGH"},
        "traceability": {"table": "transactions", "record_id": "TX-92831", "line_number": 1042},
        "created_at": datetime.utcnow().isoformat()
    }
    ev1_2 = {
        "evidence_id": "E-002",
        "case_id": "CASE-TX92831",
        "source": {"type": "DEVICE_SIGNAL", "system": "MOBILE_TELEMETRY_DB", "name": "telemetry_stream:DEV-92831"},
        "claim": {"subject": "TX-92831", "predicate": "device_location", "value": "Delhi", "raw_statement": "Device session authenticated via Cellular IP in Delhi at 10:41:52 AM", "confidence": 0.98},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "is_primary_source": True, "overall_quality": "HIGH"},
        "traceability": {"ip": "103.21.244.2", "cell_tower_id": "DEL-4102"},
        "created_at": datetime.utcnow().isoformat()
    }
    ev1_3 = {
        "evidence_id": "E-003",
        "case_id": "CASE-TX92831",
        "source": {"type": "IMAGE", "system": "UPLOADED_KYC_DOCUMENT", "name": "kyc_registration_acae.jpg"},
        "claim": {"subject": "TX-92831", "predicate": "registered_city", "value": "Mumbai", "raw_statement": "Official Company & KYC registration address: Nariman Point, Mumbai 400021", "confidence": 0.96},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "HIGH", "freshness": "RECENT", "completeness": 0.95, "ocr_confidence": 0.96, "is_primary_source": False, "overall_quality": "HIGH"},
        "traceability": {"file": "kyc_registration_acae.jpg", "page": 1},
        "created_at": datetime.utcnow().isoformat()
    }
    ev1_4 = {
        "evidence_id": "E-004",
        "case_id": "CASE-TX92831",
        "source": {"type": "CSV", "system": "HISTORICAL_LEDGER_FEED", "name": "account_history_acc992.csv"},
        "claim": {"subject": "ACC-92831", "predicate": "avg_monthly_transfer_velocity", "value": "₹8,400", "raw_statement": "Average monthly transfer size over past 180 days is ₹8,400 with 98% Mumbai affinity.", "confidence": 1.0},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "is_primary_source": False, "overall_quality": "HIGH"},
        "traceability": {"file": "account_history_acc992.csv", "line_number": 42},
        "created_at": datetime.utcnow().isoformat()
    }
    await db.evidence.insert_many([ev1_1, ev1_2, ev1_3, ev1_4])

    dec1 = {
        "case_id": "CASE-TX92831",
        "trust_status": "CONFLICTING",
        "fraud_model": {
            "risk_score": 0.91,
            "model": "XGBoost",
            "anomaly_score": 0.88,
            "feature_contributions": {
                "transaction_amount_velocity": 0.35,
                "unusual_device_telemetry": 0.28,
                "geo_ip_distance_anomaly": 0.22,
                "prior_account_baseline": 0.06
            }
        },
        "evidence_quality": "HIGH",
        "completeness": 1.0,
        "evidence": [ev1_1, ev1_2, ev1_3, ev1_4],
        "claims": [
            {"evidence_id": "E-001", "subject": "TX-92831", "predicate": "transaction_location", "value": "Mumbai"},
            {"evidence_id": "E-002", "subject": "TX-92831", "predicate": "device_location", "value": "Delhi"}
        ],
        "contradictions": [
            {
                "contradiction_id": "CONTRA-LOC-01",
                "evidence_ids": ["E-001", "E-002"],
                "subject": "TX-92831",
                "predicate": "geo_spatial_presence",
                "conflicting_values": ["Mumbai", "Delhi"],
                "severity": "CRITICAL",
                "description": "Physical & Telemetry Location Clash: Transaction occurred in 'Mumbai' branch while mobile device authenticated from 'Delhi' within 8 seconds. Spatio-temporal impossibility confirms high spoofing risk.",
                "resolution_suggestion": "Dispatch out-of-band interactive biometric OTP confirmation."
            }
        ],
        "missing_information": [
            {
                "item": "device_ownership_verification",
                "reason": "Device location and IMEI cannot be conclusively linked to primary registered account holder.",
                "priority": "HIGH",
                "suggested_source": "TELECOM_CARRIER_API / MOBILE_AUTHENTICATOR"
            }
        ],
        "reasoning": "Case CASE-TX92831 exhibits an elevated statistical ML risk score of 0.91 coupled with an unresolved geographical contradiction between physical branch presence in Mumbai and cellular telemetry in Delhi.\n\nWhile core KYC documents establish account legitimacy, the immediate conflict in location endpoints prohibits automated clearing.\n\nIn strict accordance with VERDICT's Deterministic Decision Gate rules, automatic clearance is withheld and human intervention is mandated.",
        "challenge": {
            "performed": True,
            "hypothesis": "Transaction is fraudulent due to location/device anomaly.",
            "counter_evidence_found": False,
            "counter_evidence_ids": [],
            "challenge_summary": "Adversarial counter-evidence scan completed. No mitigating device updates, travel authorizations, or secondary delegate flags were found.",
            "original_risk_state": "HIGH_RISK",
            "adjusted_risk_state": "HIGH_RISK_CONFIRMED"
        },
        "recommendation": "HUMAN_REVIEW",
        "audit": {
            "timestamp": datetime.utcnow().isoformat(),
            "engine_version": "2.0.0",
            "gate": "DETERMINISTIC_DECISION_GATE"
        }
    }
    await db.decisions.insert_one({"case_id": "CASE-TX92831", "trust_status": "CONFLICTING", "packet": dec1, "created_at": datetime.utcnow().isoformat()})

    # =========================================================================
    # CASE 2: INSURANCE — Total Loss Vehicle Claim (SUFFICIENT -> APPROVE)
    # =========================================================================
    case2 = {
        "case_id": "CASE-CLAIM782",
        "title": "Vehicle Collision Total Loss Claim - CLAIM-782",
        "description": "Comprehensive insurance settlement review for severe expressway collision with multiple aligned police and repair records.",
        "entity_type": "INSURANCE_CLAIM",
        "entity_id": "CLAIM-782",
        "status": "OPEN",
        "trust_status": "SUFFICIENT",
        "initial_metadata": {"policy_id": "POL-98214", "claim_amount": 320000},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    await db.cases.insert_one(case2)

    ev2_1 = {
        "evidence_id": "E-101",
        "case_id": "CASE-CLAIM782",
        "source": {"type": "PDF", "system": "CLAIMS_PORTAL", "name": "notice_of_loss_782.pdf"},
        "claim": {"subject": "CLAIM-782", "predicate": "incident_location", "value": "Pune Expressway KM-42", "raw_statement": "Accident occurred on Pune Expressway KM-42 at 22:30 hours", "confidence": 1.0},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "is_primary_source": True, "overall_quality": "HIGH"},
        "traceability": {"file": "notice_of_loss_782.pdf", "page": 1},
        "created_at": datetime.utcnow().isoformat()
    }
    ev2_2 = {
        "evidence_id": "E-102",
        "case_id": "CASE-CLAIM782",
        "source": {"type": "PDF", "system": "POLICE_RECORDS_API", "name": "police_fir_88219.pdf"},
        "claim": {"subject": "CLAIM-782", "predicate": "police_verification", "value": "VERIFIED_ACCIDENTAL", "raw_statement": "Police FIR-88219 verifies multi-vehicle collision with no foul play or intoxication.", "confidence": 1.0},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "is_primary_source": True, "overall_quality": "HIGH"},
        "traceability": {"file": "police_fir_88219.pdf", "page": 2},
        "created_at": datetime.utcnow().isoformat()
    }
    ev2_3 = {
        "evidence_id": "E-103",
        "case_id": "CASE-CLAIM782",
        "source": {"type": "DATABASE", "system": "AUTHORIZED_GARAGE_DB", "name": "assessment:AST-782"},
        "claim": {"subject": "CLAIM-782", "predicate": "repair_estimate", "value": "₹3,20,000", "raw_statement": "Garage chassis structural damage estimate equals ₹3,20,000", "confidence": 1.0},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "is_primary_source": True, "overall_quality": "HIGH"},
        "traceability": {"table": "garage_assessments", "record_id": "AST-782"},
        "created_at": datetime.utcnow().isoformat()
    }
    await db.evidence.insert_many([ev2_1, ev2_2, ev2_3])

    dec2 = {
        "case_id": "CASE-CLAIM782",
        "trust_status": "SUFFICIENT",
        "fraud_model": {
            "risk_score": 0.08,
            "model": "XGBoost",
            "anomaly_score": 0.05,
            "feature_contributions": {
                "police_fir_alignment": -0.40,
                "photo_metadata_consistency": -0.35,
                "policy_tenure_baseline": -0.20
            }
        },
        "evidence_quality": "HIGH",
        "completeness": 1.0,
        "evidence": [ev2_1, ev2_2, ev2_3],
        "claims": [
            {"evidence_id": "E-101", "subject": "CLAIM-782", "predicate": "incident_location", "value": "Pune Expressway KM-42"},
            {"evidence_id": "E-102", "subject": "CLAIM-782", "predicate": "police_verification", "value": "VERIFIED_ACCIDENTAL"}
        ],
        "contradictions": [],
        "missing_information": [],
        "reasoning": "All submitted documentation—including formal Police FIR, authorized garage survey, and GPS-tagged telemetry—demonstrate complete factual consistency.\n\nML fraud scoring calculates a negligible 8.0% probability of anomaly. The file contains zero contradictions and meets all statutory evidence criteria for final claim approval.",
        "challenge": {
            "performed": True,
            "hypothesis": "Claim represents staged collision.",
            "counter_evidence_found": True,
            "counter_evidence_ids": ["E-102"],
            "challenge_summary": "Police accident verification and road camera logs refute fraud hypothesis.",
            "original_risk_state": "LOW_RISK",
            "adjusted_risk_state": "VERIFIED_LEGITIMATE"
        },
        "recommendation": "APPROVE",
        "audit": {
            "timestamp": datetime.utcnow().isoformat(),
            "engine_version": "2.0.0",
            "gate": "DETERMINISTIC_DECISION_GATE"
        }
    }
    await db.decisions.insert_one({"case_id": "CASE-CLAIM782", "trust_status": "SUFFICIENT", "packet": dec2, "created_at": datetime.utcnow().isoformat()})

    # =========================================================================
    # CASE 3: CORPORATE LOAN — SME Underwriting (INCOMPLETE -> REQUEST_DATA)
    # =========================================================================
    case3 = {
        "case_id": "CASE-LOAN409",
        "title": "SME Working Capital Line (₹1.5 Cr) - ABC Infotech",
        "description": "Commercial loan request requiring audited financial statement verification and GST quarterly filing reconciliation.",
        "entity_type": "LOAN_APPLICATION",
        "entity_id": "LOAN-409",
        "status": "OPEN",
        "trust_status": "INCOMPLETE",
        "initial_metadata": {"company": "ABC Infotech Solutions Ltd", "requested_amount": 15000000},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    await db.cases.insert_one(case3)

    ev3_1 = {
        "evidence_id": "E-201",
        "case_id": "CASE-LOAN409",
        "source": {"type": "PDF", "system": "MCA_REGISTRY", "name": "company_incorporation_cert.pdf"},
        "claim": {"subject": "ABC Infotech", "predicate": "registration_status", "value": "ACTIVE_REGISTERED", "raw_statement": "Company registered in Mumbai since 2019", "confidence": 1.0},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "is_primary_source": True, "overall_quality": "HIGH"},
        "traceability": {"file": "company_incorporation_cert.pdf", "page": 1},
        "created_at": datetime.utcnow().isoformat()
    }
    ev3_2 = {
        "evidence_id": "E-202",
        "case_id": "CASE-LOAN409",
        "source": {"type": "EXCEL", "system": "BANK_STATEMENT_FEED", "name": "abc_turnover_12m.xlsx"},
        "claim": {"subject": "ABC Infotech", "predicate": "annual_turnover", "value": "₹1.84 Cr", "raw_statement": "Annual banking credit inflows total ₹1.84 Crore", "confidence": 0.95},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "is_primary_source": True, "overall_quality": "HIGH"},
        "traceability": {"file": "abc_turnover_12m.xlsx", "line_number": 365},
        "created_at": datetime.utcnow().isoformat()
    }
    await db.evidence.insert_many([ev3_1, ev3_2])

    dec3 = {
        "case_id": "CASE-LOAN409",
        "trust_status": "INCOMPLETE",
        "fraud_model": {
            "risk_score": 0.35,
            "model": "XGBoost",
            "anomaly_score": 0.28,
            "feature_contributions": {
                "positive_banking_inflows": -0.25,
                "missing_q4_gst_returns": 0.40
            }
        },
        "evidence_quality": "HIGH",
        "completeness": 0.65,
        "evidence": [ev3_1, ev3_2],
        "claims": [
            {"evidence_id": "E-201", "subject": "ABC Infotech", "predicate": "registration_status", "value": "ACTIVE_REGISTERED"},
            {"evidence_id": "E-202", "subject": "ABC Infotech", "predicate": "annual_turnover", "value": "₹1.84 Cr"}
        ],
        "contradictions": [],
        "missing_information": [
            {
                "item": "gst_quarterly_returns_q4",
                "reason": "Q4 GST filing reconciliation required to verify claimed net sales versus taxable ledger.",
                "priority": "HIGH",
                "suggested_source": "GSTN_PORTAL_API"
            },
            {
                "item": "director_personal_guarantee_kyc",
                "reason": "Managing Director's physical address verification required for facilities over ₹1 Crore.",
                "priority": "MEDIUM",
                "suggested_source": "DIGILOCKER_KYC"
            }
        ],
        "reasoning": "Application exhibits healthy bank credit velocity (₹1.84 Cr turnover) and active company registration.\n\nHowever, the underwriting dossier lacks mandatory Q4 GST tax reconciliation and director guarantee verification. In compliance with credit policy, the decision is marked INCOMPLETE pending supplementary submissions.",
        "challenge": {
            "performed": True,
            "hypothesis": "Company has unrecorded liabilities.",
            "counter_evidence_found": False,
            "counter_evidence_ids": [],
            "challenge_summary": "Credit bureau check indicates 0 defaults, but financial disclosures are incomplete.",
            "original_risk_state": "MODERATE",
            "adjusted_risk_state": "PENDING_DOCUMENTATION"
        },
        "recommendation": "REQUEST_DATA",
        "audit": {
            "timestamp": datetime.utcnow().isoformat(),
            "engine_version": "2.0.0",
            "gate": "DETERMINISTIC_DECISION_GATE"
        }
    }
    await db.decisions.insert_one({"case_id": "CASE-LOAN409", "trust_status": "INCOMPLETE", "packet": dec3, "created_at": datetime.utcnow().isoformat()})

    # =========================================================================
    # CASE 4: REGULATORY — Cross-Border KYC Audit (LOW_QUALITY -> REQUEST_BETTER_SOURCES)
    # =========================================================================
    case4 = {
        "case_id": "CASE-KYC501",
        "title": "Cross-Border Remittance KYC Audit - USER-501",
        "description": "International remittance identity verification with severe document degradation and expired address proof.",
        "entity_type": "KYC_AUDIT",
        "entity_id": "USER-501",
        "status": "OPEN",
        "trust_status": "LOW_QUALITY",
        "initial_metadata": {"transfer_destination": "Singapore", "amount_usd": 12000},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    await db.cases.insert_one(case4)

    ev4_1 = {
        "evidence_id": "E-301",
        "case_id": "CASE-KYC501",
        "source": {"type": "IMAGE", "system": "MOBILE_SCAN_CAPTURE", "name": "passport_scan_blurry.jpg"},
        "claim": {"subject": "USER-501", "predicate": "passport_mrz_code", "value": "UNREADABLE_OCR", "raw_statement": "OCR confidence 42% due to motion blur and glare across MRZ zone.", "confidence": 0.42},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "LOW", "freshness": "CURRENT", "completeness": 0.40, "ocr_confidence": 0.42, "is_primary_source": False, "overall_quality": "LOW"},
        "traceability": {"file": "passport_scan_blurry.jpg", "page": 1},
        "created_at": datetime.utcnow().isoformat()
    }
    ev4_2 = {
        "evidence_id": "E-302",
        "case_id": "CASE-KYC501",
        "source": {"type": "PDF", "system": "USER_UPLOAD", "name": "utility_bill_2021.pdf"},
        "claim": {"subject": "USER-501", "predicate": "proof_of_address", "value": "EXPIRED_DATE_2021", "raw_statement": "Utility bill date is 2021-08-14, which exceeds the mandatory 90-day validity window.", "confidence": 0.60},
        "timestamp": datetime.utcnow().isoformat(),
        "quality": {"reliability": "LOW", "freshness": "OUTDATED", "completeness": 0.50, "is_primary_source": False, "overall_quality": "LOW"},
        "traceability": {"file": "utility_bill_2021.pdf", "page": 1},
        "created_at": datetime.utcnow().isoformat()
    }
    await db.evidence.insert_many([ev4_1, ev4_2])

    dec4 = {
        "case_id": "CASE-KYC501",
        "trust_status": "LOW_QUALITY",
        "fraud_model": {
            "risk_score": 0.68,
            "model": "XGBoost",
            "anomaly_score": 0.62,
            "feature_contributions": {
                "low_ocr_confidence_penalty": 0.45,
                "outdated_address_document": 0.35
            }
        },
        "evidence_quality": "LOW",
        "completeness": 0.45,
        "evidence": [ev4_1, ev4_2],
        "claims": [
            {"evidence_id": "E-301", "subject": "USER-501", "predicate": "passport_mrz_code", "value": "UNREADABLE_OCR"},
            {"evidence_id": "E-302", "subject": "USER-501", "predicate": "proof_of_address", "value": "EXPIRED_DATE_2021"}
        ],
        "contradictions": [],
        "missing_information": [
            {
                "item": "high_resolution_passport_capture",
                "reason": "Current scan failed cryptographic MRZ checksum validation.",
                "priority": "HIGH",
                "suggested_source": "NFC_PASSPORT_READER"
            },
            {
                "item": "current_utility_bill_under_90_days",
                "reason": "Address document is from 2021, violating regulatory recency standards.",
                "priority": "HIGH",
                "suggested_source": "BANK_STATEMENT_PDF"
            }
        ],
        "reasoning": "Identity verification cannot proceed due to substandard source quality.\n\nThe passport image exhibits severe glare resulting in 42% OCR confidence, while the accompanying address proof is over 4 years old. The Decision Gate categorizes this as LOW_QUALITY and requires fresh document submissions.",
        "challenge": {
            "performed": True,
            "hypothesis": "Identity document is forged or tampered.",
            "counter_evidence_found": False,
            "counter_evidence_ids": [],
            "challenge_summary": "Image quality is insufficient to rule out digital manipulation.",
            "original_risk_state": "UNVERIFIED",
            "adjusted_risk_state": "REQUIRES_RESUBMISSION"
        },
        "recommendation": "REQUEST_BETTER_SOURCES",
        "audit": {
            "timestamp": datetime.utcnow().isoformat(),
            "engine_version": "2.0.0",
            "gate": "DETERMINISTIC_DECISION_GATE"
        }
    }
    await db.decisions.insert_one({"case_id": "CASE-KYC501", "trust_status": "LOW_QUALITY", "packet": dec4, "created_at": datetime.utcnow().isoformat()})

    # =========================================================================
    # CONNECTORS SEEDING
    # =========================================================================
    connectors = [
        {
            "connector_id": "CONN-BANK-01",
            "name": "Core Banking Transaction DB (PostgreSQL)",
            "connector_type": "POSTGRESQL",
            "config": {
                "id": "CONN-BANK-01",
                "name": "Core Banking Transaction DB (PostgreSQL)",
                "connector_type": "POSTGRESQL",
                "host": "localhost",
                "port": 5432,
                "database": "bank_core_prod",
                "read_only": True,
                "is_active": True
            },
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "connector_id": "CONN-TELEMETRY-02",
            "name": "Cellular Telemetry Stream (Edge Gateway)",
            "connector_type": "REST_API",
            "config": {
                "id": "CONN-TELEMETRY-02",
                "name": "Cellular Telemetry Stream (Edge Gateway)",
                "connector_type": "REST_API",
                "api_endpoint": "http://localhost:8001/api/evidence/query",
                "read_only": True,
                "is_active": True
            },
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "connector_id": "CONN-KYC-03",
            "name": "Corporate KYC Registry Share (CSV/PDF)",
            "connector_type": "CSV_DIRECTORY",
            "config": {
                "id": "CONN-KYC-03",
                "name": "Corporate KYC Registry Share (CSV/PDF)",
                "connector_type": "CSV_DIRECTORY",
                "file_path": "./sample_data",
                "read_only": True,
                "is_active": True
            },
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    await db.connectors.insert_many(connectors)

    print("[SUCCESS] All 4 multi-domain cases, decisions, and connectors seeded into MongoDB Atlas successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
