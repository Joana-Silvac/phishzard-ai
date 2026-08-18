

from .heuristics import run_all_heuristics
from .models import AnalysisReport, EmailMessage

#faixa de risco. 

RISK_THRESHOLDS = {
    "alto": 0.7,
    "medio": 0.4,
}


def _classify_risk(score: float) -> str:
    if score >= RISK_THRESHOLDS["alto"]:
        return "alto"
    if score >= RISK_THRESHOLDS["medio"]:
        return "medio"
    return "baixo"


def analyze_email(email: EmailMessage) -> AnalysisReport:
   
    results = run_all_heuristics(email)

    triggered = [r for r in results if r.triggered]

    if triggered:
        base_score = max(r.score for r in triggered)
        bonus = 0.05 * (len(triggered) - 1)
        risk_score = min(1.0, base_score + bonus)
    else:
        risk_score = 0.0

    reasons = [r.reason for r in triggered if r.reason]

    return AnalysisReport(
        risk_score=round(risk_score, 2),
        risk_level=_classify_risk(risk_score),
        reasons=reasons,
        details=results,
    )
