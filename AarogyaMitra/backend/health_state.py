import re
from datetime import datetime
from .db import db_session, HealthState

EMERGENCY_TERMS=['severe bleeding','heavy bleeding','uncontrolled bleeding','difficulty breathing',"can't breathe",'cannot breathe','severe chest pain','unconscious','not responding','stroke symptoms','signs of stroke','seizure','loss of consciousness']
SYMPTOMS=['fever','headache','cough','sore throat','fatigue','nausea','vomiting','diarrhea','diarrhoea','abdominal pain','back pain','joint pain','body pain','chest pain','breathlessness','shortness of breath','dizziness','rash','itching','weakness','stomach pain','runny nose','sneezing']
def update_health_state(user_id,text):
    s=db_session()
    try:
        st=s.get(HealthState,user_id)
        if not st: st=HealthState(user_id=user_id,symptoms=[],red_flags=[],duration='',severity=None);s.add(st)
        low=text.lower(); syms=list(st.symptoms or []); flags=list(st.red_flags or [])
        for x in SYMPTOMS:
            if x in low and x not in syms: syms.append(x)
        for x in EMERGENCY_TERMS:
            if x in low and x not in flags: flags.append(x)
        m=re.search(r'\b(\d{1,2})\s*(?:day|days|week|weeks|month|months)\b',low)
        if m: st.duration=m.group(0)
        sev=re.search(r'\b(?:severity|pain)\s*(?:is|of)?\s*(10|[1-9])\b',low)
        if sev: st.severity=int(sev.group(1))
        st.symptoms=syms;st.red_flags=flags;st.last_updated=datetime.utcnow();s.commit();return get_health_state(user_id)
    finally:s.close()
def get_health_state(user_id):
    s=db_session()
    try:
        st=s.get(HealthState,user_id)
        if not st:return {'symptoms':[],'duration':'','severity':None,'red_flags':[],'last_updated':''}
        return {'symptoms':st.symptoms or [],'duration':st.duration or '','severity':st.severity,'red_flags':st.red_flags or [],'last_updated':st.last_updated.isoformat(timespec='seconds') if st.last_updated else ''}
    finally:s.close()
def reset_health_state(user_id):
    s=db_session()
    try:s.query(HealthState).filter_by(user_id=user_id).delete();s.commit()
    finally:s.close()
