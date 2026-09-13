import secrets
from datetime import datetime,timedelta
from .db import db_session,Followup

def _delay(urgency):
    return {'High':timedelta(hours=4),'Moderate':timedelta(days=1),'Low':timedelta(days=3)}.get((urgency or 'Low').title(),timedelta(days=1))

def schedule_followup(user_id,severity,urgency,concern):
    s=db_session()
    try:
        s.query(Followup).filter_by(user_id=user_id,status='pending').update({'status':'superseded'})
        f=Followup(id='fu:'+secrets.token_hex(10),user_id=user_id,concern=concern or 'Health assessment',previous_severity=int(severity or 5),previous_urgency=urgency or 'Low',due_date=datetime.utcnow()+_delay(urgency),status='pending')
        s.add(f);s.commit();return _to_dict(f)
    finally:s.close()

def get_followup(user_id):
    s=db_session()
    try:
        f=s.query(Followup).filter_by(user_id=user_id,status='pending').order_by(Followup.due_date.asc()).first();return _to_dict(f) if f else None
    finally:s.close()

def complete_followup(user_id,comparison,severity,notes):
    s=db_session()
    try:
        f=s.query(Followup).filter_by(user_id=user_id,status='pending').order_by(Followup.due_date.asc()).first()
        if not f:return None
        f.status='completed';f.completed_at=datetime.utcnow();f.comparison=comparison;f.current_severity=severity;f.notes=notes or '';s.commit();return _to_dict(f)
    finally:s.close()

def _to_dict(f):
    return {'id':f.id,'concern':f.concern,'previous_severity':f.previous_severity,'previous_urgency':f.previous_urgency,'due_date':f.due_date.isoformat(timespec='seconds'),'status':f.status,'completed_at':f.completed_at.isoformat(timespec='seconds') if f.completed_at else '','comparison':f.comparison,'current_severity':f.current_severity,'notes':f.notes}
