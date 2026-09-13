"""Clinical safety governance and recommendation provenance helpers."""
from datetime import datetime
import secrets
from .db import db_session, SafetyRule, RecommendationRecord

RULE_VERSION = 'clinical-safety-1.0'

DEFAULT_RULES = [
    {'id':'emergency-red-flags','name':'Emergency red-flag escalation','description':'Serious symptoms require urgent care guidance and should not be delayed by additional questioning.','evidence_source':'WHO / local emergency guidance','evidence_url':'https://www.who.int/','status':'draft','review_date':'','reviewer':'','applicable_population':['all'],'contraindications':[],'human_review_required':True},
    {'id':'pediatric-caution','name':'Pediatric caution','description':'Children require age-appropriate interpretation and lower tolerance for uncertain advice.','evidence_source':'WHO child health guidance','evidence_url':'https://www.who.int/health-topics/child-health','status':'draft','review_date':'','reviewer':'','applicable_population':['children'],'contraindications':[],'human_review_required':True},
    {'id':'pregnancy-caution','name':'Pregnancy and breastfeeding caution','description':'Pregnancy/breastfeeding should trigger conservative guidance and medication caution.','evidence_source':'WHO maternal health guidance','evidence_url':'https://www.who.int/health-topics/maternal-health','status':'draft','review_date':'','reviewer':'','applicable_population':['pregnancy','breastfeeding'],'contraindications':[],'human_review_required':True},
    {'id':'older-adult-caution','name':'Older adult caution','description':'Older adults may need additional context and lower thresholds for professional review.','evidence_source':'WHO healthy ageing guidance','evidence_url':'https://www.who.int/health-topics/ageing','status':'draft','review_date':'','reviewer':'','applicable_population':['older_adults'],'contraindications':[],'human_review_required':True},
]

def seed_rules():
    s=db_session()
    try:
        for item in DEFAULT_RULES:
            if not s.query(SafetyRule).filter_by(id=item['id']).first():
                s.add(SafetyRule(id=item['id'], name=item['name'], description=item['description'], version=RULE_VERSION, status=item['status'], evidence_source=item['evidence_source'], evidence_url=item['evidence_url'], review_date=item['review_date'], reviewer=item['reviewer'], applicable_population=item['applicable_population'], contraindications=item['contraindications'], human_review_required=item['human_review_required']))
        s.commit()
    finally:s.close()

def list_rules():
    s=db_session()
    try:
        rows=s.query(SafetyRule).order_by(SafetyRule.name.asc()).all()
        return [rule_dict(x) for x in rows]
    finally:s.close()

def rule_dict(x):
    return {'id':x.id,'name':x.name,'description':x.description,'version':x.version,'status':x.status,'evidence_source':x.evidence_source,'evidence_url':x.evidence_url,'review_date':x.review_date,'reviewer':x.reviewer,'applicable_population':x.applicable_population or [],'contraindications':x.contraindications or [],'human_review_required':x.human_review_required}

def update_rule(rule_id, payload):
    s=db_session()
    try:
        row=s.query(SafetyRule).filter_by(id=rule_id).first()
        if not row: return None
        for key in ['name','description','version','status','evidence_source','evidence_url','review_date','reviewer','human_review_required']:
            if key in payload: setattr(row,key,payload[key])
        if 'applicable_population' in payload: row.applicable_population=payload['applicable_population'] or []
        if 'contraindications' in payload: row.contraindications=payload['contraindications'] or []
        row.updated_at=datetime.utcnow();s.commit();return rule_dict(row)
    finally:s.close()

def applicable_population(payload):
    age=payload.get('age'); pop=['all']
    try: age=int(age) if age not in (None,'') else None
    except: age=None
    if age is not None:
        if age < 18: pop.append('children')
        if age >= 65: pop.append('older_adults')
    pregnancy=str(payload.get('pregnancy') or '').lower()
    if 'pregnant' in pregnancy: pop.append('pregnancy')
    if 'breastfeeding' in pregnancy: pop.append('breastfeeding')
    return pop

def record_recommendation(user_id, text, *, evidence=None, confidence='medium', contraindications=None, human_review_required=True, payload=None):
    evidence=evidence or {}
    s=db_session()
    try:
        row=RecommendationRecord(id='rec:'+secrets.token_hex(10),user_id=user_id,text=text,evidence_source=evidence.get('source',''),evidence_url=evidence.get('url',''),rule_version=RULE_VERSION,model_version='groq-current',confidence=confidence,applicable_population=applicable_population(payload or {}),contraindications=contraindications or [],human_review_required=human_review_required,created_at=datetime.utcnow())
        s.add(row);s.commit();return {'id':row.id,'text':row.text,'evidence_source':row.evidence_source,'evidence_url':row.evidence_url,'rule_version':row.rule_version,'model_version':row.model_version,'confidence':row.confidence,'applicable_population':row.applicable_population or [],'contraindications':row.contraindications or [],'human_review_required':row.human_review_required}
    finally:s.close()
