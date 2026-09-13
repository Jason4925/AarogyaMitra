from datetime import datetime
import json
from pathlib import Path
from .db import db_session, KnowledgeSource, KnowledgeReview

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_FILE = BASE_DIR / 'knowledge' / 'sources.json'

def seed_sources():
    try:
        items = json.loads(SOURCE_FILE.read_text(encoding='utf-8'))
    except Exception:
        items = []
    s = db_session()
    try:
        existing = {row.id for row in s.query(KnowledgeSource.id).all()}
        for item in items:
            if item.get('id') in existing:
                continue
            s.add(KnowledgeSource(
                id=item.get('id','source:'+str(len(existing))),
                title=item.get('title',''), topic=item.get('topic',''), source=item.get('source',''),
                url=item.get('url',''), summary=item.get('summary',''),
                specific_triggers=item.get('specific_triggers',[]) or [], status='active',
                version=str(item.get('version','1.0')), last_reviewed=item.get('last_reviewed',''), next_review=item.get('next_review','')
            ))
        s.commit()
    finally:
        s.close()

def list_sources():
    seed_sources()
    s=db_session()
    try:
        rows=s.query(KnowledgeSource).order_by(KnowledgeSource.title.asc()).all()
        return [{
            'id':r.id,'title':r.title,'topic':r.topic,'source':r.source,'url':r.url,
            'summary':r.summary,'specific_triggers':r.specific_triggers or [],'status':r.status,
            'version':r.version,'last_reviewed':r.last_reviewed,'next_review':r.next_review,
            'updated_at':r.updated_at.isoformat(timespec='seconds') if r.updated_at else ''
        } for r in rows]
    finally:
        s.close()

def update_source(source_id, changes):
    s=db_session()
    try:
        row=s.query(KnowledgeSource).filter_by(id=source_id).first()
        if not row:
            return None
        for key in ['title','topic','source','url','summary','specific_triggers','status','version','last_reviewed','next_review']:
            if key in changes:
                setattr(row,key,changes[key])
        row.updated_at=datetime.utcnow()
        s.commit()
        s.refresh(row)
        return row
    finally:
        s.close()

def review_source(source_id, reviewer_user_id, decision, notes=''):
    s=db_session()
    try:
        row=s.query(KnowledgeSource).filter_by(id=source_id).first()
        if not row:
            return None
        row.last_reviewed=datetime.utcnow().date().isoformat()
        if decision.lower() in {'disable','inactive','reject'}:
            row.status='inactive'
        elif decision.lower() in {'approve','active','reviewed'}:
            row.status='active'
        s.add(KnowledgeReview(
            id='kr:'+datetime.utcnow().strftime('%Y%m%d%H%M%S%f'),
            source_id=source_id, reviewer_user_id=reviewer_user_id,
            decision=decision, notes=notes, created_at=datetime.utcnow()
        ))
        s.commit()
        return True
    finally:
        s.close()
