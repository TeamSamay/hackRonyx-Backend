from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.analysis import AnalysisRequest
from app.schemas.evidence import EvidenceObject
from app.schemas.decision import DecisionPacket
from app.services.rag.retriever import retriever
from app.services.ml.fraud_model import fraud_model
from app.services.ml.anomaly_model import anomaly_model
from app.services.ml.explainability import shap_explainer
from app.services.contradiction.contradiction_engine import contradiction_engine
from app.services.challenge.challenge_engine import challenge_engine
from app.services.decision.decision_gate import decision_gate
from app.db.repository import repo
from app.core.logging import logger

router = APIRouter(prefix="/api/cases", tags=["Analysis"])

async def _load_case_evidence(case_id: str) -> List[EvidenceObject]:
    raw_list = await repo.get_case_evidence(case_id)
    return [EvidenceObject(**r) for r in raw_list]

@router.post("/{case_id}/analyze", response_model=DecisionPacket)
async def run_case_analysis(case_id: str, req: AnalysisRequest = None):
    """
    Full VERDICT Pipeline Execution against MongoDB:
    1. Load all case evidence
    2. RAG Retrieval of decision-critical items
    3. ML Risk & Anomaly scoring + SHAP
    4. Deterministic Contradiction Detection
    5. Challenge Engine counter-evidence evaluation
    6. DETERMINISTIC DECISION GATE evaluation
    7. Saves to MongoDB & returns the canonical DecisionPacket
    """
    logger.info(f"Triggered full analysis for case {case_id}")
    
    # 1. Load case
    case = await repo.get_case(case_id)
    if not case:
        # Auto-create case if not present
        case = {
            "case_id": case_id,
            "title": f"Investigation {case_id}",
            "entity_type": "TRANSACTION",
            "entity_id": case_id,
            "status": "OPEN"
        }
        await repo.create_case(case)

    # 2. Load evidence
    evidence_list = await _load_case_evidence(case_id)
    
    # 3. RAG retrieval
    relevant_evidence = retriever.retrieve_decision_evidence(
        case_id=case_id,
        query=req.focus_query if req else None,
        all_evidence=evidence_list
    )

    # 4. ML Fraud & Anomaly Analysis
    ml_risk = fraud_model.predict_risk(case_id, relevant_evidence)
    ml_anomaly = anomaly_model.detect_anomaly(case_id, relevant_evidence)
    ml_risk["anomaly_score"] = ml_anomaly["anomaly_score"]
    
    shap_contribs = shap_explainer.generate_attributions(
        case_id=case_id,
        risk_score=ml_risk["risk_score"],
        evidence_list=relevant_evidence
    )
    ml_risk["feature_contributions"] = shap_contribs

    # 5. Deterministic Contradictions
    contradictions = contradiction_engine.detect_contradictions(relevant_evidence)

    # 6. Challenge Engine
    challenge_result = challenge_engine.challenge_case(
        case_id=case_id,
        initial_risk_score=ml_risk["risk_score"],
        evidence_list=relevant_evidence
    )

    # 7. DETERMINISTIC DECISION GATE
    decision_packet = decision_gate.evaluate(
        case_id=case_id,
        evidence_list=relevant_evidence,
        ml_fraud_result=ml_risk,
        contradictions=contradictions,
        challenge_result=challenge_result
    )

    # 8. Persist Decision Record in MongoDB
    await repo.save_decision(decision_packet.dict())

    return decision_packet

@router.get("/{case_id}/analysis", response_model=DecisionPacket)
async def get_case_analysis(case_id: str):
    """
    Retrieves the latest analysis and decision packet for a case from MongoDB.
    """
    dec_raw = await repo.get_latest_decision(case_id)
    if not dec_raw:
        return await run_case_analysis(case_id=case_id)

    return DecisionPacket(**dec_raw)
