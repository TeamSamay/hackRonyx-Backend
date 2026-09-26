from typing import Dict, Any, Optional
from app.schemas.evidence import SourceType, ReliabilityLevel, FreshnessLevel, QualityMetrics

class EvidenceQualityEngine:
    """
    Deterministic Evidence Quality Assessment Engine.
    Evaluates evidence source pedigree, freshness, OCR confidence, and completeness.
    Does NOT claim 'absolute truth', but provides calibrated quality scoring.
    """

    RELIABILITY_WEIGHTS = {
        ReliabilityLevel.HIGH: 1.0,
        ReliabilityLevel.MEDIUM: 0.7,
        ReliabilityLevel.LOW: 0.4,
        ReliabilityLevel.UNVERIFIED: 0.2
    }

    FRESHNESS_WEIGHTS = {
        FreshnessLevel.CURRENT: 1.0,
        FreshnessLevel.RECENT: 0.8,
        FreshnessLevel.OUTDATED: 0.5,
        FreshnessLevel.HISTORICAL: 0.3
    }

    SOURCE_DEFAULT_RELIABILITY = {
        SourceType.DATABASE: (ReliabilityLevel.HIGH, True),
        SourceType.API: (ReliabilityLevel.HIGH, True),
        SourceType.DEVICE_SIGNAL: (ReliabilityLevel.HIGH, True),
        SourceType.PDF: (ReliabilityLevel.MEDIUM, False),
        SourceType.IMAGE: (ReliabilityLevel.MEDIUM, False),
        SourceType.EXCEL: (ReliabilityLevel.MEDIUM, False),
        SourceType.CSV: (ReliabilityLevel.MEDIUM, False),
        SourceType.EXTERNAL: (ReliabilityLevel.LOW, False),
        SourceType.MANUAL: (ReliabilityLevel.LOW, False)
    }

    def assess_quality(
        self,
        source_type: SourceType,
        explicit_reliability: Optional[ReliabilityLevel] = None,
        explicit_freshness: Optional[FreshnessLevel] = None,
        ocr_confidence: Optional[float] = None,
        completeness: float = 1.0,
        has_traceability: bool = True
    ) -> QualityMetrics:
        
        default_rel, is_primary = self.SOURCE_DEFAULT_RELIABILITY.get(source_type, (ReliabilityLevel.MEDIUM, False))
        reliability = explicit_reliability or default_rel
        freshness = explicit_freshness or FreshnessLevel.CURRENT

        # Base score computation
        rel_val = self.RELIABILITY_WEIGHTS.get(reliability, 0.5)
        fresh_val = self.FRESHNESS_WEIGHTS.get(freshness, 0.5)
        
        score = (rel_val * 0.45) + (fresh_val * 0.25) + (completeness * 0.20)
        
        if ocr_confidence is not None:
            score = (score * 0.8) + (ocr_confidence * 0.2)
            
        if not has_traceability:
            score *= 0.85 # Penalty for untraceable claims

        if score >= 0.78:
            overall_quality = "HIGH"
        elif score >= 0.50:
            overall_quality = "MEDIUM"
        else:
            overall_quality = "LOW"

        return QualityMetrics(
            reliability=reliability,
            freshness=freshness,
            completeness=round(completeness, 2),
            ocr_confidence=round(ocr_confidence, 2) if ocr_confidence is not None else None,
            is_primary_source=is_primary,
            overall_quality=overall_quality
        )

quality_engine = EvidenceQualityEngine()
