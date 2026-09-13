from datetime import datetime
from .db import db_session, AuditLog

def log_audit(actor_user_id, action, resource_type='', resource_id='', result='success', ip_address='', metadata=None):
    s=db_session()
    try:
        s.add(AuditLog(actor_user_id=actor_user_id,action=action,resource_type=resource_type,resource_id=resource_id,result=result,ip_address=ip_address or '',metadata_json=metadata or {},created_at=datetime.utcnow()));s.commit()
    finally:s.close()
