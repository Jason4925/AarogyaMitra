"""Auditable, topic-specific retrieval for trusted health sources.

The base catalog lives in knowledge/sources.json and is mirrored into the
PostgreSQL/SQLite knowledge_sources table. Active database records override the
static catalog so an administrator can disable or review sources without code changes.
"""
from pathlib import Path
import json
from re import findall

BASE_DIR=Path(__file__).resolve().parent.parent
SOURCE_FILE=BASE_DIR/'knowledge'/'sources.json'
try:
    STATIC_KNOWLEDGE=json.loads(SOURCE_FILE.read_text(encoding='utf-8'))
except Exception:
    STATIC_KNOWLEDGE=[]

STOP={'the','a','an','is','are','for','to','of','and','or','i','me','my','have','what','how','can','in','on','with','do','does','this','that','it','about','please','tell','give','information','health','issue','problem','symptom','symptoms','want','need','help','could','would','should'}
ALIASES={'sugar':'diabetes','high sugar':'diabetes','bp':'hypertension','blood pressure':'hypertension','breathlessness':'shortness of breath','breathing problem':'shortness of breath','loose motion':'diarrhea','loose motions':'diarrhea','vomit':'vomiting','head pain':'headache','migraine headache':'migraine'}

def _tokens(text:str):
    raw=[x.lower() for x in findall(r'[a-zA-Z]{2,}',text or '')]
    joined=' '.join(raw)
    expanded=[canonical for phrase,canonical in ALIASES.items() if phrase in joined]
    return {x for x in raw+expanded if x not in STOP}

def _db_sources():
    try:
        from .db import db_session, KnowledgeSource
        s=db_session()
        try:
            rows=s.query(KnowledgeSource).filter(KnowledgeSource.status=='active').all()
            return [{
                'id':r.id,'topic':r.topic,'title':r.title,'summary':r.summary,'source':r.source,
                'url':r.url,'specific_triggers':r.specific_triggers or [],'status':r.status
            } for r in rows]
        finally:
            s.close()
    except Exception:
        return []

def _catalog():
    by_id={str(x.get('id')):x for x in STATIC_KNOWLEDGE if isinstance(x,dict)}
    for item in _db_sources():
        by_id[str(item.get('id'))]=item
    return list(by_id.values())

def retrieve(query:str, limit:int=3):
    q=(query or '').lower().strip()
    q_tokens=_tokens(q)
    if not q_tokens: return []
    scored=[]
    for item in _catalog():
        if str(item.get('status','active')).lower()=='inactive': continue
        specific=[str(x).lower().strip() for x in item.get('specific_triggers',[]) if x]
        direct_hits=[x for x in specific if x and x in q]
        topic_tokens=_tokens(item.get('topic','')); title_tokens=_tokens(item.get('title','')); summary_tokens=_tokens(item.get('summary',''))
        if specific and not direct_hits and len(q_tokens & (topic_tokens|title_tokens)) < 2: continue
        score=(len(direct_hits)*12)+(len(q_tokens&title_tokens)*6)+(len(q_tokens&topic_tokens)*4)+(len(q_tokens&summary_tokens))
        if score>=4: scored.append((score,item))
    scored.sort(key=lambda x:(-x[0],x[1].get('title','')))
    return [item for _,item in scored[:limit]]

def build_context(query:str,limit:int=3):
    sources=retrieve(query,limit)
    if not sources:return '',[]
    lines=['TRUSTED KNOWLEDGE RETRIEVAL. Use only these sources when directly relevant to the user query:']
    for item in sources:
        lines.append(f"- {item['title']} [{item['source']}]: {item['summary']} Source: {item['url']}")
    return '\n'.join(lines),sources
