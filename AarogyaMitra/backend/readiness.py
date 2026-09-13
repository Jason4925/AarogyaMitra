from datetime import datetime
from .db import db_session, ReadinessItem

INTELLIGENCE_ITEMS = [
    ("personal-health-intelligence","Personal Health Intelligence","active","Health Intelligence","Longitudinal profile, risk trends and patient-specific context."),
    ("care-pathways","Care Pathways","active","Clinical Product","Risk-aware next-step pathways and routing."),
    ("decision-engine","Decision Engine","active","AarogyaMitra Core","Deterministic risk and routing decisions outside the LLM."),
    ("knowledge-governance","Knowledge Governance","active","Medical Content","Versioned reviewed source catalog and retrieval rules."),
    ("continuous-ai-evaluation","Continuous AI Evaluation","active","AI Safety","Repeatable safety scenarios and evaluation history."),
    ("better-explainability","Better Explainability","active","AI Safety","Risk factors, rationale and recommended action."),
    ("product-analytics","Product Analytics","active","Product","Usage, completion, quality and safety metrics."),
]

EVIDENCE_ITEMS = [
    ("clinical-validation","Clinical validation","planned","Clinical Partnerships","Prospective validation study / clinician review required before clinical claims."),
    ("ai-benchmark","AI benchmark","active","AI Safety","Benchmark suite for emergency handling, uncertainty and unsafe-output prevention."),
    ("real-world-studies","Real-world studies","planned","Research","Field evaluation with target communities and outcomes measurement."),
    ("security-audits","Security audits","planned","Security","External penetration test, dependency review and infrastructure audit."),
    ("privacy-governance","Privacy governance","active","Privacy","Consent controls, audit logging, export and deletion workflows."),
    ("healthcare-partnerships","Healthcare partnerships","planned","Partnerships","Hospitals, clinics, public-health teams and clinician advisory network."),
    ("interoperability","Interoperability","planned","Platform","Standards-based exchange; FHIR/ABDM alignment should be validated before production use."),
    ("scalability","Scalability","active","Platform","PostgreSQL/Supabase backend, stateless API deployment and async-friendly architecture."),
]

def seed_readiness():
    s=db_session()
    try:
        existing={x.id for x in s.query(ReadinessItem.id).all()}
        rows=[]
        for category,name,status,owner,notes in INTELLIGENCE_ITEMS:
            rid='intel:'+category
            if rid not in existing: rows.append(ReadinessItem(id=rid,category='intelligence',name=name,status=status,owner=owner,last_reviewed=datetime.utcnow().date().isoformat(),notes=notes))
        for slug,name,status,owner,notes in EVIDENCE_ITEMS:
            rid='evidence:'+slug
            if rid not in existing: rows.append(ReadinessItem(id=rid,category='evidence',name=name,status=status,owner=owner,last_reviewed=datetime.utcnow().date().isoformat(),notes=notes))
        if rows: s.add_all(rows); s.commit()
    finally: s.close()

def readiness_snapshot():
    seed_readiness()
    s=db_session()
    try:
        rows=s.query(ReadinessItem).order_by(ReadinessItem.category,ReadinessItem.name).all()
        return {'items':[{'id':x.id,'category':x.category,'name':x.name,'status':x.status,'owner':x.owner,'last_reviewed':x.last_reviewed,'notes':x.notes} for x in rows]}
    finally: s.close()
