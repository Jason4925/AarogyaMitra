import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey, text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool
from .config import DATABASE_URL, DATABASE_POOLING

BASE_DIR = Path(__file__).resolve().parent.parent
url = DATABASE_URL or f"sqlite:///{(BASE_DIR / 'aarogyamitra_local.db').as_posix()}"
if url.startswith('postgres://'):
    url = 'postgresql+psycopg://' + url[len('postgres://'):]
elif url.startswith('postgresql://') and '+psycopg' not in url:
    url = 'postgresql+psycopg://' + url[len('postgresql://'):]
elif url.startswith('postgresql+psycopg2://'):
    url = 'postgresql+psycopg://' + url[len('postgresql+psycopg2://'):]

kwargs = {'future': True, 'pool_pre_ping': True}
if url.startswith('postgresql') and not DATABASE_POOLING:
    kwargs['poolclass'] = NullPool
if url.startswith('sqlite'):
    kwargs['connect_args'] = {'check_same_thread': False}

engine = create_engine(url, **kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__='users'
    user_id: Mapped[str]=mapped_column(String(80),primary_key=True)
    name: Mapped[str]=mapped_column(String(100))
    email: Mapped[str]=mapped_column(String(200),unique=True,index=True)
    phone: Mapped[str]=mapped_column(String(30),default='')
    role: Mapped[str]=mapped_column(String(20),default='user',index=True)
    password_hash: Mapped[str]=mapped_column(Text)
    location: Mapped[str]=mapped_column(String(255),default='')
    preferred_language: Mapped[str]=mapped_column(String(40),default='English')
    emergency_contact: Mapped[str]=mapped_column(String(40),default='')
    age: Mapped[str]=mapped_column(String(10),default='',nullable=True)
    gender: Mapped[str]=mapped_column(String(40),default='')
    conditions: Mapped[list]=mapped_column(JSON,default=list)
    allergies: Mapped[str]=mapped_column(Text,default='')
    memory_enabled: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class RevokedToken(Base):
    __tablename__='revoked_tokens'
    jti: Mapped[str]=mapped_column(String(100),primary_key=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime,index=True)


class LoginSession(Base):
    __tablename__='login_sessions'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    jti: Mapped[str]=mapped_column(String(100),unique=True,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime,index=True)
    revoked: Mapped[bool]=mapped_column(Boolean,default=False,index=True)

class LoginAttempt(Base):
    __tablename__='login_attempts'
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    email: Mapped[str]=mapped_column(String(200),index=True)
    user_id: Mapped[str|None]=mapped_column(String(80),nullable=True,index=True)
    success: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    ip_address: Mapped[str]=mapped_column(String(64),default='')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class Conversation(Base):
    __tablename__='conversations'
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    role: Mapped[str]=mapped_column(String(20))
    message: Mapped[str]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class HealthState(Base):
    __tablename__='health_states'
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),primary_key=True)
    symptoms: Mapped[list]=mapped_column(JSON,default=list)
    duration: Mapped[str]=mapped_column(String(100),default='')
    severity: Mapped[int|None]=mapped_column(Integer,nullable=True)
    red_flags: Mapped[list]=mapped_column(JSON,default=list)
    last_updated: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)

class Report(Base):
    __tablename__='reports'
    id: Mapped[str]=mapped_column(String(80),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    payload: Mapped[dict]=mapped_column(JSON)
    risk: Mapped[dict]=mapped_column(JSON)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
    document_path: Mapped[str]=mapped_column(String(500),default='')

class TimelineEvent(Base):
    __tablename__='health_timeline'
    id: Mapped[str]=mapped_column(String(80),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    event_type: Mapped[str]=mapped_column(String(40))
    title: Mapped[str]=mapped_column(String(255))
    severity: Mapped[int|None]=mapped_column(Integer,nullable=True)
    urgency: Mapped[str]=mapped_column(String(20),default='')
    summary: Mapped[str]=mapped_column(Text,default='')
    source: Mapped[str]=mapped_column(String(40),default='')
    timestamp: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
    metadata_json: Mapped[dict]=mapped_column(JSON,default=dict)

class Followup(Base):
    __tablename__='followups'
    id: Mapped[str]=mapped_column(String(80),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    concern: Mapped[str]=mapped_column(Text)
    previous_severity: Mapped[int]=mapped_column(Integer)
    previous_urgency: Mapped[str]=mapped_column(String(20),default='')
    due_date: Mapped[datetime]=mapped_column(DateTime,index=True)
    status: Mapped[str]=mapped_column(String(20),default='pending',index=True)
    completed_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    comparison: Mapped[str]=mapped_column(String(30),default='')
    current_severity: Mapped[int|None]=mapped_column(Integer,nullable=True)
    notes: Mapped[str]=mapped_column(Text,default='')

class Handoff(Base):
    __tablename__='handoffs'
    id: Mapped[str]=mapped_column(String(80),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    data: Mapped[dict]=mapped_column(JSON)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class EmergencyEvent(Base):
    __tablename__='emergency_events'
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    user_id: Mapped[str]=mapped_column(String(80),index=True)
    user_name: Mapped[str]=mapped_column(String(100),default='')
    channel: Mapped[str]=mapped_column(String(40),default='')
    reason: Mapped[str]=mapped_column(Text)
    contact: Mapped[str]=mapped_column(String(40),default='')
    call_success: Mapped[bool]=mapped_column(Boolean,default=False)
    call_sid: Mapped[str]=mapped_column(String(100),default='')
    call_status: Mapped[str]=mapped_column(String(50),default='')
    timestamp: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class AIEvent(Base):
    __tablename__='ai_events'
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    user_id: Mapped[str|None]=mapped_column(String(80),nullable=True,index=True)
    event_type: Mapped[str]=mapped_column(String(50),index=True)
    details: Mapped[dict]=mapped_column(JSON,default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class Consent(Base):
    __tablename__='consents'
    __table_args__=(UniqueConstraint('user_id','consent_type',name='uq_consent_user_type'),)
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    consent_type: Mapped[str]=mapped_column(String(50),index=True)
    granted: Mapped[bool]=mapped_column(Boolean,default=False)
    version: Mapped[str]=mapped_column(String(20),default='1.0')
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class AIEvaluation(Base):
    __tablename__='ai_evaluations'
    id: Mapped[str]=mapped_column(String(80),primary_key=True)
    scenario_id: Mapped[str]=mapped_column(String(80),index=True)
    prompt: Mapped[str]=mapped_column(Text)
    response: Mapped[str]=mapped_column(Text)
    passed: Mapped[bool]=mapped_column(Boolean,default=False)
    issues: Mapped[list]=mapped_column(JSON,default=list)
    expected: Mapped[list]=mapped_column(JSON,default=list)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class DashboardSignal(Base):
    __tablename__='dashboard_signals'
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    signal_type: Mapped[str]=mapped_column(String(50),default='refresh')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class AuditLog(Base):
    __tablename__='audit_logs'
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    actor_user_id: Mapped[str|None]=mapped_column(String(80),nullable=True,index=True)
    action: Mapped[str]=mapped_column(String(100),index=True)
    resource_type: Mapped[str]=mapped_column(String(80),default='')
    resource_id: Mapped[str]=mapped_column(String(100),default='')
    result: Mapped[str]=mapped_column(String(30),default='success')
    ip_address: Mapped[str]=mapped_column(String(64),default='')
    metadata_json: Mapped[dict]=mapped_column(JSON,default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class ReadinessItem(Base):
    __tablename__='readiness_items'
    id: Mapped[str]=mapped_column(String(80),primary_key=True)
    category: Mapped[str]=mapped_column(String(40),index=True)
    name: Mapped[str]=mapped_column(String(160))
    status: Mapped[str]=mapped_column(String(30),default='planned')
    owner: Mapped[str]=mapped_column(String(120),default='')
    last_reviewed: Mapped[str]=mapped_column(String(40),default='')
    notes: Mapped[str]=mapped_column(Text,default='')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)


class DoctorNote(Base):
    __tablename__='doctor_notes'
    id: Mapped[str]=mapped_column(String(80),primary_key=True)
    patient_user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    doctor_user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    handoff_id: Mapped[str]=mapped_column(String(80),default='',index=True)
    note: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(30),default='reviewed',index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class KnowledgeSource(Base):
    __tablename__='knowledge_sources'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    title: Mapped[str]=mapped_column(String(255))
    topic: Mapped[str]=mapped_column(String(255),default='')
    source: Mapped[str]=mapped_column(String(160),default='')
    url: Mapped[str]=mapped_column(String(500),default='')
    summary: Mapped[str]=mapped_column(Text,default='')
    specific_triggers: Mapped[list]=mapped_column(JSON,default=list)
    status: Mapped[str]=mapped_column(String(30),default='active',index=True)
    version: Mapped[str]=mapped_column(String(40),default='1.0')
    last_reviewed: Mapped[str]=mapped_column(String(40),default='')
    next_review: Mapped[str]=mapped_column(String(40),default='')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class KnowledgeReview(Base):
    __tablename__='knowledge_reviews'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    source_id: Mapped[str]=mapped_column(ForeignKey('knowledge_sources.id',ondelete='CASCADE'),index=True)
    reviewer_user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    decision: Mapped[str]=mapped_column(String(30),default='reviewed')
    notes: Mapped[str]=mapped_column(Text,default='')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)


def init_db():
    Base.metadata.create_all(engine)
    if engine.url.get_backend_name() == 'postgresql':
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS memory_enabled BOOLEAN DEFAULT TRUE"))
            conn.execute(text("ALTER TABLE public.users ALTER COLUMN age SET DEFAULT ''"))
            # Repair legacy nullable rows before enforcing the application invariant.
            conn.execute(text("UPDATE public.users SET age='' WHERE age IS NULL"))

def db_session():
    return SessionLocal()

def database_health():
    from datetime import datetime
    s=db_session()
    try:
        s.execute(text('SELECT 1'))
        counts={
            'users':s.query(User).count(),
            'conversations':s.query(Conversation).count(),
            'reports':s.query(Report).count(),
            'timeline':s.query(TimelineEvent).count(),
            'followups':s.query(Followup).count(),
            'handoffs':s.query(Handoff).count(),
            'emergencies':s.query(EmergencyEvent).count(),
            'ai_events':s.query(AIEvent).count(),
            'audit_logs':s.query(AuditLog).count(),
            'consents':s.query(Consent).count(),
            'ai_evaluations':s.query(AIEvaluation).count(),
            'safety_rules':s.query(SafetyRule).count(),
            'measurements':s.query(HealthMeasurement).count(),
            'documents':s.query(HealthDocument).count(),
            'handoff_shares':s.query(HandoffShare).count(),
            'caregiver_access':s.query(CaregiverAccess).count(),
            'feedback_tickets':s.query(FeedbackTicket).count(),
            'recommendations':s.query(RecommendationRecord).count(),
            'emergency_acknowledgements':s.query(EmergencyAcknowledgement).count(),
            'clinical_labels':s.query(ClinicalLabel).count(),
        }
        return {'connected':True,'database':engine.url.get_backend_name(),'driver':engine.url.drivername,'counts':counts,'checked_at':datetime.utcnow().isoformat(timespec='seconds')}
    finally:s.close()

class SafetyRule(Base):
    __tablename__='safety_rules'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    name: Mapped[str]=mapped_column(String(180))
    description: Mapped[str]=mapped_column(Text,default='')
    version: Mapped[str]=mapped_column(String(40),default='1.0')
    status: Mapped[str]=mapped_column(String(30),default='draft',index=True)
    evidence_source: Mapped[str]=mapped_column(String(500),default='')
    evidence_url: Mapped[str]=mapped_column(String(1000),default='')
    review_date: Mapped[str]=mapped_column(String(40),default='')
    reviewer: Mapped[str]=mapped_column(String(160),default='')
    applicable_population: Mapped[list]=mapped_column(JSON,default=list)
    contraindications: Mapped[list]=mapped_column(JSON,default=list)
    human_review_required: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class HealthMeasurement(Base):
    __tablename__='health_measurements'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    metric: Mapped[str]=mapped_column(String(80),index=True)
    value: Mapped[str]=mapped_column(String(120))
    unit: Mapped[str]=mapped_column(String(40),default='')
    measured_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
    source: Mapped[str]=mapped_column(String(40),default='user')
    note: Mapped[str]=mapped_column(Text,default='')
    verified: Mapped[bool]=mapped_column(Boolean,default=False)
    provenance: Mapped[dict]=mapped_column(JSON,default=dict)

class HealthDocument(Base):
    __tablename__='health_documents'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    filename: Mapped[str]=mapped_column(String(255))
    content_type: Mapped[str]=mapped_column(String(120),default='')
    storage_path: Mapped[str]=mapped_column(String(1000),default='')
    extracted: Mapped[dict]=mapped_column(JSON,default=dict)
    confirmed: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class HandoffShare(Base):
    __tablename__='handoff_shares'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    handoff_id: Mapped[str]=mapped_column(String(100),index=True)
    access_code_hash: Mapped[str]=mapped_column(String(255))
    token_hash: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime,index=True)
    revoked: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    accessed_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    included: Mapped[list]=mapped_column(JSON,default=list)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class CaregiverAccess(Base):
    __tablename__='caregiver_access'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    patient_user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    caregiver_name: Mapped[str]=mapped_column(String(120))
    caregiver_contact: Mapped[str]=mapped_column(String(120),default='')
    permissions: Mapped[list]=mapped_column(JSON,default=list)
    expires_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
    active: Mapped[bool]=mapped_column(Boolean,default=True,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class FeedbackTicket(Base):
    __tablename__='feedback_tickets'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    user_id: Mapped[str|None]=mapped_column(ForeignKey('users.user_id',ondelete='SET NULL'),nullable=True,index=True)
    category: Mapped[str]=mapped_column(String(80),index=True)
    severity: Mapped[str]=mapped_column(String(30),default='normal')
    description: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(30),default='open',index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
    resolved_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)

class RecommendationRecord(Base):
    __tablename__='recommendation_records'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    text: Mapped[str]=mapped_column(Text)
    evidence_source: Mapped[str]=mapped_column(String(500),default='')
    evidence_url: Mapped[str]=mapped_column(String(1000),default='')
    rule_version: Mapped[str]=mapped_column(String(80),default='')
    model_version: Mapped[str]=mapped_column(String(80),default='')
    confidence: Mapped[str]=mapped_column(String(30),default='medium')
    applicable_population: Mapped[list]=mapped_column(JSON,default=list)
    contraindications: Mapped[list]=mapped_column(JSON,default=list)
    human_review_required: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class EmergencyAcknowledgement(Base):
    __tablename__='emergency_acknowledgements'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    emergency_event_id: Mapped[int|None]=mapped_column(ForeignKey('emergency_events.id',ondelete='CASCADE'),nullable=True,index=True)
    acknowledged: Mapped[bool]=mapped_column(Boolean,default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class CarePathwayDecision(Base):
    __tablename__='care_pathway_decisions'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.user_id',ondelete='CASCADE'),index=True)
    risk_level: Mapped[str]=mapped_column(String(30),index=True)
    pathway: Mapped[str]=mapped_column(String(100))
    rule_version: Mapped[str]=mapped_column(String(80),default='')
    reasons: Mapped[list]=mapped_column(JSON,default=list)
    human_review_required: Mapped[bool]=mapped_column(Boolean,default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)

class ClinicalLabel(Base):
    __tablename__='clinical_labels'
    id: Mapped[str]=mapped_column(String(100),primary_key=True)
    case_id: Mapped[str]=mapped_column(String(120),index=True)
    reviewer: Mapped[str]=mapped_column(String(160))
    reviewed_status: Mapped[str]=mapped_column(String(30),default='pending')
    expected_urgency: Mapped[str]=mapped_column(String(30),default='')
    notes: Mapped[str]=mapped_column(Text,default='')
    rule_version: Mapped[str]=mapped_column(String(80),default='')
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,index=True)
