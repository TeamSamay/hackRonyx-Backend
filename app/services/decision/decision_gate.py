from typing import List, Dict, Any, Optional
from datetime import datetime
from app.schemas.evidence import EvidenceObject
from app.schemas.decision import (
    DecisionPacket,
    TrustStatus,
    RecommendationAction,
    MLFraudModel,
    ContradictionItem,
    MissingInformationItem,
    ChallengePacket
)
from app.services.llm.llm_service import llm_service
from app.core.logging import logger

class DeterministicDecisionGate:
    """
    DETERMINISTIC DECISION GATE (The Ultimate Authority).
    Enforces the 6 Final Trust States. The LLM cannot bypass or override these rules.
    """

    def evaluate(
        self,
        case_id: str,
        evidence_list: List[EvidenceObject],
        ml_fraud_result: Dict[str, Any],
        contradictions: List[ContradictionItem],
        challenge_result: ChallengePacket,
        missing_info: Optional[List[MissingInformationItem]] = None
    ) -> DecisionPacket:
        
        logger.info(f"Deterministic Decision Gate evaluating case {case_id}")

        fraud_risk = float(ml_fraud_result.get("risk_score", 0.5))
        anomaly_score = float(ml_fraud_result.get("anomaly_score", 0.0))
        model_name = str(ml_fraud_result.get("model", "xgboost"))
        shap_contribs = ml_fraud_result.get("feature_contributions", {})

        # Compute aggregate evidence quality
        if not evidence_list:
            overall_quality = "LOW"
            completeness = 0.0
        else:
            quality_scores = [1.0 if e.quality.overall_quality == "HIGH" else (0.6 if e.quality.overall_quality == "MEDIUM" else 0.3) for e in evidence_list]
            avg_quality_score = sum(quality_scores) / len(quality_scores)
            overall_quality = "HIGH" if avg_quality_score >= 0.8 else ("MEDIUM" if avg_quality_score >= 0.5 else "LOW")
            completeness = min(round(len(evidence_list) / 4.0, 2), 1.0) # Target min 4 evidence items for 100%

        # Missing Information items
        missing_items = missing_info or []
        if not missing_items:
            raw_missing = llm_service.identify_missing_evidence(case_id, "TRANSACTION", evidence_list)
            for rm in raw_missing:
                missing_items.append(MissingInformationItem(
                    item=rm["item"],
                    reason=rm["reason"],
                    priority=rm["priority"],
                    suggested_source=rm.get("suggested_source")
                ))

        # ========================================================
        # DETERMINISTIC RULES FOR THE 6 TRUST STATES
        # ========================================================
        
        # 1. Check for LOW_QUALITY
        if overall_quality == "LOW" or len(evidence_list) == 0:
            trust_status = TrustStatus.LOW_QUALITY
            recommendation = RecommendationAction.REQUEST_BETTER_SOURCES

        # 2. Check for CONFLICTING (Location mismatch, amount mismatch, claim clash)
        elif len(contradictions) > 0:
            trust_status = TrustStatus.CONFLICTING
            recommendation = RecommendationAction.HUMAN_REVIEW

        # 3. Check for NEED_MORE_INFO / INCOMPLETE
        elif completeness < 0.60 or (len(missing_items) > 0 and fraud_risk > 0.65):
            trust_status = TrustStatus.INCOMPLETE if completeness >= 0.40 else TrustStatus.NEED_MORE_INFO
            recommendation = RecommendationAction.REQUEST_DATA if trust_status == TrustStatus.INCOMPLETE else RecommendationAction.SPECIFY_REQUIRED_EVIDENCE

        # 4. Check for REFUSE (Extreme risk with unresolvable state)
        elif fraud_risk >= 0.95 and completeness < 0.50:
            trust_status = TrustStatus.REFUSE
            recommendation = RecommendationAction.REFUSE_ESCALATE

        # 5. SUFFICIENT (Clean evidence, low/acceptable risk, zero contradictions)
        else:
            trust_status = TrustStatus.SUFFICIENT
            recommendation = RecommendationAction.APPROVE if fraud_risk < 0.40 else RecommendationAction.PROCEED

        # Generate Evidence-Aware Synthesized Reasoning
        reasoning = llm_service.generate_reasoning(
            case_id=case_id,
            ml_risk=fraud_risk,
            contradictions_count=len(contradictions),
            evidence_quality=overall_quality,
            evidence_list=evidence_list
        )

        # Build Claims list for packet
        claims_list = [
            {
                "evidence_id": e.evidence_id,
                "subject": e.claim.subject,
                "predicate": e.claim.predicate,
                "value": e.claim.value,
                "source": f"{e.source.type}:{e.source.name}"
            }
            for e in evidence_list
        ]

        packet = DecisionPacket(
            case_id=case_id,
            trust_status=trust_status,
            fraud_model=MLFraudModel(
                risk_score=fraud_risk,
                model=model_name,
                anomaly_score=anomaly_score,
                feature_contributions=shap_contribs
            ),
            evidence_quality=overall_quality,
            completeness=completeness,
            evidence=evidence_list,
            claims=claims_list,
            contradictions=contradictions,
            missing_information=missing_items,
            reasoning=reasoning,
            challenge=challenge_result,
            recommendation=recommendation,
            audit={
                "timestamp": datetime.utcnow().isoformat(),
                "engine_version": "2.0.0",
                "gate": "DETERMINISTIC_DECISION_GATE",
                "rules_evaluated": ["LOW_QUALITY_RULE", "CONTRADICTION_GATE", "COMPLETENESS_GATE", "CHALLENGE_GATE"]
            }
        )

        logger.info(f"Decision Gate finalized: State={packet.trust_status}, Recommendation={packet.recommendation}")
        return packet

decision_gate = DeterministicDecisionGate()
