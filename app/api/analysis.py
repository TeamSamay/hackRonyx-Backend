from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models import CaseModel, EvidenceModel, DecisionModel
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, MLAnalysisResult
from app.schemas.evidence import EvidenceObject, SourceMetadata, ClaimPayload, QualityMetrics, TraceabilityInfo, SourceType, ReliabilityLevel, FreshnessLevel
from app.schemas.decision import DecisionPacket
from app.services.rag.retriever import retriever
from app.services.ml.fraud_model import fraud_model
from app.services.ml.anomaly_model import anomaly_model
from app.services.ml.explainability import shap_explainer
from app.services.contradiction.contradiction_engine import contradiction_engine
from app.services.challenge.challenge_engine import challenge_engine
from app.services.decision.decision_gate import decision_gate
from app.core.logging import logger

router = APIRouter(prefix="/api/cases", tags=["Analysis"])

async def _load_case_evidence(case_id: str, db: AsyncSession) -> list[EvidenceObject]:
    result = await db.execute(select(EvidenceModel).where(EvidenceModel.case_id == case_id))
    rows = result.scalars().all()
    evidence_objects = []
    for r in rows:
        ev = EvidenceObject(
            evidence_id=r.evidence_id,
            case_id=r.case_id,
            source=SourceMetadata(
                type=SourceType(r.source_type) if r.source_type in SourceType.__members__ else SourceType.DATABASE,
                system=r.source_system,
                name=r.source_reference
            ),
            claim=ClaimPayload(
                subject=r.claim_subject,
                predicate=r.claim_predicate,
                value=r.claim_value,
                raw_statement=r.raw_statement
            ),
            timestamp=r.timestamp.isoformat() if r.timestamp else "",
            quality=QualityMetrics(
                reliability=ReliabilityLevel(r.reliability) if r.reliability in ReliabilityLevel.__members__ else ReliabilityLevel.HIGH,
                freshness=FreshnessLevel(r.freshness) if r.freshness in FreshnessLevel.__members__ else FreshnessLevel.CURRENT,
                completeness=r.completeness or 1.0,
                ocr_confidence=r.ocr_confidence,
                overall_quality=r.overall_quality or "HIGH"
            ),
            traceability=TraceabilityInfo(**(r.traceability or {})),
            raw_payload=r.raw_payload or {},
            created_at=r.created_at.isoformat() if r.created_at else ""
        )
        evidence_objects.append(ev)
    return evidence_objects

@router.post("/{case_id}/analyze", response_model=DecisionPacket)
async def run_case_analysis(
    case_id: str,
    req: AnalysisRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Full VERDICT Pipeline Execution:
    1. Load all case evidence
    2. RAG Retrieval of decision-critical items
    3. ML Risk & Anomaly scoring + SHAP
    4. Deterministic Contradiction Detection
    5. Challenge Engine counter-evidence evaluation
    6. DETERMINISTIC DECISION GATE evaluation
    7. Saves & returns the canonical DecisionPacket
    """
    logger.info(f"Triggered full analysis for case {case_id}")
    
    # 1. Load case
    case_res = await db.execute(select(CaseModel).where(CaseModel.case_id == case_id))
    case = case_res.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    # 2. Load evidence
    evidence_list = await _load_case_evidence(case_id, db)
    
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

    # 8. Persist Decision Record & update Case Trust Status
    case.trust_status = decision_packet.trust_status.value
    
    decision_record = DecisionModel(
        case_id=case_id,
        trust_status=decision_packet.trust_status.value,
        fraud_risk_score=decision_packet.fraud_model.risk_score,
        anomaly_score=decision_packet.fraud_model.anomaly_score or 0.0,
        evidence_quality=decision_packet.evidence_quality,
        completeness=decision_packet.completeness,
        recommendation=decision_packet.recommendation.value,
        reasoning=decision_packet.reasoning,
        packet_json=decision_packet.dict()
    )
    db.add(decision_record)
    await db.commit()

    return decision_packet

@router.get("/{case_id}/analysis", response_model=DecisionPacket)
async def get_case_analysis(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the latest analysis and decision packet for a case.
    """
    result = await db.execute(
        select(DecisionModel).where(DecisionModel.case_id == case_id).order_by(DecisionModel.id.desc())
    )
    dec = result.scalars().first()
    if not dec:
        # If not analyzed yet, run it automatically
        return await run_case_analysis(case_id=case_id, db=db)

    return DecisionPacket(**dec.packet_json)
