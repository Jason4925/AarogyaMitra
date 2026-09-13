import secrets
from datetime import datetime
from .db import db_session,TimelineEvent

def add_event(user_id,event_type,title,severity=None,urgency='',summary='',source='',metadata=None):
    e=TimelineEvent(id='tl:'+secrets.token_hex(10),user_id=user_id,event_type=event_type,title=title,severity=severity,urgency=urgency or '',summary=summary or '',source=source or '',timestamp=datetime.utcnow(),metadata_json=metadata or {})
    s=db_session()
    try:
        s.add(e);s.commit();return {'id':e.id,'timestamp':e.timestamp.isoformat(timespec='seconds'),'event_type':e.event_type,'title':e.title,'severity':e.severity,'urgency':e.urgency,'summary':e.summary,'source':e.source,'metadata':e.metadata_json or {}}
    finally:s.close()

def get_timeline(user_id,limit=50):
    s=db_session()
    try:
        rows=s.query(TimelineEvent).filter_by(user_id=user_id).order_by(TimelineEvent.timestamp.desc()).limit(limit).all()
        return [{'id':e.id,'timestamp':e.timestamp.isoformat(timespec='seconds'),'event_type':e.event_type,'title':e.title,'severity':e.severity,'urgency':e.urgency,'summary':e.summary,'source':e.source,'metadata':e.metadata_json or {}} for e in rows]
    finally:s.close()
