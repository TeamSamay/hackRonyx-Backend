from app.schemas.evidence import ReliabilityLevel
from app.schemas.decision import TrustStatus, RecommendationAction
from app.services.evidence.normalizer import normalizer
from app.services.contradiction.contradiction_engine import contradiction_engine
from app.services.challenge.challenge_engine import challenge_engine
from app.services.decision.decision_gate import decision_gate

def test_evidence_normalization_and_quality():
    ev = normalizer.from_database_record(
        case_id="TEST-001",
        table_name="transactions",
        record_id="TX100",
        subject="TX100",
        predicate="transaction_location",
        value="Mumbai",
        reliability=ReliabilityLevel.HIGH
    )
    assert ev.evidence_id.startswith("E-DB")
    assert ev.claim.predicate == "transaction_location"
    assert ev.claim.value == "Mumbai"
    assert ev.quality.reliability == ReliabilityLevel.HIGH
    assert ev.quality.overall_quality == "HIGH"

def test_contradiction_detection():
    ev1 = normalizer.from_database_record(
        case_id="TEST-001",
        table_name="transactions",
        record_id="TX100",
        subject="TX100",
        predicate="transaction_location",
        value="Mumbai"
    )
    ev2 = normalizer.from_database_record(
        case_id="TEST-001",
        table_name="telemetry",
        record_id="DEV100",
        subject="TX100",
        predicate="device_location",
        value="Delhi"
    )
    contradictions = contradiction_engine.detect_contradictions([ev1, ev2])
    assert len(contradictions) >= 1
    assert "Mumbai" in contradictions[0].conflicting_values
    assert "Delhi" in contradictions[0].conflicting_values

def test_deterministic_decision_gate_conflicting():
    ev1 = normalizer.from_database_record("TEST-001", "tx", "1", "TX100", "transaction_location", "Mumbai")
    ev2 = normalizer.from_database_record("TEST-001", "dev", "2", "TX100", "device_location", "Delhi")
    evidence_list = [ev1, ev2]
    
    contradictions = contradiction_engine.detect_contradictions(evidence_list)
    challenge = challenge_engine.challenge_case("TEST-001", 0.91, evidence_list)
    
    packet = decision_gate.evaluate(
        case_id="TEST-001",
        evidence_list=evidence_list,
        ml_fraud_result={"risk_score": 0.91, "model": "xgboost"},
        contradictions=contradictions,
        challenge_result=challenge
    )
    
    assert packet.trust_status == TrustStatus.CONFLICTING
    assert packet.recommendation == RecommendationAction.HUMAN_REVIEW
    assert packet.fraud_model.risk_score == 0.91
