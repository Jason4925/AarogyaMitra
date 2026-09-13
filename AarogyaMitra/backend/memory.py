from .db import db_session, Conversation, User
from datetime import datetime

def save_message(user_id,role,message):
    s=db_session()
    try:s.add(Conversation(user_id=user_id,role=role,message=str(message),created_at=datetime.utcnow()));s.commit()
    finally:s.close()

def get_history(user_id,limit=50):
    s=db_session()
    try:
        rows=s.query(Conversation).filter_by(user_id=user_id).order_by(Conversation.id.desc()).limit(limit).all();return [(x.role,x.message) for x in reversed(rows)]
    finally:s.close()

def reset_user_memory(user_id):
    s=db_session()
    try:s.query(Conversation).filter_by(user_id=user_id).delete();s.commit()
    finally:s.close()

def get_memory_enabled(user_id):
    s=db_session()
    try:
        u=s.query(User.memory_enabled).filter_by(user_id=user_id).first();return bool(u[0]) if u else True
    finally:s.close()

def set_memory_enabled(user_id,enabled):
    s=db_session()
    try:
        u=s.query(User).filter_by(user_id=user_id).first()
        if not u:return False
        u.memory_enabled=bool(enabled);s.commit();return True
    finally:s.close()
