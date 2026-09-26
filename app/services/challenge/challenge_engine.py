from typing import List, Dict, Any
from app.schemas.evidence import EvidenceObject
from app.schemas.decision import ChallengePacket
from app.services.llm.llm_service import llm_service
from app.core.logging import logger

class ChallengeEngine:
    """
    Challenge Engine (Adversarial / Devil's Advocate Decision Stress-Tester).
    Interrogates initial high-risk assumptions by actively searching for
    mitigating explanations or counter-evidence.
    """

    def challenge_case(
        self,
        case_id: str,
        initial_risk_score: float,
        evidence_list: List[EvidenceObject]
    ) -> ChallengePacket:
        
        logger.info(f"Running Challenge Engine for case {case_id} (Initial ML Risk: {initial_risk_score})")

        hypothesis = "Transaction is fraudulent due to location/device anomaly."
        
        # Search for potential counter-evidence
        counter_evidence_ids = []
        counter_evidence_found = False
        notes = []

        for ev in evidence_list:
            pred = ev.claim.predicate.lower()
            val = str(ev.claim.value).lower()

            if "device_replaced" in pred or "device_update" in pred:
                counter_evidence_found = True
                counter_evidence_ids.append(ev.evidence_id)
                notes.append(f"Account holder updated registered device within the last 24 hours ({ev.claim.value}).")
            elif "travel_notice" in pred or "travel_flag" in pred:
                counter_evidence_found = True
                counter_evidence_ids.append(ev.evidence_id)
                notes.append(f"Pre-authorized travel notice was registered for Delhi ({ev.claim.value}).")
            elif "verified_kyc" in pred and "active" in val:
                notes.append("Customer KYC profile is active and verified in Mumbai.")

        if counter_evidence_found:
            summary = (
                f"Challenge Engine found {len(counter_evidence_ids)} piece(s) of mitigating counter-evidence. "
                + " ".join(notes)
                + " The geo-spatial anomaly has a plausible operational explanation, but identity confirmation remains mandatory."
            )
            adjusted_state = "INCOMPLETE"
        else:
            summary = (
                "Adversarial counter-evidence scan completed. No mitigating device updates, travel notices, "
                "or secondary authorizations were found to offset the location anomaly."
            )
            adjusted_state = "HIGH_RISK_CONFIRMED"

        return ChallengePacket(
            performed=True,
            hypothesis=hypothesis,
            counter_evidence_found=counter_evidence_found,
            counter_evidence_ids=counter_evidence_ids,
            challenge_summary=summary,
            original_risk_state="HIGH_RISK" if initial_risk_score > 0.70 else "LOW_RISK",
            adjusted_risk_state=adjusted_state
        )

challenge_engine = ChallengeEngine()
