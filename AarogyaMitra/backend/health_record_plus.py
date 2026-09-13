from datetime import datetime, timezone
import secrets, hashlib
from .db import db_session, HealthMeasurement, HealthDocument, HandoffShare, CaregiverAccess, EmergencyAcknowledgement, FeedbackTicket, Handoff

VALID_METRICS={'blood_pressure','blood_glucose','temperature','oxygen_saturation','heart_rate','weight','menstrual_cycle'}

def add_measurement(user_id, metric, value, unit='', measured_at=None, note='', source='user', verified=False, provenance=None):
    metric=metric.strip().lower()
    if metric not in VALID_METRICS: raise ValueError('Unsupported health measurement.')
    measured=measured_at or datetime.utcnow()
    s=db_session()
    try:
        row=HealthMeasurement(id='meas:'+secrets.token_hex(10),user_id=user_id,metric=metric,value=str(value).strip(),unit=unit.strip(),measured_at=measured,source=source,verified=verified,provenance=provenance or {'source':'user'},note=note.strip())
        s.add(row);s.commit();return measurement_dict(row)
    finally:s.close()

def measurement_dict(x):
    return {'id':x.id,'metric':x.metric,'value':x.value,'unit':x.unit,'measured_at':x.measured_at.isoformat(timespec='seconds'),'source':x.source,'verified':x.verified,'note':x.note,'provenance':x.provenance or {}}

def list_measurements(user_id, limit=100):
    s=db_session()
    try:return [measurement_dict(x) for x in s.query(HealthMeasurement).filter_by(user_id=user_id).order_by(HealthMeasurement.measured_at.desc()).limit(limit).all()]
    finally:s.close()

def add_document(user_id, filename, content_type, storage_path='', extracted=None):
    s=db_session()
    try:
        row=HealthDocument(id='doc:'+secrets.token_hex(10),user_id=user_id,filename=filename,content_type=content_type,storage_path=storage_path,extracted=extracted or {},confirmed=False)
        s.add(row);s.commit();return document_dict(row)
    finally:s.close()

def document_dict(x):
    return {'id':x.id,'filename':x.filename,'content_type':x.content_type,'storage_path':x.storage_path,'extracted':x.extracted or {},'confirmed':x.confirmed,'created_at':x.created_at.isoformat(timespec='seconds')}

def confirm_document(user_id, doc_id):
    s=db_session()
    try:
        row=s.query(HealthDocument).filter_by(id=doc_id,user_id=user_id).first()
        if not row:return None
        row.confirmed=True;s.commit();return document_dict(row)
    finally:s.close()

def list_documents(user_id, limit=50):
    s=db_session()
    try:return [document_dict(x) for x in s.query(HealthDocument).filter_by(user_id=user_id).order_by(HealthDocument.created_at.desc()).limit(limit).all()]
    finally:s.close()

def create_share(user_id, handoff_id, expiry_hours=24, included=None):
    raw_token=secrets.token_urlsafe(24); access_code=''.join(str(secrets.randbelow(10)) for _ in range(6))
    token_hash=hashlib.sha256(raw_token.encode()).hexdigest(); code_hash=hashlib.sha256(access_code.encode()).hexdigest()
    from datetime import timedelta
    expires=datetime.utcnow()+timedelta(hours=max(1,min(expiry_hours,168)))
    s=db_session()
    try:
        row=HandoffShare(id='share:'+secrets.token_hex(10),user_id=user_id,handoff_id=handoff_id,access_code_hash=code_hash,token_hash=token_hash,expires_at=expires,included=included or ['handoff','report','timeline'])
        s.add(row);s.commit();return {'id':row.id,'token':raw_token,'access_code':access_code,'expires_at':expires.isoformat(timespec='seconds'),'included':row.included}
    finally:s.close()

def verify_share(token, access_code):
    token_hash=hashlib.sha256(token.encode()).hexdigest(); code_hash=hashlib.sha256(access_code.encode()).hexdigest()
    s=db_session()
    try:
        row=s.query(HandoffShare).filter_by(token_hash=token_hash,revoked=False).first()
        if not row or row.expires_at < datetime.utcnow() or not hashlib.sha256(access_code.encode()).hexdigest()==row.access_code_hash: return None
        row.accessed_at=datetime.utcnow();s.commit(); h=s.query(Handoff).filter_by(id=row.handoff_id,user_id=row.user_id).first()
        return {'share':{'id':row.id,'expires_at':row.expires_at.isoformat(timespec='seconds'),'included':row.included,'accessed_at':row.accessed_at.isoformat(timespec='seconds') if row.accessed_at else None},'handoff':h.data if h else {}}
    finally:s.close()

def revoke_share(user_id, share_id):
    s=db_session()
    try:
        row=s.query(HandoffShare).filter_by(id=share_id,user_id=user_id).first()
        if not row:return False
        row.revoked=True;s.commit();return True
    finally:s.close()

def list_shares(user_id):
    s=db_session()
    try:return [{'id':x.id,'expires_at':x.expires_at.isoformat(timespec='seconds'),'revoked':x.revoked,'accessed_at':x.accessed_at.isoformat(timespec='seconds') if x.accessed_at else None,'included':x.included or []} for x in s.query(HandoffShare).filter_by(user_id=user_id).order_by(HandoffShare.created_at.desc()).limit(50).all()]
    finally:s.close()

def set_caregiver(user_id,name,contact,permissions,expires_at=None):
    s=db_session()
    try:
        s.query(CaregiverAccess).filter_by(patient_user_id=user_id,active=True).update({'active':False})
        row=CaregiverAccess(id='cg:'+secrets.token_hex(10),patient_user_id=user_id,caregiver_name=name.strip(),caregiver_contact=contact.strip(),permissions=permissions or ['emergency'],expires_at=expires_at,active=True)
        s.add(row);s.commit();return {'id':row.id,'caregiver_name':row.caregiver_name,'caregiver_contact':row.caregiver_contact,'permissions':row.permissions,'expires_at':row.expires_at.isoformat(timespec='seconds') if row.expires_at else None,'active':row.active}
    finally:s.close()

def get_caregiver(user_id):
    s=db_session()
    try:
        x=s.query(CaregiverAccess).filter_by(patient_user_id=user_id,active=True).order_by(CaregiverAccess.created_at.desc()).first()
        return {'id':x.id,'caregiver_name':x.caregiver_name,'caregiver_contact':x.caregiver_contact,'permissions':x.permissions or [],'expires_at':x.expires_at.isoformat(timespec='seconds') if x.expires_at else None,'active':x.active} if x else None
    finally:s.close()

def acknowledge_emergency(user_id,event_id=None):
    s=db_session()
    try:
        row=EmergencyAcknowledgement(id='ack:'+secrets.token_hex(10),user_id=user_id,emergency_event_id=event_id,acknowledged=True);s.add(row);s.commit();return {'id':row.id,'acknowledged':True,'created_at':row.created_at.isoformat(timespec='seconds')}
    finally:s.close()

def add_feedback(user_id,category,description,severity='normal'):
    s=db_session()
    try:
        row=FeedbackTicket(id='fb:'+secrets.token_hex(10),user_id=user_id,category=category,severity=severity,description=description);s.add(row);s.commit();return {'id':row.id,'status':row.status,'created_at':row.created_at.isoformat(timespec='seconds')}
    finally:s.close()
