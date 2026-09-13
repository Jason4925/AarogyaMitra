from datetime import datetime
from .db import db_session, SafetyRule, RecommendationRecord
from .risk_engine import calculate_risk

def evaluate_rule_case(payload):
    risk=calculate_risk(payload or {})
    expectations=payload.get('expected_levels') or []
    passed=(not expectations) or risk.get('level') in expectations
    return {'risk':risk,'passed':passed,'expectations':expectations}

def governance_metrics():
    s=db_session()
    try:
        total=s.query(SafetyRule).count(); active=s.query(SafetyRule).filter_by(status='active').count(); reviewed=s.query(SafetyRule).filter(SafetyRule.status.in_(['clinically_reviewed','active'])).count(); recs=s.query(RecommendationRecord).count()
        return {'total_rules':total,'active_rules':active,'clinically_reviewed_rules':reviewed,'recommendation_records':recs,'review_coverage_pct':round(reviewed/max(1,total)*100,1)}
    finally:s.close()
