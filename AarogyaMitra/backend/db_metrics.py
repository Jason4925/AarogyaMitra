from sqlalchemy import func
from .db import db_session, User, Conversation, Report, AIEvent

def ai_analytics():
    s=db_session()
    try:
        conv=s.query(func.count(Conversation.id)).filter(Conversation.role=='user').scalar() or 0
        users=s.query(func.count(User.user_id)).filter(User.role=='user').scalar() or 0
        reports=s.query(func.count(Report.id)).scalar() or 0
        types=['emergency_detected','low_confidence','unsupported_question','human_escalation','api_failure']
        counts={t:s.query(func.count(AIEvent.id)).filter(AIEvent.event_type==t).scalar() or 0 for t in types}
        correction=s.query(func.count(AIEvent.id)).filter(AIEvent.event_type=='user_correction').scalar() or 0
        fallback=s.query(func.count(AIEvent.id)).filter(AIEvent.event_type=='fallback_response').scalar() or 0
        return {'total_conversations':conv,'assessment_completion':round(min(100,reports/max(1,users)*100),1),'fallback_responses':round(fallback/max(1,conv)*100,1),'user_corrections':round(correction/max(1,conv)*100,1),'safety_escalations':counts['emergency_detected'],'uncertain_responses':counts['low_confidence'],'safety_events':counts}
    finally:s.close()

def log_ai_event(event_type,user_id=None,details=None):
    s=db_session()
    try: from datetime import datetime; from .db import AIEvent;s.add(AIEvent(event_type=event_type,user_id=user_id,details=details or {},created_at=datetime.utcnow()));s.commit()
    finally:s.close()

def dashboard_signal(signal_type='refresh'):
    from .db import DashboardSignal
    from datetime import datetime
    s=db_session()
    try:s.add(DashboardSignal(signal_type=signal_type,created_at=datetime.utcnow()));s.commit()
    finally:s.close()
