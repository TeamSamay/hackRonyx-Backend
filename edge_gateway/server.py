import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

gateway_app = FastAPI(
    title="VERDICT Edge Gateway & Demo Enterprise Data Server",
    version="2.0.0",
    description="Simulates a local/remote Enterprise Data Gateway hosting PostgreSQL records, Customer/KYC DB, Telemetry, and Document Store."
)

gateway_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active Demo Scenario State
# Options: "SUFFICIENT", "INCOMPLETE", "CONFLICTING", "LOW_QUALITY"
CURRENT_SCENARIO = "CONFLICTING"

# Synthetic Enterprise Database Storage
CUSTOMERS_DB = {
    "CUST-1001": {
        "customer_id": "CUST-1001",
        "name": "Rahul Sharma",
        "age": 32,
        "city": "Mumbai",
        "state": "Maharashtra",
        "email": "rahul.sharma@example.com",
        "phone": "+91 98765 43210",
        "customer_since": "2022-04-12",
        "account_status": "ACTIVE",
        "kyc_status": "VERIFIED"
    },
    "CUST-1002": {
        "customer_id": "CUST-1002",
        "name": "Priya Patel",
        "age": 29,
        "city": "Ahmedabad",
        "state": "Gujarat",
        "email": "priya.patel@example.com",
        "phone": "+91 98123 45678",
        "customer_since": "2023-01-15",
        "account_status": "ACTIVE",
        "kyc_status": "VERIFIED"
    }
}

ACCOUNTS_DB = {
    "ACC-92831": {
        "account_id": "ACC-92831",
        "customer_id": "CUST-1001",
        "account_type": "SAVINGS",
        "opened_date": "2022-04-12",
        "balance": 482000.0,
        "currency": "INR",
        "status": "ACTIVE",
        "branch": "Nariman Point, Mumbai"
    }
}

DOCUMENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data", "documents"))
DATASETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_data"))
os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(DATASETS_DIR, exist_ok=True)

# Pydantic Request & Response Schemas
class EvidenceQueryRequest(BaseModel):
    case_id: str
    subject_id: str = "TX-92831"
    requested_evidence: List[str] = ["transaction", "customer", "device", "kyc", "history"]

class ScenarioSwitchRequest(BaseModel):
    scenario: str # SUFFICIENT | INCOMPLETE | CONFLICTING | LOW_QUALITY

@gateway_app.get("/health", tags=["Gateway Health"])
async def gateway_health():
    return {
        "status": "ONLINE",
        "service": "VERDICT Edge Gateway Node",
        "mode": "READ_ONLY_ENTERPRISE_GATEWAY",
        "port": 8001,
        "active_scenario": CURRENT_SCENARIO,
        "connected_datasources": [
            {"type": "PostgreSQL", "database": "bank_core_db", "status": "CONNECTED"},
            {"type": "Device Telemetry", "stream": "mobile_app_events", "status": "ACTIVE"},
            {"type": "KYC Document Vault", "store": "s3_enterprise_bucket", "status": "ENCRYPTED_READ"},
            {"type": "Excel/CSV Ingestion Feed", "path": "./sample_data", "status": "SYNCED"}
        ],
        "latency_ms": 14
    }

@gateway_app.get("/api/scenarios/active", tags=["Scenarios"])
async def get_active_scenario():
    return {
        "active_scenario": CURRENT_SCENARIO,
        "available_scenarios": ["SUFFICIENT", "INCOMPLETE", "CONFLICTING", "LOW_QUALITY"]
    }

@gateway_app.post("/api/scenarios/switch", tags=["Scenarios"])
async def switch_scenario(req: ScenarioSwitchRequest):
    global CURRENT_SCENARIO
    scenario_upper = req.scenario.upper()
    if scenario_upper not in ["SUFFICIENT", "INCOMPLETE", "CONFLICTING", "LOW_QUALITY"]:
        raise HTTPException(status_code=400, detail="Invalid scenario. Choose from: SUFFICIENT, INCOMPLETE, CONFLICTING, LOW_QUALITY")
    CURRENT_SCENARIO = scenario_upper
    return {
        "success": True,
        "previous_scenario": CURRENT_SCENARIO,
        "active_scenario": scenario_upper,
        "message": f"Edge Gateway scenario successfully set to '{scenario_upper}'"
    }

@gateway_app.get("/api/customer/{customer_id}", tags=["Customer DB"])
async def get_customer(customer_id: str):
    if customer_id not in CUSTOMERS_DB:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return CUSTOMERS_DB[customer_id]

@gateway_app.get("/api/account/{account_id}", tags=["Banking DB"])
async def get_account(account_id: str):
    if account_id not in ACCOUNTS_DB:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return ACCOUNTS_DB[account_id]

@gateway_app.get("/api/transaction/{transaction_id}", tags=["Transactions DB"])
async def get_transaction(transaction_id: str):
    if CURRENT_SCENARIO == "SUFFICIENT":
        return {
            "transaction_id": transaction_id,
            "account_id": "ACC-92831",
            "timestamp": "2026-09-26T10:42:00",
            "amount": 85000.0,
            "currency": "INR",
            "merchant": "ABC Electronics Mumbai",
            "merchant_category": "Electronics",
            "location": "Mumbai",
            "payment_method": "UPI",
            "device_id": "DEV-1001",
            "ip_address": "103.21.244.2",
            "status": "SUCCESS"
        }
    elif CURRENT_SCENARIO == "INCOMPLETE":
        return {
            "transaction_id": transaction_id,
            "account_id": "ACC-92831",
            "timestamp": "2026-09-26T10:42:00",
            "amount": 285000.0,
            "currency": "INR",
            "merchant": "Unregistered International Wire",
            "merchant_category": "High Value Transfer",
            "location": "Mumbai",
            "payment_method": "WIRE_TRANSFER",
            "device_id": "DEV-UNKNOWN",
            "ip_address": "103.21.244.2",
            "status": "PENDING"
        }
    elif CURRENT_SCENARIO == "LOW_QUALITY":
        return {
            "transaction_id": transaction_id,
            "account_id": "ACC-92831",
            "timestamp": "2026-09-26T10:42:00",
            "amount": 85000.0,
            "currency": "INR",
            "merchant": "ABC Electronics",
            "merchant_category": "Retail",
            "location": "Mumbai",
            "payment_method": "CARD_PRESENT",
            "device_id": "DEV-1001",
            "ip_address": "192.168.1.12",
            "status": "SUCCESS"
        }
    else: # CONFLICTING
        return {
            "transaction_id": transaction_id,
            "account_id": "ACC-92831",
            "timestamp": "2026-09-26T10:42:00",
            "amount": 85000.0,
            "currency": "INR",
            "merchant": "ABC Electronics Mumbai",
            "merchant_category": "Electronics",
            "location": "Mumbai",
            "payment_method": "UPI",
            "device_id": "DEV-1001",
            "ip_address": "103.21.244.2",
            "status": "SUCCESS"
        }

@gateway_app.get("/api/customer/{customer_id}/devices", tags=["Device Telemetry"])
async def get_customer_devices(customer_id: str):
    if CURRENT_SCENARIO == "SUFFICIENT":
        return [
            {
                "device_id": "DEV-1001",
                "customer_id": customer_id,
                "device_type": "iPhone 14",
                "registered_city": "Mumbai",
                "last_seen_city": "Mumbai",
                "last_seen_time": "2026-09-26T10:42:00",
                "device_status": "ACTIVE"
            }
        ]
    elif CURRENT_SCENARIO == "INCOMPLETE":
        return [] # Empty device list -> Missing device ownership verification!
    elif CURRENT_SCENARIO == "LOW_QUALITY":
        return [
            {
                "device_id": "DEV-1001",
                "customer_id": customer_id,
                "device_type": "Android Legacy",
                "registered_city": "Mumbai",
                "last_seen_city": "Mumbai",
                "last_seen_time": "2022-01-10T10:00:00",
                "device_status": "UNCHECKED"
            }
        ]
    else: # CONFLICTING
        return [
            {
                "device_id": "DEV-1001",
                "customer_id": customer_id,
                "device_type": "iPhone 14",
                "registered_city": "Mumbai",
                "last_seen_city": "Delhi", # Divergent telemetry!
                "last_seen_time": "2026-09-26T10:43:00",
                "device_status": "ACTIVE"
            }
        ]

@gateway_app.get("/api/customer/{customer_id}/kyc", tags=["KYC Registry"])
async def get_customer_kyc(customer_id: str):
    if CURRENT_SCENARIO == "INCOMPLETE":
        return {
            "kyc_id": "KYC-1001",
            "customer_id": customer_id,
            "document_type": "PAN",
            "verified": False,
            "registered_name": "Rahul Sharma",
            "registered_address": "Mumbai",
            "verification_date": "2021-02-14",
            "document_status": "EXPIRED_REQUIRES_REVERIFICATION"
        }
    elif CURRENT_SCENARIO == "LOW_QUALITY":
        return {
            "kyc_id": "KYC-1001",
            "customer_id": customer_id,
            "document_type": "PAN_SCAN",
            "verified": True,
            "registered_name": "Rahul Sharma",
            "registered_address": "Mumbai",
            "verification_date": "2020-05-10",
            "ocr_confidence": 0.42, # Low OCR quality!
            "document_status": "BLURRY_IMAGE_LOW_QUALITY"
        }
    else:
        return {
            "kyc_id": "KYC-1001",
            "customer_id": customer_id,
            "document_type": "PAN",
            "verified": True,
            "registered_name": "Rahul Sharma",
            "registered_address": "Mumbai",
            "verification_date": "2026-01-10",
            "ocr_confidence": 0.96,
            "document_status": "VERIFIED"
        }

@gateway_app.post("/api/evidence/query", tags=["Targeted Evidence Pull"])
async def query_evidence(req: EvidenceQueryRequest):
    """
    Main Edge Gateway Evidence Extraction API.
    VERDICT Core Backend calls this endpoint to pull live enterprise evidence.
    """
    case_id = req.case_id
    subject_id = req.subject_id
    evidence_items = []

    if CURRENT_SCENARIO == "SUFFICIENT":
        evidence_items = [
            {
                "evidence_id": f"EG-E001-{case_id}",
                "case_id": case_id,
                "source": {"type": "DATABASE", "system": "CORE_BANKING_POSTGRES", "reference": "transactions:TX-92831"},
                "claim": {"subject": subject_id, "predicate": "transaction_location", "value": "Mumbai", "raw_statement": "Transaction TX-92831 authorized at Mumbai terminal for ₹85,000"},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "overall_quality": "HIGH"},
                "traceability": {"table": "transactions", "record_id": subject_id, "gateway": "VERDICT_EDGE_NODE_1"},
                "raw_payload": {"amount": 85000, "location": "Mumbai", "status": "SUCCESS"}
            },
            {
                "evidence_id": f"EG-E002-{case_id}",
                "case_id": case_id,
                "source": {"type": "DEVICE_SIGNAL", "system": "MOBILE_TELEMETRY_GATEWAY", "reference": "devices:DEV-1001"},
                "claim": {"subject": subject_id, "predicate": "device_location", "value": "Mumbai", "raw_statement": "Device DEV-1001 pinged cell tower in Mumbai at 10:42 AM"},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "overall_quality": "HIGH"},
                "traceability": {"ip": "103.21.244.2", "cell_tower": "MUM-8012"},
                "raw_payload": {"ip": "103.21.244.2", "location": "Mumbai", "device": "iPhone 14"}
            },
            {
                "evidence_id": f"EG-E003-{case_id}",
                "case_id": case_id,
                "source": {"type": "IMAGE", "system": "KYC_DOCUMENT_VAULT", "reference": "kyc_doc_1001.pdf"},
                "claim": {"subject": subject_id, "predicate": "registered_city", "value": "Mumbai", "raw_statement": "PAN & Address Proof verified for Nariman Point, Mumbai"},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "ocr_confidence": 0.96, "overall_quality": "HIGH"},
                "traceability": {"file": "kyc_doc_1001.pdf", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
                "raw_payload": {"registered_address": "Mumbai", "kyc_status": "VERIFIED"}
            }
        ]

    elif CURRENT_SCENARIO == "INCOMPLETE":
        evidence_items = [
            {
                "evidence_id": f"EG-E001-{case_id}",
                "case_id": case_id,
                "source": {"type": "DATABASE", "system": "CORE_BANKING_POSTGRES", "reference": "transactions:TX-92831"},
                "claim": {"subject": subject_id, "predicate": "transaction_location", "value": "Mumbai", "raw_statement": "High-value wire request of ₹2,85,000 initiated"},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 0.75, "overall_quality": "MEDIUM"},
                "traceability": {"table": "transactions", "record_id": subject_id},
                "raw_payload": {"amount": 285000, "location": "Mumbai"}
            },
            {
                "evidence_id": f"EG-E002-{case_id}",
                "case_id": case_id,
                "source": {"type": "IMAGE", "system": "KYC_DOCUMENT_VAULT", "reference": "kyc_expired.pdf"},
                "claim": {"subject": subject_id, "predicate": "registered_city", "value": "Mumbai", "raw_statement": "KYC document expired in 2021. Recent identity verification missing."},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "LOW", "freshness": "OUTDATED", "completeness": 0.40, "overall_quality": "LOW"},
                "traceability": {"file": "kyc_expired.pdf"},
                "raw_payload": {"status": "EXPIRED"}
            }
        ]

    elif CURRENT_SCENARIO == "LOW_QUALITY":
        evidence_items = [
            {
                "evidence_id": f"EG-E001-{case_id}",
                "case_id": case_id,
                "source": {"type": "DATABASE", "system": "CORE_BANKING_POSTGRES", "reference": "transactions:TX-92831"},
                "claim": {"subject": subject_id, "predicate": "transaction_location", "value": "Mumbai", "raw_statement": "Transaction recorded at branch terminal"},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "overall_quality": "HIGH"},
                "traceability": {"table": "transactions", "record_id": subject_id},
                "raw_payload": {"amount": 85000, "location": "Mumbai"}
            },
            {
                "evidence_id": f"EG-E002-{case_id}",
                "case_id": case_id,
                "source": {"type": "IMAGE", "system": "OCR_SCAN_VAULT", "reference": "blurry_kyc_scan.jpg"},
                "claim": {"subject": subject_id, "predicate": "registered_city", "value": "Mumbai (Uncertain)", "raw_statement": "OCR confidence extremely low due to severe blur: 42%"},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "LOW", "freshness": "OUTDATED", "completeness": 0.35, "ocr_confidence": 0.42, "overall_quality": "LOW"},
                "traceability": {"file": "blurry_kyc_scan.jpg", "ocr_confidence": 0.42},
                "raw_payload": {"ocr_confidence": 0.42}
            }
        ]

    else: # CONFLICTING
        evidence_items = [
            {
                "evidence_id": f"EG-E001-{case_id}",
                "case_id": case_id,
                "source": {"type": "DATABASE", "system": "CORE_BANKING_POSTGRES", "reference": "transactions:TX-92831"},
                "claim": {"subject": subject_id, "predicate": "transaction_location", "value": "Mumbai", "raw_statement": "Bank Transaction DB records transaction location in Mumbai"},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "overall_quality": "HIGH"},
                "traceability": {"table": "transactions", "record_id": subject_id},
                "raw_payload": {"amount": 85000, "location": "Mumbai"}
            },
            {
                "evidence_id": f"EG-E002-{case_id}",
                "case_id": case_id,
                "source": {"type": "DEVICE_SIGNAL", "system": "MOBILE_TELEMETRY_GATEWAY", "reference": "devices:DEV-1001"},
                "claim": {"subject": subject_id, "predicate": "device_location", "value": "Delhi", "raw_statement": "Mobile device cell tower authenticated location in Delhi"},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "HIGH", "freshness": "CURRENT", "completeness": 1.0, "overall_quality": "HIGH"},
                "traceability": {"ip": "103.21.244.2", "cell_tower": "DEL-4102"},
                "raw_payload": {"ip": "103.21.244.2", "location": "Delhi"}
            },
            {
                "evidence_id": f"EG-E003-{case_id}",
                "case_id": case_id,
                "source": {"type": "PDF", "system": "COMPANY_REGISTRY_VAULT", "reference": "abc_technologies_registration.pdf"},
                "claim": {"subject": subject_id, "predicate": "registered_city", "value": "Pune", "raw_statement": "Corporate registration records official address in Pune"},
                "timestamp": datetime.utcnow().isoformat(),
                "quality": {"reliability": "HIGH", "freshness": "RECENT", "completeness": 0.95, "overall_quality": "HIGH"},
                "traceability": {"file": "abc_technologies_registration.pdf", "page": 1},
                "raw_payload": {"registered_address": "Pune"}
            }
        ]

    return {
        "case_id": case_id,
        "active_scenario": CURRENT_SCENARIO,
        "evidence_count": len(evidence_items),
        "evidence": evidence_items
    }

@gateway_app.get("/api/documents/list", tags=["Document Vault"])
async def list_documents():
    docs = []
    if os.path.exists(DOCUMENTS_DIR):
        for f in os.listdir(DOCUMENTS_DIR):
            fp = os.path.join(DOCUMENTS_DIR, f)
            if os.path.isfile(fp):
                ext = f.split(".")[-1].upper()
                docs.append({
                    "filename": f,
                    "file_type": ext,
                    "size_bytes": os.path.getsize(fp),
                    "modified": datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
                    "download_url": f"/api/documents/download/{f}"
                })
    if os.path.exists(DATASETS_DIR):
        for f in os.listdir(DATASETS_DIR):
            fp = os.path.join(DATASETS_DIR, f)
            if os.path.isfile(fp) and (f.endswith(".csv") or f.endswith(".xlsx")):
                ext = f.split(".")[-1].upper()
                docs.append({
                    "filename": f,
                    "file_type": ext,
                    "size_bytes": os.path.getsize(fp),
                    "modified": datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
                    "download_url": f"/api/documents/download/{f}"
                })
    return {"count": len(docs), "documents": docs}

@gateway_app.get("/api/documents/download/{filename}", tags=["Document Vault"])
async def download_document(filename: str):
    fp1 = os.path.join(DOCUMENTS_DIR, filename)
    fp2 = os.path.join(DATASETS_DIR, filename)
    target_fp = fp1 if os.path.exists(fp1) else (fp2 if os.path.exists(fp2) else None)
    if not target_fp:
        raise HTTPException(status_code=404, detail=f"Document {filename} not found.")
    return FileResponse(target_fp, filename=filename)

@gateway_app.post("/api/documents/upload", tags=["Document Vault"])
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename
    target_path = os.path.join(DOCUMENTS_DIR, filename)
    with open(target_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {
        "success": True,
        "filename": filename,
        "size_bytes": os.path.getsize(target_path),
        "status": "STORED_ON_EDGE_GATEWAY",
        "ocr_queued": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(gateway_app, host="0.0.0.0", port=8001)
