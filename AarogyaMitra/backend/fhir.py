from __future__ import annotations
from datetime import datetime
import uuid

def _ref(resource_type, value): return {'reference':f'{resource_type}/{value}'}

def patient_bundle(user:dict, record:dict)->dict:
    uid=user.get('user_id','patient'); pid=uid.replace(':','-')
    report=record.get('latest_report') or {}; risk=report.get('risk_engine') or report.get('risk') or record.get('risk') or {}
    symptoms=report.get('symptoms') or record.get('health_state',{}).get('symptoms') or []
    resources=[{'resource':{'resourceType':'Patient','id':pid,'name':[{'text':user.get('name','')}],'gender':(user.get('gender') or '').lower() or None}}]
    for i,symptom in enumerate(symptoms[:20],1):
        resources.append({'resource':{'resourceType':'Observation','id':f'observation-{i}','status':'final','code':{'text':str(symptom)},'subject':_ref('Patient',pid),'effectiveDateTime':report.get('created_at')}})
    if report.get('mainProblem'):
        resources.append({'resource':{'resourceType':'Condition','id':'condition-1','clinicalStatus':{'text':'active'},'code':{'text':str(report['mainProblem'])},'subject':_ref('Patient',pid)}})
    if user.get('allergies'):
        resources.append({'resource':{'resourceType':'AllergyIntolerance','id':'allergy-1','clinicalStatus':{'text':'active'},'code':{'text':str(user['allergies'])},'patient':_ref('Patient',pid)}})
    if user.get('conditions'):
        for i,c in enumerate(user['conditions'][:10],1):
            resources.append({'resource':{'resourceType':'Condition','id':f'history-condition-{i}','clinicalStatus':{'text':'history'},'code':{'text':str(c)},'subject':_ref('Patient',pid)}})
    if report.get('medications'):
        resources.append({'resource':{'resourceType':'MedicationStatement','id':'medication-1','status':'active','medicationCodeableConcept':{'text':str(report['medications'])},'subject':_ref('Patient',pid)}})
    resources.append({'resource':{'resourceType':'CarePlan','id':f'careplan-{uuid.uuid4().hex[:10]}','status':'active','intent':'plan','title':'AarogyaMitra decision-support care plan','subject':_ref('Patient',pid),'description':f"Risk level: {risk.get('level','Unknown')}; score: {risk.get('score',0)}"}})
    resources.append({'resource':{'resourceType':'Encounter','id':f'encounter-{uuid.uuid4().hex[:10]}','status':'finished','class':{'code':'AI-SD','display':'AI decision-support encounter'},'subject':_ref('Patient',pid)}})
    return {'resourceType':'Bundle','type':'collection','timestamp':datetime.utcnow().isoformat(timespec='seconds'),'entry':resources,'meta':{'tag':[{'system':'https://aarogyamitra.local/fhir','code':'decision-support','display':'Prototype interoperability export; not a clinical record of authority.'}]}}
