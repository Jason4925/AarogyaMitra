from __future__ import annotations
from datetime import datetime, timezone
from .db import db_session, RevokedToken, AuditLog, AIEvent, Conversation


def security_summary(user):
    s=db_session()
    try:
        failed = s.query(AuditLog).filter(AuditLog.actor_user_id==user.user_id, AuditLog.action=='login_failed').order_by(AuditLog.created_at.desc()).limit(10).all()
        events = s.query(AuditLog).filter(AuditLog.actor_user_id==user.user_id).order_by(AuditLog.created_at.desc()).limit(20).all()
        return {
            'account': {'user_id':user.user_id,'role':user.role,'created_at':user.created_at.isoformat() if user.created_at else ''},
            'memory_enabled': bool(user.memory_enabled),
            'recent_failed_logins': len(failed),
            'recent_security_events': [{'action':e.action,'result':e.result,'created_at':e.created_at.isoformat(timespec='seconds')} for e in events],
            'controls':['memory preference','clear conversation history','consent preferences','data export','account deletion'],
            'server_time':datetime.now(timezone.utc).isoformat()
        }
    finally: s.close()
