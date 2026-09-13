import secrets
from datetime import datetime
from .db import db_session,Handoff

def create_handoff(user,payload,risk,report,timeline,questions_asked=0):
    data={'id':'ho:'+secrets.token_hex(10),'user_id':user.user_id if hasattr(user,'user_id') else user.get('user_id'),'patient_name':user.name if hasattr(user,'name') else user.get('name','Patient'),'generated_at':datetime.utcnow().isoformat(timespec='seconds'),'chief_concern':payload.get('mainProblem',''),'duration':payload.get('duration',''),'severity':payload.get('severity',''),'associated_symptoms':payload.get('symptoms',[]) or [],'relevant_history':payload.get('conditions',[]) or [],'medications':payload.get('medications',''),'allergies':payload.get('allergies',''),'red_flags_checked':risk.get('red_flags',[]) or [],'risk':risk,'questions_answered':questions_asked,'key_findings':report.get('key_findings',[]) or [],'patient_description':payload.get('mainProblem',''),'timeline':timeline,'next_steps':report.get('next_steps') or risk.get('recommended_action','')}
    s=db_session()
    try:s.add(Handoff(id=data['id'],user_id=data['user_id'],data=data,created_at=datetime.utcnow()));s.commit();return data
    finally:s.close()
def latest_handoff(user_id):
    s=db_session()
    try:
        h=s.query(Handoff).filter_by(user_id=user_id).order_by(Handoff.created_at.desc()).first();return h.data if h else None
    finally:s.close()
