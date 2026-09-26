from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    case_id: str
    run_ml: bool = True
    run_rag: bool = True
    run_challenge: bool = True
    focus_query: Optional[str] = None

class MLAnalysisResult(BaseModel):
    fraud_risk_score: float
    anomaly_score: float
    is_anomaly: bool
    model_name: str = "XGBoost + Isolation Forest"
    shap_contributions: Dict[str, float] = {}

class AnalysisResponse(BaseModel):
    case_id: str
    status: str = "COMPLETED"
    ml_result: MLAnalysisResult
    claims_extracted_count: int
    contradictions_detected_count: int
    evidence_quality_score: str
    completeness_score: float
    decision_summary: str
