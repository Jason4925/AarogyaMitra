from collections import defaultdict
from datetime import datetime
from typing import Optional
import os, uuid, json
from fastapi import FastAPI, Form, Header, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field
from twilio.twiml.messaging_response import MessagingResponse
import uvicorn

from .db import init_db, db_session, User, Report, EmergencyEvent, DashboardSignal, Conversation, AIEvent, Handoff, AuditLog, AIEvaluation, database_health, LoginSession, LoginAttempt, RevokedToken, KnowledgeSource, KnowledgeReview, RecommendationRecord, CarePathwayDecision
from .auth import authenticate, create_user, get_user_by_token, public_user, revoke_token, seed_admin
from .ai_agent import graph, SYSTEM_PROMPT
from .assessment import generate_report
from .awareness import get_daily_awareness, get_public_health
from .health_state import update_health_state, get_health_state, reset_health_state
from .memory import save_message, get_history, reset_user_memory, get_memory_enabled, set_memory_enabled
from .vaccination import calculate_schedule, next_milestone
from .risk_engine import calculate_risk, follow_up_questions
from .timeline import add_event, get_timeline
from .followup import schedule_followup, get_followup, complete_followup
from .handoff import create_handoff, latest_handoff
from .tools import call_emergency_family, search_nearby_healthcare_structured
from .storage_service import upload_report_document
from .db_metrics import ai_analytics, log_ai_event, dashboard_signal
from .readiness import seed_readiness, readiness_snapshot
from .audit import log_audit
from .ai_safety import validate_response
from .knowledge_base import build_context
from .knowledge_governance import seed_sources, list_sources, update_source, review_source
from .consent import get_consents, set_consents
from .population import population_analytics, outbreak_signals, evaluation_scenarios
from .care_plan import build_care_plan
from .redteam import SCENARIOS as REDTEAM_SCENARIOS, run_case as run_redteam_case
from .fhir import patient_bundle
from .security_center import security_summary
from .care_pathways import build_care_pathway
from .ai_benchmark import benchmark_summary
from .clinical_safety import seed_rules, list_rules, update_rule, record_recommendation, RULE_VERSION
from .clinical_safety_lab import evaluate_rule_case, governance_metrics
from .health_record_plus import add_measurement, list_measurements, add_document, list_documents, confirm_document, create_share, verify_share, revoke_share, list_shares, set_caregiver, get_caregiver, acknowledge_emergency, add_feedback
from .medication_safety import check_medications
from .config import *

app=FastAPI(title='AarogyaMitra API',version='3.0')
app.add_middleware(CORSMiddleware,allow_origins=FRONTEND_ORIGINS,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
rate_hits=defaultdict(list)

@app.on_event('startup')
def startup():
    init_db()
    try: seed_sources()
    except Exception as e: print('KNOWLEDGE SEED WARNING:',repr(e))
    try: seed_admin()
    except Exception as e: print('ADMIN SEED WARNING:',repr(e))
    try: seed_readiness()
    except Exception as e: print('READINESS SEED WARNING:',repr(e))
    try: seed_rules()
    except Exception as e: print('SAFETY RULE SEED WARNING:',repr(e))

@app.middleware('http')
async def security_middleware(request:Request,call_next):
    if request.method!='OPTIONS':
        cl=request.headers.get('content-length')
        if cl and cl.isdigit() and int(cl)>MAX_REQUEST_BYTES:return JSONResponse({'detail':'Request too large.'},status_code=413)
        client=request.client.host if request.client else 'unknown';now=datetime.now().timestamp();rate_hits[client]=[t for t in rate_hits[client] if now-t<RATE_LIMIT_WINDOW]
        if len(rate_hits[client])>=RATE_LIMIT_MAX and request.url.path not in {'/health','/docs','/openapi.json'}:return JSONResponse({'detail':'Too many requests. Please try again shortly.'},status_code=429)
        rate_hits[client].append(now)
    response=await call_next(request);response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='DENY';response.headers['Referrer-Policy']='no-referrer';response.headers['Cache-Control']='no-store';return response

class Query(BaseModel): message:str=Field(min_length=1,max_length=4000);user_id:str=Field(min_length=1,max_length=200)
class SignupPayload(BaseModel): name:str=Field(min_length=1,max_length=100);email:str=Field(min_length=3,max_length=200);phone:str=Field(default='',max_length=30);password:str=Field(min_length=8,max_length=128)
class LoginPayload(BaseModel): email:str=Field(min_length=3,max_length=200);password:str=Field(min_length=1,max_length=128)
class EmergencyPayload(BaseModel): reason:str=Field(min_length=1,max_length=1000)
class FollowupPayload(BaseModel): comparison:str=Field(min_length=1,max_length=30);severity:int=Field(ge=1,le=10);notes:str=Field(default='',max_length=1000)
class MemoryPayload(BaseModel): enabled:bool
class DeletePayload(BaseModel): confirmation:str


def current_user(auth:Optional[str]):
    if not auth or not auth.startswith('Bearer '):raise HTTPException(401,'Login required.')
    user=get_user_by_token(auth.split(' ',1)[1].strip())
    if not user:raise HTTPException(401,'Session expired. Please login again.')
    return user

def _user_field(user, name, default=''):
    if isinstance(user, dict):
        return user.get(name, default)
    return getattr(user, name, default)

def current_admin(auth):
    u=current_user(auth)
    if _user_field(u, 'role', '')!='admin':
        raise HTTPException(403,'Admin access required.')
    return u

def is_medical_emergency(text):
    lower=text.lower();return any(p in lower for p in ['severe bleeding','heavy bleeding','uncontrolled bleeding','difficulty breathing',"can't breathe",'cannot breathe','severe chest pain','unconscious','not responding','stroke symptoms','signs of stroke','seizure','severe injury','loss of consciousness'])

def limit_response(text,max_chars=900):
    text=str(text or '').strip()
    if len(text)<=max_chars:return text
    short=text[:max_chars];end=max(short.rfind('.'),short.rfind('!'),short.rfind('?'));return short[:end+1] if end>300 else short.rsplit(' ',1)[0]+'...'

def add_emergency(user,text,channel,result):
    s=db_session()
    try:
        row=EmergencyEvent(user_id=user.user_id,user_name=user.name,channel=channel,reason=text,contact=user.emergency_contact or 'default',call_success=bool(result.get('success')),call_sid=result.get('sid',''),call_status=result.get('status',''),timestamp=datetime.utcnow())
        s.add(row);s.add(DashboardSignal(signal_type='emergency'));s.commit();s.refresh(row);return row.id
    finally:s.close()

def latest_report_data(uid):
    s=db_session()
    try:
        r=s.query(Report).filter_by(user_id=uid).order_by(Report.created_at.desc()).first();return r.payload if r else {}
    finally:s.close()

def json_safe_user(user):return public_user(user)

@app.get('/health')
async def health():
    try: db=database_health();return {'status':'ok','service':'AarogyaMitra','database':db}
    except Exception as e:return JSONResponse({'status':'degraded','service':'AarogyaMitra','database':{'connected':False,'error':str(e)}},status_code=503)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "AarogyaMitra API",
        "message": "Backend is running successfully"
    }

@app.get('/public-health')
async def public_health(language:str='English'):
    return get_public_health(language)
@app.get('/languages')
async def languages():
    return {'default':'English','languages':['English','Hindi','Marathi','Tamil','Telugu','Bengali','Gujarati','Kannada','Malayalam','Punjabi','Odia','Urdu']}

@app.get('/awareness')
async def awareness():return {'items':get_daily_awareness(6)}
@app.get('/health-state')
async def health_state(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    return get_health_state(u.user_id)

@app.get('/dashboard/summary')
async def dashboard_summary(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    report=latest_report_data(u.user_id)
    return {'latest_report': report or None, 'risk': (report or {}).get('risk_engine') or (report or {}).get('risk') or {}, 'health_state': get_health_state(u.user_id)}


@app.get('/vaccination/schedule')
async def vacc(dob:str,authorization:Optional[str]=Header(default=None)):
    current_user(authorization)
    try:birth=datetime.strptime(dob,'%Y-%m-%d').date()
    except ValueError:raise HTTPException(400,'DOB must be YYYY-MM-DD.')
    return {'dob':dob,'schedule':calculate_schedule(birth),'next':next_milestone(birth)}

@app.post('/signup')
async def signup(p:SignupPayload):
    try:
        u=create_user(p.name,p.email,p.phone,p.password);a=authenticate(p.email,p.password);log_audit(u['user_id'],'signup','user',u['user_id']);return {**public_user(a['user']),'token':a['token']}
    except ValueError as e:raise HTTPException(400,str(e))

@app.post('/login')
async def login(p:LoginPayload):
    a=authenticate(p.email,p.password)
    if not a:raise HTTPException(401,'Invalid email or password.')
    log_audit(_user_field(a.get('user'),'user_id'),'login','user',_user_field(a.get('user'),'user_id'))
    return {**public_user(a['user']),'token':a['token']}

@app.post('/admin/login')
async def admin_login(p:LoginPayload):
    a=authenticate(p.email,p.password)
    if not a or _user_field(a.get('user'),'role','')!='admin':raise HTTPException(401,'Invalid admin credentials.')
    log_audit(_user_field(a.get('user'),'user_id'),'admin_login','admin',_user_field(a.get('user'),'user_id'));return {**public_user(a['user']),'token':a['token']}

@app.post('/logout')
async def logout(authorization:Optional[str]=Header(default=None)):
    if authorization and authorization.startswith('Bearer '):revoke_token(authorization.split(' ',1)[1].strip())
    return {'success':True}

@app.post('/ask')
async def ask(q:Query,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if q.user_id!=u.user_id:raise HTTPException(403,'Invalid user session.')
    text=q.message.strip()
    update_health_state(u.user_id,text)
    save_message(u.user_id,'user',text)
    log_ai_event('conversation',u.user_id)
    if is_medical_emergency(text):
        r=call_emergency_family(text,contact=u.emergency_contact or None)
        emergency_id=add_emergency(u,text,'website',r)
        log_ai_event('emergency_detected',u.user_id)
        log_audit(u.user_id,'emergency_escalation','conversation',u.user_id,metadata={'success':bool(r.get('success'))})
        resp='⚠️ This may be a medical emergency. '+('Your registered family/caregiver has been alerted. ' if r.get('success') else 'I could not reach your registered family/caregiver. ')+'Please seek immediate medical help.'
        save_message(u.user_id,'assistant',resp)
        return {'response':resp,'tool_called':'emergency_family_call','sources':[],'safety':{'passed':True,'confidence':'high'},'do_not_delay':True,'emergency_event_id':emergency_id,'emergency_action':'Seek emergency care now and acknowledge the warning after acting.'}
    history=get_history(u.user_id,12) if get_memory_enabled(u.user_id) else []
    state=get_health_state(u.user_id)
    lang=u.preferred_language or 'English'
    source_ctx,sources=build_context(text,3)
    ctx=(f"\nCURRENT HEALTH STATE: Symptoms {', '.join(state.get('symptoms',[])) or 'unknown'}; Duration {state.get('duration') or 'unknown'}; Severity {state.get('severity') or 'unknown'}; Red flags {', '.join(state.get('red_flags',[])) or 'none'}."
         f"\nUSER LANGUAGE: Respond primarily in {lang}. Keep medical terms clear and define them briefly when needed.\n"+source_ctx)
    try:
        result=graph.invoke({'messages':[('system',SYSTEM_PROMPT+ctx)]+history+[('user',text)]})
        draft=limit_response(result['messages'][-1].content)
        checked=validate_response(draft)
        final=checked['text']
        if checked['issues']:
            log_ai_event('safety_validator_block',u.user_id,{'issues':checked['issues']})
        if checked['confidence']=='low':log_ai_event('low_confidence',u.user_id,{'issues':checked['issues']})
        if any(x in final.lower() for x in ['i cannot answer that','outside my scope','unsupported question','i do not have information on']):log_ai_event('unsupported_question',u.user_id)
        if any(x in text.lower() for x in ['wrong','incorrect','that is not right','you are mistaken']):log_ai_event('user_correction',u.user_id)
        save_message(u.user_id,'assistant',final);dashboard_signal('conversation')
        return {'response':final,'tool_called':'AI','sources':sources,'safety':checked}
    except Exception as e:
        print('ASK ERROR:',repr(e));log_ai_event('api_failure',u.user_id,{'error':str(e)[:250]});log_ai_event('fallback_response',u.user_id);save_message(u.user_id,'assistant','Sorry, I am having trouble processing your request right now.');return {'response':'Sorry, I am having trouble processing your request right now.','tool_called':'fallback','sources':sources,'safety':{'passed':False,'confidence':'low','issues':['api_failure']}}

@app.post('/assessment')
async def assessment(payload:dict,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    try:
        payload=dict(payload);payload['preferred_language']=u.preferred_language or 'English'
        report,risk=generate_report(payload); source_ctx,sources=build_context((payload.get('mainProblem') or '')+' '+' '.join(payload.get('symptoms') or []),3); report['sources']=sources; report_id='rp:'+uuid.uuid4().hex
        pathway=build_care_pathway(payload,risk); care_plan=build_care_plan(payload,risk,pathway)
        question_count=len(payload.get('follow_up_details') or {})
        timeline=add_event(u.user_id,'assessment',payload.get('mainProblem','Health assessment'),payload.get('severity'),risk.get('level',''),report.get('problem_summary',''),'assessment',{'risk_score':risk.get('score',0)})
        events=get_timeline(u.user_id,40);handoff=create_handoff(u,payload,risk,report,events,questions_asked=question_count);follow=schedule_followup(u.user_id,payload.get('severity'),risk.get('level'),payload.get('mainProblem',''))
        do_not_delay=bool(risk.get('level') in {'High','Critical'} or report.get('red_flags'));
        provenance=[]
        for text_item in [risk.get('recommended_action',''), report.get('next_steps','')]:
            if text_item: provenance.append(record_recommendation(u.user_id,text_item,evidence={'source':'AarogyaMitra governed safety rules'},confidence='medium',contraindications=[],human_review_required=do_not_delay,payload=payload))
        report_data={**payload,'id':report_id,'user_id':u.user_id,'user_name':u.name,'created_at':datetime.utcnow().isoformat(timespec='seconds'),'report':report,'red_flags':report.get('red_flags',[]),'risk':risk,'risk_engine':risk,'timeline_event':timeline,'followup':follow,'handoff_id':handoff['id'],'questions_answered':question_count,'care_pathway':pathway,'care_plan':care_plan,'do_not_delay':do_not_delay,'recommendation_provenance':provenance,'applicable_population':['all']}
        s=db_session()
        try:
            s.add(Report(id=report_id,user_id=u.user_id,payload=report_data,risk=risk,created_at=datetime.utcnow()))
            s.add(DashboardSignal(signal_type='assessment'))
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()
        log_ai_event('assessment_completed',u.user_id)
        log_audit(u.user_id,'assessment_completed','report',report_id,metadata={'risk_level':risk.get('level'),'risk_score':risk.get('score')})
        return report_data
    except Exception as e:
        print('ASSESSMENT ERROR:',repr(e));log_ai_event('api_failure',u.user_id,{'area':'assessment','error':str(e)[:250]});raise HTTPException(500,'Unable to generate the health report. Please try again.')

@app.post('/risk/calculate')
async def rc(payload:dict,authorization:Optional[str]=Header(default=None)):current_user(authorization);return calculate_risk(payload)
@app.post('/risk/questions')
async def rq(payload:dict,authorization:Optional[str]=Header(default=None)):current_user(authorization);return {'questions':follow_up_questions(payload)}

@app.get('/care-pathway')
async def care_pathway(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    report=latest_report_data(u.user_id) or {}
    risk=report.get('risk_engine') or report.get('risk') or calculate_risk(report)
    pathway=build_care_pathway(report, risk)
    pathway['care_plan']=build_care_plan(report, risk, pathway)
    s=db_session()
    try:
        s.add(CarePathwayDecision(id='cp:'+uuid.uuid4().hex,user_id=u.user_id,risk_level=risk.get('level',''),pathway=pathway.get('title',''),rule_version=RULE_VERSION,reasons=risk.get('factors') or [],human_review_required=risk.get('level') in {'High','Critical'}));s.commit()
    finally:s.close()
    return pathway

@app.get('/timeline')
async def timeline(authorization:Optional[str]=Header(default=None)):return {'events':get_timeline(current_user(authorization).user_id,50)}
@app.get('/followup')
async def pending(authorization:Optional[str]=Header(default=None)):return {'followup':get_followup(current_user(authorization).user_id)}
@app.post('/followup/check-in')
async def checkin(p:FollowupPayload,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);c=complete_followup(u.user_id,p.comparison,p.severity,p.notes)
    if not c:raise HTTPException(404,'No pending follow-up found.')
    previous=int(c.get('previous_severity') or p.severity);w=p.comparison.lower()=='worse' or p.severity>previous+1
    latest=latest_report_data(u.user_id);follow_payload=dict(latest or {});follow_payload['severity']=p.severity;follow_payload['follow_up_details']={**(follow_payload.get('follow_up_details') or {}),'follow_up_comparison':p.comparison}
    new_risk=calculate_risk(follow_payload);add_event(u.user_id,'follow-up','Follow-up check-in',p.severity,new_risk.get('level',''),f'Compared with previous severity {previous}/10: {p.comparison}.','followup',{'risk_score':new_risk.get('score')})
    next_fu=schedule_followup(u.user_id,p.severity,new_risk.get('level'),c.get('concern')) if not w else None
    return {'completed':c,'worsening':w,'risk':new_risk,'next_followup':next_fu,'message':'⚠️ Symptoms appear to be worsening. Please reassess and consider prompt professional evaluation.' if w else 'Thanks for checking in. Your updated health status has been recorded.'}

@app.get('/handoff/latest')
async def handoff_latest(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);h=latest_handoff(u.user_id)
    # Always repair from latest report if the saved handoff is missing or empty.
    rep=latest_report_data(u.user_id)
    if rep:
        report=rep.get('report') or {};risk=rep.get('risk_engine') or rep.get('risk') or calculate_risk(rep)
        if not h or not h.get('chief_concern') or h.get('chief_concern')!=rep.get('mainProblem'):
            h=create_handoff(u,rep,risk,report,get_timeline(u.user_id,40),len(rep.get('follow_up_details') or {}))
    return h or {}

@app.get('/latest-report')
async def latest(authorization:Optional[str]=Header(default=None)):return latest_report_data(current_user(authorization).user_id)

@app.get('/patient-record')
async def patient_record(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);s=db_session()
    try:
        reports=s.query(Report).filter_by(user_id=u.user_id).order_by(Report.created_at.desc()).limit(20).all()
        report_rows=[{'id':r.id,'created_at':r.created_at.isoformat(timespec='seconds'),'mainProblem':(r.payload or {}).get('mainProblem',''),'severity':(r.payload or {}).get('severity',''),'risk':(r.risk or {}).get('level',''),'risk_score':(r.risk or {}).get('score',0)} for r in reports]
    finally:s.close()
    return {'user':public_user(u),'health_state':get_health_state(u.user_id),'timeline':get_timeline(u.user_id,100),'followup':get_followup(u.user_id),'reports':report_rows,'latest_report':latest_report_data(u.user_id),'handoff':latest_handoff(u.user_id)}


@app.get('/health-record/measurements')
async def health_measurements(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); return {'measurements':list_measurements(u.user_id)}

@app.post('/health-record/measurements')
async def health_measurement_add(payload:dict,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    try:
        measured_at = datetime.fromisoformat(str(payload.get('measured_at'))) if payload.get('measured_at') else None
        row=add_measurement(u.user_id, str(payload.get('metric','')), str(payload.get('value','')), str(payload.get('unit','')), measured_at, str(payload.get('note','')), str(payload.get('source','user')), False, {'source':'user'})
        log_audit(u.user_id,'measurement_created','health_record',row['id'],metadata={'metric':row['metric']})
        return row
    except ValueError as e: raise HTTPException(400,str(e))

@app.get('/health-record/documents')
async def health_documents(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); return {'documents':list_documents(u.user_id)}

@app.post('/health-record/documents')
async def health_document_upload(file:UploadFile=File(...),authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); content=await file.read()
    if len(content)>MAX_REQUEST_BYTES: raise HTTPException(413,'Document too large.')
    extracted={}
    if (file.content_type or '').startswith('text/'):
        try: extracted={'text_preview':content.decode('utf-8','ignore')[:5000], 'requires_confirmation':True}
        except Exception: extracted={'requires_confirmation':True}
    try:
        path=upload_report_document(u.user_id,'health-doc',file.filename or 'health-document',content,file.content_type or 'application/octet-stream')
    except Exception:
        path=''
    return add_document(u.user_id,file.filename or 'health-document',file.content_type or '',path,extracted)

@app.post('/health-record/documents/{doc_id}/confirm')
async def health_document_confirm(doc_id:str,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); row=confirm_document(u.user_id,doc_id)
    if not row: raise HTTPException(404,'Document not found.')
    log_audit(u.user_id,'health_document_confirmed','health_document',doc_id); return row

@app.get('/handoff/shares')
async def handoff_shares(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); return {'shares':list_shares(u.user_id)}

@app.post('/handoff/shares')
async def handoff_share_create(payload:dict,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); h=latest_handoff(u.user_id)
    if not h: raise HTTPException(404,'No Doctor Handoff is available to share.')
    result=create_share(u.user_id,h['id'],int(payload.get('expiry_hours',24)),payload.get('included'))
    log_audit(u.user_id,'handoff_share_created','handoff_share',result['id'])
    return result

@app.post('/handoff/shares/revoke/{share_id}')
async def handoff_share_revoke(share_id:str,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if not revoke_share(u.user_id,share_id): raise HTTPException(404,'Share not found.')
    log_audit(u.user_id,'handoff_share_revoked','handoff_share',share_id); return {'success':True}

@app.post('/public/handoff/access')
async def public_handoff_access(payload:dict):
    token=str(payload.get('token','')).strip(); code=str(payload.get('access_code','')).strip()
    if not token or not code: raise HTTPException(400,'Access token and code are required.')
    result=verify_share(token,code)
    if not result: raise HTTPException(403,'Invalid, expired, or revoked share.')
    return result

@app.get('/caregiver')
async def caregiver_get(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); return {'caregiver':get_caregiver(u.user_id)}

@app.put('/caregiver')
async def caregiver_put(payload:dict,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    row=set_caregiver(u.user_id,str(payload.get('name','')),str(payload.get('contact','')),payload.get('permissions') or ['emergency'])
    log_audit(u.user_id,'caregiver_updated','caregiver',row['id']); return row

@app.post('/feedback')
async def feedback(payload:dict,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); category=str(payload.get('category','other')); description=str(payload.get('description','')).strip()
    if not description: raise HTTPException(400,'Description is required.')
    row=add_feedback(u.user_id,category,description,str(payload.get('severity','normal'))); log_audit(u.user_id,'feedback_submitted','feedback',row['id']); return row

@app.post('/medication/check')
async def medication_check(payload:dict,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); result=check_medications(payload.get('medications'),payload.get('allergies',''),payload.get('age',''),payload.get('weight',''),payload.get('pregnancy',''))
    log_audit(u.user_id,'medication_safety_checked','medication_check',u.user_id); return result

@app.post('/emergency/acknowledge/{event_id}')
async def emergency_ack(event_id:int,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); result=acknowledge_emergency(u.user_id,event_id); log_audit(u.user_id,'emergency_warning_acknowledged','emergency',str(event_id)); return result

@app.get('/clinical-safety/rules')
async def clinical_rules_public(authorization:Optional[str]=Header(default=None)):
    current_user(authorization); return {'rules':[x for x in list_rules() if x['status']=='active' or x['status']=='clinically_reviewed'], 'version':RULE_VERSION}

@app.post('/admin/clinical-safety/label')
async def admin_clinical_label(payload:dict,authorization:Optional[str]=Header(default=None)):
    admin=current_admin(authorization)
    from .db import ClinicalLabel
    case_id=str(payload.get('case_id','')).strip();expected=str(payload.get('expected_urgency','')).strip()
    if not case_id or not expected: raise HTTPException(400,'case_id and expected_urgency are required.')
    s=db_session()
    try:
        row=ClinicalLabel(id='label:'+uuid.uuid4().hex,case_id=case_id,reviewer=str(payload.get('reviewer') or admin.name),reviewed_status='reviewed',expected_urgency=expected,notes=str(payload.get('notes','')),rule_version=RULE_VERSION,created_at=datetime.utcnow());s.add(row);s.commit();return {'id':row.id,'case_id':row.case_id,'reviewer':row.reviewer,'expected_urgency':row.expected_urgency,'notes':row.notes,'rule_version':row.rule_version}
    finally:s.close()

@app.get('/admin/clinical-safety/labels')
async def admin_clinical_labels(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); from .db import ClinicalLabel; s=db_session()
    try:
        rows=s.query(ClinicalLabel).order_by(ClinicalLabel.created_at.desc()).limit(100).all(); return {'labels':[{'id':x.id,'case_id':x.case_id,'reviewer':x.reviewer,'status':x.reviewed_status,'expected_urgency':x.expected_urgency,'notes':x.notes,'rule_version':x.rule_version,'created_at':x.created_at.isoformat(timespec='seconds')} for x in rows]}
    finally:s.close()

@app.get('/admin/feedback')
async def admin_feedback(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); from .db import FeedbackTicket; s=db_session()
    try:
        rows=s.query(FeedbackTicket).order_by(FeedbackTicket.created_at.desc()).limit(200).all(); return {'feedback':[{'id':x.id,'user_id':x.user_id,'category':x.category,'severity':x.severity,'description':x.description,'status':x.status,'created_at':x.created_at.isoformat(timespec='seconds')} for x in rows]}
    finally:s.close()

@app.get('/admin/recommendations/provenance')
async def admin_recommendation_provenance(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); s=db_session()
    try:
        rows=s.query(RecommendationRecord).order_by(RecommendationRecord.created_at.desc()).limit(200).all(); return {'records':[{'id':x.id,'user_id':x.user_id,'text':x.text,'evidence_source':x.evidence_source,'evidence_url':x.evidence_url,'rule_version':x.rule_version,'model_version':x.model_version,'confidence':x.confidence,'applicable_population':x.applicable_population or [],'contraindications':x.contraindications or [],'human_review_required':x.human_review_required,'created_at':x.created_at.isoformat(timespec='seconds')} for x in rows]}
    finally:s.close()

@app.get('/admin/clinical-safety')
async def admin_clinical_safety(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); return {'metrics':governance_metrics(),'rules':list_rules()}

@app.put('/admin/clinical-safety/rules/{rule_id}')
async def admin_clinical_rule_update(rule_id:str,payload:dict,authorization:Optional[str]=Header(default=None)):
    admin=current_admin(authorization)
    if str(payload.get('status','')).lower()=='active' and (not payload.get('reviewer') or not payload.get('evidence_source')):
        raise HTTPException(400,'An active rule requires a named reviewer and evidence source. Use draft until clinically reviewed.')
    row=update_rule(rule_id,payload)
    if not row: raise HTTPException(404,'Safety rule not found.')
    log_audit(admin.user_id,'clinical_safety_rule_updated','safety_rule',rule_id,metadata={'status':row['status'],'version':row['version']}); return row

@app.post('/admin/clinical-safety/evaluate')
async def admin_clinical_evaluate(payload:dict,authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); return evaluate_rule_case(payload)

@app.get('/admin/clinical-safety/recommendations')
async def admin_recommendation_records(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); s=db_session()
    try:
        rows=s.query(RecommendationRecord).order_by(RecommendationRecord.created_at.desc()).limit(100).all()
        return {'recommendations':[{'id':x.id,'text':x.text,'evidence_source':x.evidence_source,'evidence_url':x.evidence_url,'rule_version':x.rule_version,'model_version':x.model_version,'confidence':x.confidence,'applicable_population':x.applicable_population or [],'contraindications':x.contraindications or [],'human_review_required':x.human_review_required,'created_at':x.created_at.isoformat(timespec='seconds')} for x in rows]}
    finally:s.close()

@app.get('/admin/ai-evaluation-metrics')
async def admin_ai_eval_metrics(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); s=db_session()
    try:
        rows=s.query(AIEvaluation).all(); total=len(rows); passed=sum(1 for r in rows if r.passed)
        return {'total':total,'passed':passed,'pass_rate_pct':round(passed/max(1,total)*100,1),'uncertain_handling':sum(1 for r in rows if 'uncertain' in (r.scenario_id or '')),'emergency_cases':sum(1 for r in rows if 'emergency' in (r.scenario_id or '')),'medication_cases':sum(1 for r in rows if 'medication' in (r.scenario_id or ''))}
    finally:s.close()

@app.get('/healthcare/search')
async def healthcare(location:str,service:str='doctor',risk_level:str='Low',authorization:Optional[str]=Header(default=None)):
    current_user(authorization);return {'location':location,'service':service,'risk_level':risk_level,'facilities':search_nearby_healthcare_structured(location,service,limit=3,risk_level=risk_level)}

@app.get('/history/{user_id}')
async def history(user_id:str,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if u.user_id!=user_id and u.role!='admin':raise HTTPException(403,'Access denied.')
    if u.user_id==user_id and not get_memory_enabled(user_id):return {'user_id':user_id,'history':[],'memory_enabled':False}
    return {'user_id':user_id,'history':[{'role':r,'message':m} for r,m in get_history(user_id,50)],'memory_enabled':get_memory_enabled(user_id)}

@app.delete('/history/{user_id}')
async def delhistory(user_id:str,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if u.user_id!=user_id:raise HTTPException(403,'Access denied.')
    reset_user_memory(user_id);log_audit(u.user_id,'conversation_history_cleared','conversation',user_id);return {'success':True}

@app.get('/memory/preferences')
async def memory_get(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);return {'enabled':get_memory_enabled(u.user_id)}
@app.put('/memory/preferences')
async def memory_put(p:MemoryPayload,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);set_memory_enabled(u.user_id,p.enabled);log_audit(u.user_id,'memory_preference_changed','privacy',u.user_id,metadata={'enabled':p.enabled});return {'enabled':p.enabled}

@app.get('/profile')
async def profile(authorization:Optional[str]=Header(default=None)):return public_user(current_user(authorization))
@app.put('/profile')
async def profile_put(payload:dict,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);s=db_session()
    try:
        target=s.query(User).filter_by(user_id=u.user_id).first()
        if not target:
            raise HTTPException(404,'User profile not found.')
        allowed=['name','phone','location','preferred_language','emergency_contact','age','gender','conditions','allergies']
        for k in allowed:
            if k not in payload:
                continue
            value=payload[k]
            # The production users.age column is NOT NULL.  Treat an empty
            # optional age as an empty string rather than SQL NULL.
            if k=='age':
                # Never allow a NULL age to reach the DB. Empty means unknown/not provided.
                if value is None or (isinstance(value, str) and not value.strip()):
                    value=''
                else:
                    try:
                        n=int(value)
                    except (TypeError,ValueError):
                        raise HTTPException(400,'Age must be a whole number or left blank.')
                    if n < 1 or n > 120:
                        raise HTTPException(400,'Age must be between 1 and 120.')
                    value=str(n)
            if k=='conditions':
                value=value if isinstance(value,list) else []
            setattr(target,k,value)
        # Repair legacy rows whose NOT NULL age field somehow contains NULL.
        if target.age is None:
            target.age=''
        if target.phone is None: target.phone=''
        if target.location is None: target.location=''
        if target.preferred_language is None: target.preferred_language='English'
        if target.emergency_contact is None: target.emergency_contact=''
        if target.gender is None: target.gender=''
        if target.allergies is None: target.allergies=''
        if target.conditions is None: target.conditions=[]
        s.commit();s.refresh(target)
        out=public_user(target)
    except HTTPException:
        s.rollback()
        raise
    except Exception as e:
        s.rollback()
        print('PROFILE UPDATE ERROR:', repr(e))
        raise HTTPException(500, 'Unable to save your profile. Please try again.')
    finally:
        s.close()
    log_audit(u.user_id,'profile_updated','user',u.user_id)
    return out

@app.get('/consents')
async def consents_get(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);return {'consents':get_consents(u.user_id)}

@app.put('/consents')
async def consents_put(payload:dict,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); values={k:bool(v) for k,v in payload.items() if isinstance(v,(bool,int))}; out=set_consents(u.user_id,values);log_audit(u.user_id,'consent_updated','privacy',u.user_id,metadata={'changes':values});return {'consents':out}

@app.get('/privacy/security-summary')
async def privacy_security_summary(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    uid=_user_field(u, 'user_id', '')
    role=_user_field(u, 'role', 'user')
    return {
        'account': {'authenticated': True, 'role': role},
        'memory_enabled': get_memory_enabled(uid),
        'stored_areas': ['profile','conversations','health state','reports','timeline','follow-ups','doctor handoffs','consents'],
        'controls': ['memory preference','clear conversation history','consent preferences','export my data','delete my account'],
        'sharing': get_consents(uid),
        'note': 'Security and privacy controls shown here describe application controls; they are not a substitute for an independent security audit.'
    }

@app.get('/privacy/export')
async def privacy_export(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    record={'user':public_user(u),'consents':get_consents(u.user_id),'health_state':get_health_state(u.user_id),'timeline':get_timeline(u.user_id,100),'followup':get_followup(u.user_id),'latest_report':latest_report_data(u.user_id),'handoff':latest_handoff(u.user_id),'conversation_history':[{'role':r,'message':m} for r,m in get_history(u.user_id,200)] if get_memory_enabled(u.user_id) else []}
    log_audit(u.user_id,'data_exported','privacy',u.user_id);return record

@app.delete('/privacy/account')
async def privacy_delete(p:DeletePayload,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    if p.confirmation!='DELETE':raise HTTPException(400,'Type DELETE to confirm account deletion.')
    uid=u.user_id; token=authorization.split(' ',1)[1].strip(); s=db_session()
    try:
        # Delete user-owned health/application data. Audit records are retained but anonymized.
        report_paths=[x.document_path for x in s.query(Report).filter_by(user_id=uid).all() if x.document_path]
        s.query(Conversation).filter_by(user_id=uid).delete(synchronize_session=False)
        s.query(Report).filter_by(user_id=uid).delete(synchronize_session=False)
        s.query(Handoff).filter_by(user_id=uid).delete(synchronize_session=False)
        from .db import HealthState, TimelineEvent, Followup, Consent
        s.query(HealthState).filter_by(user_id=uid).delete(synchronize_session=False)
        s.query(TimelineEvent).filter_by(user_id=uid).delete(synchronize_session=False)
        s.query(Followup).filter_by(user_id=uid).delete(synchronize_session=False)
        s.query(Consent).filter_by(user_id=uid).delete(synchronize_session=False)
        s.query(AIEvent).filter_by(user_id=uid).delete(synchronize_session=False)
        s.query(EmergencyEvent).filter_by(user_id=uid).delete(synchronize_session=False)
        s.query(AuditLog).filter_by(actor_user_id=uid).update({'actor_user_id':None,'resource_id':'deleted-user','metadata_json':{'anonymized':True}},synchronize_session=False)
        s.query(User).filter_by(user_id=uid).delete(synchronize_session=False)
        s.commit()
    finally:s.close()
    try:
        from .storage_service import delete_user_documents
        delete_user_documents(uid, report_paths)
    except Exception as e:
        print('STORAGE DELETE WARNING:', repr(e))
    revoke_token(token);return {'success':True,'message':'Account and user-owned health data deleted.'}

@app.post('/emergency/call')
async def emcall(p:EmergencyPayload,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);r=call_emergency_family(p.reason,contact=u.emergency_contact or None);event_id=add_emergency(u,p.reason,'website_report',r);log_ai_event('human_escalation',u.user_id);return {'success':r.get('success'),'message':'Emergency contact alerted.' if r.get('success') else 'Emergency call failed.','call_sid':r.get('sid'),'event_id':event_id}

@app.post('/whatsapp_ask')
async def wa(Body:str=Form('')):
    text=Body.strip()
    if is_medical_emergency(text):
        r=call_emergency_family(text);return Response(content=str(MessagingResponse().message('⚠️ This may be a medical emergency. Please seek immediate medical help.')),media_type='application/xml')
    try:
        source_ctx,_=build_context(text,2)
        result=graph.invoke({'messages':[('system',SYSTEM_PROMPT+'\n'+source_ctx),('user',text)]})
        checked=validate_response(limit_response(result['messages'][-1].content,800))
        return Response(content=str(MessagingResponse().message(checked['text'])),media_type='application/xml')
    except:
        return Response(content=str(MessagingResponse().message('Sorry, I am unable to process your message right now.')),media_type='application/xml')

@app.get('/care-plan')
async def care_plan_endpoint(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    report=latest_report_data(u.user_id) or {}
    risk=report.get('risk_engine') or report.get('risk') or calculate_risk(report)
    pathway=build_care_pathway(report,risk)
    return build_care_plan(report,risk,pathway)

@app.get('/fhir/bundle')
async def fhir_bundle(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization)
    record={'latest_report':latest_report_data(u.user_id),'risk':get_health_state(u.user_id),'health_state':get_health_state(u.user_id)}
    log_audit(u.user_id,'fhir_bundle_exported','interoperability',u.user_id)
    return patient_bundle(public_user(u),record)

@app.get('/security/summary')
async def security_summary_endpoint(authorization:Optional[str]=Header(default=None)):
    return security_summary(current_user(authorization))

@app.get('/security/sessions')
async def security_sessions(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization); s=db_session()
    try:
        rows=s.query(LoginSession).filter_by(user_id=u.user_id,revoked=False).order_by(LoginSession.created_at.desc()).limit(10).all()
        now=datetime.utcnow()
        return {'sessions':[{'id':x.id,'created_at':x.created_at.isoformat(timespec='seconds'),'expires_at':x.expires_at.isoformat(timespec='seconds'),'active':x.expires_at>now} for x in rows if x.expires_at>now]}
    finally:s.close()

@app.delete('/security/sessions/{session_id}')
async def revoke_session(session_id:str,authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);s=db_session()
    try:
        row=s.query(LoginSession).filter_by(id=session_id,user_id=u.user_id).first()
        if not row: raise HTTPException(404,'Session not found.')
        row.revoked=True; s.add(RevokedToken(jti=row.jti,expires_at=row.expires_at)); s.commit()
        log_audit(u.user_id,'session_revoked','security',session_id)
        return {'success':True}
    finally:s.close()

@app.get('/security/login-history')
async def security_login_history(authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);s=db_session()
    try:
        rows=s.query(LoginAttempt).filter_by(email=u.email).order_by(LoginAttempt.created_at.desc()).limit(20).all()
        return {'attempts':[{'success':x.success,'created_at':x.created_at.isoformat(timespec='seconds'),'ip_address':x.ip_address} for x in rows]}
    finally:s.close()

@app.get('/admin/redteam/scenarios')
async def redteam_scenarios(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); return {'scenarios':REDTEAM_SCENARIOS}

@app.post('/admin/redteam/run-all')
async def redteam_run_all(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization)
    results=[run_redteam_case(graph,SYSTEM_PROMPT,x) for x in REDTEAM_SCENARIOS]
    s=db_session()
    try:
        for item in results:
            s.add(AIEvaluation(id='rt:'+uuid.uuid4().hex,scenario_id=item['scenario_id'],prompt=item['prompt'],response=item['response'],passed=item['passed'],issues=item['issues'],expected=[],created_at=datetime.utcnow()))
        s.commit()
    finally:s.close()
    return {'total':len(results),'passed':sum(x['passed'] for x in results),'score':round(sum(x['passed'] for x in results)/max(1,len(results))*100,1),'results':results,'note':'Red-team engineering tests, not clinical validation.'}

@app.get('/admin/security-events')
async def admin_security_events(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); s=db_session()
    try:
        rows=s.query(AuditLog).filter(AuditLog.action.in_(['login_failed','session_revoked','admin_login','login'])).order_by(AuditLog.created_at.desc()).limit(100).all()
        return {'events':[{'action':x.action,'actor_user_id':x.actor_user_id,'created_at':x.created_at.isoformat(timespec='seconds'),'result':x.result} for x in rows]}
    finally:s.close()

@app.get('/admin/readiness')
async def admin_readiness(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization)
    return readiness_snapshot()

@app.get('/admin/population-analytics')
async def admin_population(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);return population_analytics()

@app.get('/admin/outbreak-signals')
async def admin_outbreaks(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);return outbreak_signals()

@app.get('/admin/evaluation-scenarios')
async def admin_eval_scenarios(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);return {'scenarios':evaluation_scenarios()}

@app.get('/admin/benchmark')
async def admin_benchmark(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization)
    return benchmark_summary()

@app.post('/admin/evaluations/run')
async def admin_eval_run(payload:dict,authorization:Optional[str]=Header(default=None)):
    current_admin(authorization)
    scenario=next((x for x in evaluation_scenarios() if x['id']==payload.get('scenario_id')),None)
    if not scenario: raise HTTPException(404,'Evaluation scenario not found.')
    from .ai_benchmark import evaluate_scenario
    return evaluate_scenario(scenario)

@app.post('/admin/evaluations/run-all')
async def admin_eval_run_all(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization)
    from .ai_benchmark import run_benchmark
    results=run_benchmark()
    passed=sum(1 for x in results if x.get('passed'))
    return {'passed':passed,'total':len(results),'score':round(passed/max(1,len(results))*100,1),'results':results,'generated_at':datetime.utcnow().isoformat(timespec='seconds')}

@app.get('/admin/evaluations')
async def admin_evaluations(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);s=db_session()
    try:
        rows=s.query(AIEvaluation).order_by(AIEvaluation.created_at.desc()).limit(100).all();return {'evaluations':[{'id':x.id,'scenario_id':x.scenario_id,'prompt':x.prompt,'response':x.response,'passed':x.passed,'issues':x.issues or [],'expected':x.expected or [],'created_at':x.created_at.isoformat(timespec='seconds')} for x in rows]}
    finally:s.close()

@app.get('/admin/analytics')
async def admin_analytics(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);s=db_session()
    try:
        users=s.query(User).filter(User.role=='user').count();messages=s.query(Conversation).count();reports=s.query(Report).count();events=s.query(EmergencyEvent).count();success=s.query(EmergencyEvent).filter(EmergencyEvent.call_success==True).count()
    finally:s.close()
    return {'registered_users':users,'conversation_messages':messages,'health_reports':reports,'emergency_events':events,'successful_calls':success,'failed_calls':events-success,'ai':ai_analytics()}

@app.get('/admin/database/status')
async def admin_db_status(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);return database_health()

@app.get('/admin/ai-events')
async def ai_events(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);s=db_session()
    try:
        rows=s.query(AIEvent).order_by(AIEvent.created_at.desc()).limit(200).all();return {'events':[{'id':x.id,'event_type':x.event_type,'user_id':x.user_id,'details':x.details,'created_at':x.created_at.isoformat(timespec='seconds')} for x in rows]}
    finally:s.close()

@app.get('/admin/audit-logs')
async def audit_logs(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);s=db_session()
    try:
        rows=s.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all();return {'events':[{'id':x.id,'actor_user_id':x.actor_user_id,'action':x.action,'resource_type':x.resource_type,'resource_id':x.resource_id,'result':x.result,'created_at':x.created_at.isoformat(timespec='seconds'),'metadata':x.metadata_json or {}} for x in rows]}
    finally:s.close()

@app.get('/admin/users')
async def users_admin(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);s=db_session()
    try:return {'users':[public_user(x) for x in s.query(User).filter(User.role!='admin').order_by(User.created_at.desc()).all()]}
    finally:s.close()

@app.get('/admin/users/{user_id}')
async def user_admin(user_id:str,authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);s=db_session();u=s.query(User).filter_by(user_id=user_id).first();s.close()
    if not u:raise HTTPException(404,'User not found.')
    log_audit(u.user_id,'admin_patient_view','patient',user_id)
    return {'user':public_user(u),'history':[{'role':r,'message':m} for r,m in get_history(user_id,50)],'health_state':get_health_state(user_id),'timeline':get_timeline(user_id,100),'followup':get_followup(user_id),'handoff':latest_handoff(user_id),'report':latest_report_data(user_id)}


@app.get('/admin/knowledge-sources')
async def admin_knowledge_sources(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization); return {'sources':list_sources()}

@app.put('/admin/knowledge-sources/{source_id}')
async def admin_knowledge_update(source_id:str,payload:dict,authorization:Optional[str]=Header(default=None)):
    admin=current_admin(authorization); row=update_source(source_id,payload)
    if not row: raise HTTPException(404,'Knowledge source not found.')
    log_audit(admin.user_id,'knowledge_source_updated','knowledge',source_id)
    return {'success':True,'source':next(x for x in list_sources() if x['id']==source_id)}

@app.post('/admin/knowledge-sources/{source_id}/review')
async def admin_knowledge_review(source_id:str,payload:dict,authorization:Optional[str]=Header(default=None)):
    admin=current_admin(authorization); ok=review_source(source_id,admin.user_id,str(payload.get('decision','reviewed')),str(payload.get('notes','')))
    if not ok: raise HTTPException(404,'Knowledge source not found.')
    log_audit(admin.user_id,'knowledge_source_reviewed','knowledge',source_id,metadata={'decision':payload.get('decision','reviewed')})
    return {'success':True}

@app.get('/admin/knowledge-reviews/{source_id}')
async def admin_knowledge_reviews(source_id:str,authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);s=db_session()
    try:
        rows=s.query(KnowledgeReview).filter_by(source_id=source_id).order_by(KnowledgeReview.created_at.desc()).limit(50).all()
        return {'reviews':[{'decision':r.decision,'notes':r.notes,'reviewer_user_id':r.reviewer_user_id,'created_at':r.created_at.isoformat(timespec='seconds')} for r in rows]}
    finally:s.close()

@app.get('/admin/security/posture')
async def admin_security_posture(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization)
    db=database_health()
    s=db_session()
    try:
        recent_failures=s.query(LoginAttempt).filter(LoginAttempt.success==False).order_by(LoginAttempt.created_at.desc()).limit(50).count()
        active_sessions=s.query(LoginSession).filter(LoginSession.revoked==False,LoginSession.expires_at>datetime.utcnow()).count()
        revoked=s.query(RevokedToken).count() if 'RevokedToken' in globals() else 0
    finally:s.close()
    return {'database':db,'recent_failed_logins':recent_failures,'active_sessions':active_sessions,'revoked_tokens':revoked,'controls':['role-based authorization','expiring sessions','token revocation','rate limiting','CORS allowlist','security headers','audit logging'],'note':'Operational security posture only; not an independent security audit.'}

@app.get('/admin/emergencies')
async def emergencies(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);s=db_session()
    try:
        rows=s.query(EmergencyEvent).order_by(EmergencyEvent.timestamp.desc()).limit(200).all();return {'events':[{'timestamp':x.timestamp.isoformat(timespec='seconds'),'user_id':x.user_id,'user_name':x.user_name,'channel':x.channel,'reason':x.reason,'contact':x.contact,'call_success':x.call_success,'call_sid':x.call_sid,'call_status':x.call_status} for x in rows]}
    finally:s.close()

@app.get('/admin/reports')
async def reports_admin(authorization:Optional[str]=Header(default=None)):
    current_admin(authorization);s=db_session()
    try:
        rows=s.query(Report).order_by(Report.created_at.desc()).limit(200).all();return {'reports':[{'user_id':x.user_id,'user_name':(x.payload or {}).get('user_name',''),'mainProblem':(x.payload or {}).get('mainProblem',''),'severity':(x.payload or {}).get('severity',''),'risk':(x.risk or {}).get('level',''),'created_at':x.created_at.isoformat(timespec='seconds')} for x in rows]}
    finally:s.close()

@app.post('/reports/{report_id}/document')
async def report_document(report_id:str,file:UploadFile=File(...),authorization:Optional[str]=Header(default=None)):
    u=current_user(authorization);s=db_session();rep=s.query(Report).filter_by(id=report_id,user_id=u.user_id).first();s.close()
    if not rep:raise HTTPException(404,'Report not found.')
    content=await file.read()
    if len(content)>MAX_REQUEST_BYTES:raise HTTPException(413,'Document too large.')
    try:path=upload_report_document(u.user_id,report_id,file.filename or 'report.pdf',content,file.content_type or 'application/octet-stream')
    except Exception as e:raise HTTPException(503,f'Storage upload unavailable: {e}')
    return {'success':True,'path':path}

if __name__=='__main__':uvicorn.run(app,host='0.0.0.0',port=int(os.getenv('PORT','8000')))
