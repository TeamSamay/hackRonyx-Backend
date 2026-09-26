# ⚖️ VERDICT AI — Complete Backend (Developer 2 Owner)





> **"Files, databases, APIs, and external sources are only different ways of collecting evidence. Once inside VERDICT, everything becomes a traceable Evidence Object."**

VERDICT AI is an enterprise-grade truth verification, fraud analysis, and deterministic decisioning platform that replaces manual file uploads with multi-source ingestion connectors, localized Edge Gateways, RAG retrieval, ML risk models (XGBoost + Isolation Forest + SHAP), deterministic contradiction detection, counter-evidence challenge engine, and an un-bypassable **Deterministic Decision Gate**.

---

## 🏛️ System Architecture

```text
DATA SOURCES (Postgres, MySQL, CSV, Excel, PDF, Image OCR, APIs)
    ↓
INGESTION LAYER & EDGE GATEWAY (Read-Only Authorized Connectors)
    ↓
DOCUMENT / DATA PROCESSING (PyMuPDF, OpenPyXL, Pandas, OCR)
    ↓
EVIDENCE NORMALIZATION LAYER (Traceable Evidence Objects)
    ↓
DATABASE (PostgreSQL / SQLite + pgvector)
    ↓
RAG RETRIEVAL (Traceable Claim & Metadata Embeddings)
    ↓
ML ANALYSIS (XGBoost Risk + Isolation Forest Anomaly + SHAP)
    ↓
CLAIM EXTRACTION & CONTRADICTION ENGINE (Deterministic Python Detection)
    ↓
EVIDENCE QUALITY ASSESSMENT (Deterministic Quality Scoring)
    ↓
LLM REASONING (Groq / Provider-Agnostic LLM Service)
    ↓
CHALLENGE ENGINE (Adversarial Counter-Evidence Hypothesis Stress-Test)
    ↓
DETERMINISTIC DECISION GATE (Enforcing 6 Strict Final Trust States)
    ↓
DECISION PACKET (Canonical JSON Contract for React Console)
    ↓
FASTAPI REST API → REACT FRONTEND
```

---

## 📁 Repository Structure

```text
hackRonyx-Backend/
├── app/
│   ├── main.py                     # FastAPI application entry & CORS
│   ├── api/
│   │   ├── cases.py                # Case management endpoints
│   │   ├── evidence.py             # Multi-format upload & manual evidence ingestion
│   │   ├── connectors.py           # Enterprise database & file share connectors
│   │   ├── analysis.py             # End-to-end VERDICT pipeline runner
│   │   ├── challenge.py            # Challenge Engine stress-test API
│   │   ├── decisions.py            # Canonical Decision Packet retriever
│   │   ├── reviews.py              # Human Analyst review & audit log
│   │   └── demo.py                 # 1-Click Hackathon Seeder for Case TX-92831
│   ├── core/
│   │   ├── config.py               # Pydantic Settings & environment
│   │   ├── security.py             # Read-only SQL sanitizer & token hashing
│   │   └── logging.py              # Structured logging
│   ├── db/
│   │   ├── session.py              # Async SQLAlchemy Engine & Session Maker
│   │   └── models.py               # Case, Document, Evidence, Contradiction, Decision models
│   ├── schemas/
│   │   ├── evidence.py             # Canonical EvidenceObject schema
│   │   ├── decision.py             # DecisionPacket, 6 Final Trust States
│   │   ├── case.py                 # Case DTOs
│   │   ├── analysis.py             # ML & Analysis DTOs
│   │   └── connector.py            # Enterprise Connector DTOs
│   ├── services/
│   │   ├── ingestion/              # Ingestion Gateway & format parsers
│   │   ├── documents/              # Unified file dispatcher
│   │   ├── ocr/                    # Tesseract OCR engine & fallbacks
│   │   ├── rag/                    # Vector store & evidence retriever
│   │   ├── ml/                     # XGBoost, Isolation Forest & SHAP
│   │   ├── llm/                    # Groq API provider-agnostic reasoning service
│   │   ├── evidence/               # Evidence Normalizer & Quality Engine
│   │   ├── contradiction/          # Deterministic Contradiction Engine
│   │   ├── challenge/              # Counter-Evidence Challenge Engine
│   │   └── decision/               # Deterministic Decision Gate
│   └── workers/
│       └── tasks.py                # Asynchronous background job processing
├── edge_gateway/                   # Standalone Local Edge Gateway
├── sample_data/                    # Sample feeds (CSV, JSON, Demo TX-92831)
├── tests/                          # Automated Pytest suite
├── Dockerfile                      # Production Docker container
├── docker-compose.yml              # PostgreSQL + pgvector + Backend + Gateway
├── requirements.txt                # Python dependencies
└── .env.example                    # Sample environment configuration
```

---

## 🔒 The 6 Deterministic Final Trust States

The Decision Gate strictly enforces these 6 deterministic states. The LLM **cannot** bypass this gate:

1. **`SUFFICIENT`** → `APPROVE` / `PROCEED` (Clean data, low risk, 0 contradictions).
2. **`INCOMPLETE`** → `REQUEST_DATA` (Partial insights, missing specific signals).
3. **`CONFLICTING`** → `HUMAN_REVIEW` (Spatio-temporal, location, or claim clashes).
4. **`LOW_QUALITY`** → `REQUEST_BETTER_SOURCES` (Poor OCR, untraceable or unreliable source).
5. **`NEED_MORE_INFO`** → `SPECIFY_REQUIRED_EVIDENCE` (Missing critical identity/device proof).
6. **`REFUSE`** → `REFUSE_ESCALATE` (Critical failure state, unresolvable high fraud risk).

---

## 🚀 Quickstart & Hackathon Demo Execution

### Option 1: Run with Docker Compose (Recommended for Dev 3 / Deployment)

```bash
docker-compose up --build
```
- FastAPI Backend: `http://localhost:8000`
- Interactive API Docs: `http://localhost:8000/docs`
- Edge Gateway: `http://localhost:8001`
- PostgreSQL + pgvector: `localhost:5432`

### Option 2: Run Standalone Python

```bash
cd hackRonyx-Backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🎯 1-Click Hackathon Demo (`TX-92831`)

To demonstrate the full end-to-end pipeline in your pitch:

1. Send `POST http://localhost:8000/api/demo/seed-tx92831`
2. The backend will:
   - Ingest **E001** (Core Banking: Mumbai, ₹85,000)
   - Ingest **E002** (Device Telemetry: Delhi)
   - Ingest **E003** (KYC Doc: Mumbai, OCR 96%)
   - Ingest **E004** (Account History: Mumbai affinity)
   - Execute XGBoost (91% Fraud Risk) + Isolation Forest (Anomaly) + SHAP
   - Detect **Mumbai ≠ Delhi** contradiction deterministically
   - Stress-test via Challenge Engine
   - Enforce **`CONFLICTING`** State → Route to **`HUMAN_REVIEW`**
   - Return the finalized Canonical `DecisionPacket` to the React Console.
