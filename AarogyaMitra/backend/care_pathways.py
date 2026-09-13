from datetime import datetime

def build_care_pathway(payload: dict, risk: dict) -> dict:
    level = str(risk.get('level') or 'Low').title()
    score = int(risk.get('score') or 0)
    high_priority = level in {'High','Critical'}
    if high_priority:
        pathway=[
            {'step':1,'title':'Seek urgent professional evaluation','detail':'For life-threatening symptoms, use emergency services immediately and do not delay care for additional AI questions.'},
            {'step':2,'title':'Use emergency-capable healthcare routing','detail':'Prefer an emergency department or facility capable of handling the presenting concern.'},
            {'step':3,'title':'Share the AarogyaMitra handoff','detail':'Bring the structured summary with symptoms, timing, severity, history, medicines, allergies and risk factors.'},
            {'step':4,'title':'Follow clinician decisions','detail':'Diagnosis, medicines, investigations and treatment changes should be decided by a qualified clinician.'},
            {'step':5,'title':'Complete follow-up after care','detail':'Record whether symptoms improve, remain the same or worsen.'}]
        action='Urgent professional evaluation is recommended.'; mode='emergency-first'
    elif level=='Moderate':
        pathway=[
            {'step':1,'title':'Arrange a timely professional assessment','detail':'Persistent or concerning symptoms should be reviewed by a qualified healthcare professional.'},
            {'step':2,'title':'Choose an appropriate facility','detail':'Use risk-aware routing to prefer a suitable clinic, hospital or specialist service.'},
            {'step':3,'title':'Prepare your handoff','detail':'Share your symptom history, severity, duration, relevant history, medicines and allergies.'},
            {'step':4,'title':'Discuss the care plan','detail':'A clinician can decide which examinations, investigations or treatment options are appropriate.'},
            {'step':5,'title':'Complete a follow-up','detail':'Record whether symptoms are better, unchanged or worse.'}]
        action='Timely professional evaluation is recommended.'; mode='clinical-evaluation'
    else:
        pathway=[
            {'step':1,'title':'Monitor symptoms','detail':'Track severity, duration and any new warning signs.'},
            {'step':2,'title':'Use relevant preventive guidance','detail':'Choose practical self-care and public-health information relevant to your concern.'},
            {'step':3,'title':'Seek routine professional care if needed','detail':'Arrange a clinician review if symptoms persist, worsen or remain unexplained.'},
            {'step':4,'title':'Complete a follow-up','detail':'Record whether you are improving, unchanged or worse.'}]
        action='Monitor symptoms and use routine professional care if symptoms persist or worsen.'; mode='routine-monitoring'
    return {'generated_at':datetime.utcnow().isoformat(timespec='seconds'),'risk_level':level,'risk_score':score,'priority_action':action,'pathway':pathway,'routing_mode':mode,'disclaimer':'Decision-support guidance, not a diagnosis or prescription.'}
