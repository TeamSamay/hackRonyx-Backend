from typing import List, Dict, Any, Tuple
from collections import defaultdict
from app.schemas.evidence import EvidenceObject
from app.schemas.decision import ContradictionItem, ContradictionSeverity
from app.services.llm.llm_service import llm_service
from app.core.logging import logger

class ContradictionEngine:
    """
    Deterministic Contradiction Engine.
    Detects factual clashes across claims (e.g. Location Mumbai != Delhi, Amount 85000 != 15000)
    using deterministic Python rules, and enriches them with LLM explanations.
    """

    # Semantic predicate equivalences (e.g. transaction_location vs device_location)
    SPATIAL_PREDICATES = {"transaction_location", "device_location", "location", "registered_city", "login_city"}

    def detect_contradictions(self, evidence_list: List[EvidenceObject]) -> List[ContradictionItem]:
        contradictions: List[ContradictionItem] = []
        if not evidence_list or len(evidence_list) < 2:
            return contradictions

        # Group by Subject
        by_subject: Dict[str, List[EvidenceObject]] = defaultdict(list)
        for ev in evidence_list:
            by_subject[ev.claim.subject].append(ev)

        # 1. Deterministic Exact Subject + Predicate Check
        for subject, items in by_subject.items():
            by_pred: Dict[str, List[EvidenceObject]] = defaultdict(list)
            for it in items:
                by_pred[it.claim.predicate].append(it)

            for pred, pred_items in by_pred.items():
                if len(pred_items) > 1:
                    values = list({str(p.claim.value).strip().lower() for p in pred_items})
                    if len(values) > 1:
                        # Direct Conflict!
                        desc = llm_service.explain_contradiction(
                            subject=subject,
                            predicate=pred,
                            conflicting_evidence=pred_items
                        )
                        item = ContradictionItem(
                            evidence_ids=[p.evidence_id for p in pred_items],
                            subject=subject,
                            predicate=pred,
                            conflicting_values=[p.claim.value for p in pred_items],
                            severity=ContradictionSeverity.CRITICAL if "location" in pred or "amount" in pred else ContradictionSeverity.HIGH,
                            description=desc,
                            resolution_suggestion="Obtain GPS telemetry or physical branch verification."
                        )
                        contradictions.append(item)

        # 2. Spatio-Temporal Cross-Predicate Check (e.g. transaction_location Mumbai vs device_location Delhi)
        location_items = [e for e in evidence_list if e.claim.predicate.lower() in self.SPATIAL_PREDICATES]
        if len(location_items) >= 2:
            loc_values = list({str(e.claim.value).strip().lower() for e in location_items})
            if len(loc_values) > 1:
                # Check if we already registered this exact contradiction
                already_found = any(set(c.evidence_ids) == set([e.evidence_id for e in location_items]) for c in contradictions)
                if not already_found:
                    desc = (
                        f"Physical & Telemetry Location Clash: Transaction occurred in '{location_items[0].claim.value}' "
                        f"while device connection was initiated from '{location_items[1].claim.value}'. "
                        "Simultaneous presence in two distinct geographic locations within minutes indicates high fraud risk."
                    )
                    contradictions.append(ContradictionItem(
                        evidence_ids=[e.evidence_id for e in location_items],
                        subject=location_items[0].claim.subject,
                        predicate="geo_spatial_presence",
                        conflicting_values=[e.claim.value for e in location_items],
                        severity=ContradictionSeverity.CRITICAL,
                        description=desc,
                        resolution_suggestion="Dispatch SMS OTP or require interactive device confirmation."
                    ))

        logger.info(f"Contradiction Engine evaluated {len(evidence_list)} evidence objects: found {len(contradictions)} contradiction(s).")
        return contradictions

contradiction_engine = ContradictionEngine()
