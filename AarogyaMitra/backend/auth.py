import hashlib, hmac, secrets, uuid
from datetime import datetime, timedelta, timezone
import jwt
from .config import ADMIN_EMAIL, ADMIN_PASSWORD, JWT_SECRET, JWT_ALGORITHM, SESSION_HOURS
from .db import db_session, User, RevokedToken, LoginSession, LoginAttempt

PBKDF2_ROUNDS = 220_000

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, PBKDF2_ROUNDS)
    return f'{salt.hex()}${digest.hex()}'

def verify_password(password, encoded):
    try:
        salt_hex, digest_hex = encoded.split('$', 1)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), PBKDF2_ROUNDS)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False

def public_user(user):
    if not user: return None
    data = user if isinstance(user, dict) else {c.name: getattr(user, c.name) for c in user.__table__.columns}
    return {k: data.get(k, '') for k in ['user_id','name','email','phone','role','location','preferred_language','emergency_contact','age','gender','allergies','memory_enabled','created_at']} | {'conditions': data.get('conditions') or []}

def seed_admin():
    s=db_session()
    try:
        email=ADMIN_EMAIL.strip().lower(); user=s.query(User).filter_by(email=email).first()
        if not user:
            s.add(User(user_id='admin:'+secrets.token_hex(12), name='AarogyaMitra Admin', email=email, role='admin', password_hash=hash_password(ADMIN_PASSWORD), created_at=datetime.utcnow()))
            s.commit()
    finally: s.close()

def create_user(name,email,phone,password):
    if len(password)<8: raise ValueError('Password must be at least 8 characters.')
    s=db_session(); email=email.strip().lower()
    try:
        if s.query(User).filter_by(email=email).first(): raise ValueError('An account with this email already exists.')
        user=User(user_id='web:'+secrets.token_hex(16), name=name.strip(), email=email, phone=phone.strip(), password_hash=hash_password(password), created_at=datetime.utcnow())
        s.add(user); s.commit(); s.refresh(user); return public_user(user)
    finally:s.close()

def authenticate(email,password):
    s=db_session()
    try:
        normalized=email.strip().lower()
        user=s.query(User).filter_by(email=normalized).first()
        if not user or not verify_password(password,user.password_hash):
            try:
                s.add(LoginAttempt(email=normalized, user_id=user.user_id if user else None, success=False, created_at=datetime.utcnow())); s.commit()
            except Exception:
                s.rollback()
            return None
        now=datetime.now(timezone.utc); exp=now+timedelta(hours=SESSION_HOURS); jti=uuid.uuid4().hex
        try:
            s.add(LoginAttempt(email=user.email, user_id=user.user_id, success=True, created_at=datetime.utcnow()))
            s.add(LoginSession(id='ls:'+uuid.uuid4().hex, user_id=user.user_id, jti=jti, created_at=datetime.utcnow(), expires_at=exp.replace(tzinfo=None), revoked=False))
            s.commit()
        except Exception:
            s.rollback()
        token=jwt.encode({'sub':user.user_id,'email':user.email,'role':user.role,'iat':int(now.timestamp()),'exp':int(exp.timestamp()),'jti':jti}, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return {'token':token,'user':public_user(user)}
    finally:s.close()

def get_user_by_token(token):
    try:
        claims=jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    s=db_session()
    try:
        if s.query(RevokedToken).filter_by(jti=claims.get('jti')).first(): return None
        return s.query(User).filter_by(user_id=claims.get('sub')).first()
    finally:s.close()

def revoke_token(token):
    try: claims=jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={'verify_exp':False})
    except jwt.PyJWTError: return
    exp=datetime.fromtimestamp(claims.get('exp',0), timezone.utc).replace(tzinfo=None)
    s=db_session()
    try:
        jti=claims.get('jti')
        s.add(RevokedToken(jti=jti,expires_at=exp))
        session=s.query(LoginSession).filter_by(jti=jti).first()
        if session: session.revoked=True
        s.commit()
    finally:s.close()

