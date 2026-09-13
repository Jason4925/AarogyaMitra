from datetime import datetime
from .db import db_session, Consent

CONSENT_TYPES = {
    'ai_assistance': 'AI health assistance',
    'health_storage': 'Health data storage',
    'doctor_handoff': 'Doctor handoff sharing',
    'emergency_contact': 'Emergency contact escalation',
    'population_analytics': 'De-identified population analytics',
}

def get_consents(user_id):
    s=db_session()
    try:
        rows=s.query(Consent).filter_by(user_id=user_id).all()
        out={k:False for k in CONSENT_TYPES}
        for r in rows: out[r.consent_type]=bool(r.granted)
        return out
    finally:s.close()

def set_consents(user_id, values):
    s=db_session()
    try:
        for key,label in CONSENT_TYPES.items():
            if key not in values: continue
            row=s.query(Consent).filter_by(user_id=user_id,consent_type=key).first()
            if not row:
                row=Consent(user_id=user_id,consent_type=key,granted=bool(values[key]),version='1.0',updated_at=datetime.utcnow())
                s.add(row)
            else:
                row.granted=bool(values[key]);row.updated_at=datetime.utcnow()
        s.commit()
    finally:s.close()
    return get_consents(user_id)
