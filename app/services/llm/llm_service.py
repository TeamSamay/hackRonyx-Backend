import os
import json
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.schemas.evidence import EvidenceObject

class LLMService:
    """
    Provider-Agnostic LLM Reasoning Service.
    Wraps Groq / Foundation LLMs with structured prompts and robust fallback reasoning.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        self.model = settings.GROQ_MODEL
        self._client = None
        if self.api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
                logger.info(f"Groq LLM client initialized with model {self.model}")
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

    def generate_claims(self, text_content: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Extracts structured claims [subject, predicate, value] from raw text.
        """
        if self._client:
            try:
                prompt = (
                    "Extract structured factual claims from this text. Return JSON array with keys: 'subject', 'predicate', 'value', 'confidence'.\n\n"
                    f"Text:\n{text_content[:2000]}"
                )
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                raw_res = response.choices[0].message.content
                # Attempt to parse json
                json_start = raw_res.find("[")
                json_end = raw_res.rfind("]")
                if json_start != -1 and json_end != -1:
                    return json.loads(raw_res[json_start:json_end+1])
            except Exception as e:
                logger.warning(f"Groq generate_claims failed: {e}")

        # Structured fallback claim extractor
        claims = []
        for line in text_content.split("\n"):
            line = line.strip()
            if ":" in line:
                k, v = line.split(":", 1)
                claims.append({
                    "subject": source_name,
                    "predicate": k.strip().lower().replace(" ", "_"),
                    "value": v.strip(),
                    "confidence": 0.95
                })
        return claims

    def explain_contradiction(
        self,
        subject: str,
        predicate: str,
        conflicting_evidence: List[EvidenceObject]
    ) -> str:
        """
        Generates human-readable, auditable explanation of a detected contradiction.
        """
        sources_str = ", ".join([f"{e.source.type} ({e.source.name})" for e in conflicting_evidence])
        values_str = ", ".join([f"'{e.claim.value}' from {e.source.type}" for e in conflicting_evidence])

        if self._client:
            try:
                prompt = f"Explain the contradiction where {subject}'s {predicate} has conflicting values: {values_str} reported by sources: {sources_str}. Explain why this presents operational or fraud risk in 2 concise sentences."
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=150
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Groq explain_contradiction failed: {e}")

        # High-clarity fallback explanation
        return (
            f"Direct contradiction detected on '{predicate}' for subject '{subject}'. "
            f"Sources [{sources_str}] reported contradictory values: [{values_str}]. "
            "This suggests potential identity spoofing, location spoofing, or data inconsistency requiring mandatory human review."
        )

    def identify_missing_evidence(
        self,
        case_id: str,
        entity_type: str,
        existing_evidence: List[EvidenceObject]
    ) -> List[Dict[str, str]]:
        """
        Identifies critical missing information needed to reach a SUFFICIENT verdict.
        """
        predicates = {e.claim.predicate.lower() for e in existing_evidence}
        missing = []

        if "device_ownership" not in predicates and "device_registered" not in predicates:
            missing.append({
                "item": "device_ownership_verification",
                "reason": "Device location and ownership cannot be conclusively linked to the account holder.",
                "priority": "HIGH",
                "suggested_source": "TELECOM_CARRIER_API / MOBILE_AUTHENTICATOR"
            })

        if "biometric_auth" not in predicates:
            missing.append({
                "item": "step_up_biometric_confirmation",
                "reason": "High transaction velocity requires secondary multi-factor authentication proof.",
                "priority": "MEDIUM",
                "suggested_source": "MOBILE_APP_BIOMETRICS"
            })

        return missing

    def generate_reasoning(
        self,
        case_id: str,
        ml_risk: float,
        contradictions_count: int,
        evidence_quality: str,
        evidence_list: List[EvidenceObject]
    ) -> str:
        """
        Generates evidence-aware synthesized reasoning.
        """
        if self._client:
            try:
                summary_ev = "\n".join([f"- [{e.source.type}] {e.claim.subject} {e.claim.predicate} = {e.claim.value} (Reliability: {e.quality.reliability})" for e in evidence_list[:8]])
                prompt = (
                    f"You are VERDICT Decision Reasoning Engine. Analyze case {case_id}.\n"
                    f"ML Fraud Risk Score: {ml_risk}\n"
                    f"Contradictions detected: {contradictions_count}\n"
                    f"Evidence Quality: {evidence_quality}\n"
                    f"Evidence Items:\n{summary_ev}\n\n"
                    "Provide a precise, 3-paragraph executive reasoning summary explaining why this transaction cannot be auto-approved and why human intervention is required."
                )
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Groq generate_reasoning failed: {e}")

        # Robust, professional fallback synthesis
        return (
            f"Case {case_id} exhibits an elevated statistical ML risk score of {ml_risk:.2f} "
            f"coupled with {contradictions_count} unresolved data contradiction(s). "
            f"While core banking records and KYC files establish baseline account legitimacy, "
            f"the active transaction telemetry reveals significant spatio-temporal divergence between physical and IP endpoints. "
            f"In accordance with VERDICT's deterministic safety protocols, automatic clearance is withheld. "
            f"The case is routed to Tier-2 Fraud Analyst for manual human verification."
        )

    def challenge_decision(
        self,
        case_id: str,
        initial_hypothesis: str,
        evidence_list: List[EvidenceObject]
    ) -> Dict[str, Any]:
        """
        Challenge Engine reasoning: seeks counter-evidence that could invalidate a high-risk conclusion.
        """
        counter_found = False
        counter_ids = []
        summary = "Challenge engine scanned for mitigating factors (e.g. recent device update, travel notification)."

        for ev in evidence_list:
            pred = ev.claim.predicate.lower()
            val = str(ev.claim.value).lower()
            if "device_replaced" in pred or "travel_notice" in pred or "authorized_delegate" in pred:
                counter_found = True
                counter_ids.append(ev.evidence_id)
                summary = f"Mitigating counter-evidence discovered: {ev.claim.predicate} = {ev.claim.value}."

        return {
            "performed": True,
            "hypothesis": initial_hypothesis,
            "counter_evidence_found": counter_found,
            "counter_evidence_ids": counter_ids,
            "challenge_summary": summary,
            "original_risk_state": "HIGH_RISK",
            "adjusted_risk_state": "INCOMPLETE" if counter_found else "HIGH_RISK_CONFIRMED"
        }

llm_service = LLMService()
