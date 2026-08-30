from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.db.session import get_session
from backend.app.models.user import User
_password_hash = PasswordHash.recommended()
_bearer = HTTPBearer(auto_error=False)
def hash_password(password: str) -> str: return _password_hash.hash(password)
def verify_password(password: str, password_hash: str) -> bool: return _password_hash.verify(password, password_hash)
def create_access_token(user_id: str, settings: Settings) -> str:
    now=datetime.now(timezone.utc)
    return jwt.encode({"sub":user_id,"iat":now,"exp":now+timedelta(minutes=settings.jwt_access_token_expire_minutes)}, settings.jwt_secret_key or "development-only-secret-key-32-bytes-long", algorithm=settings.jwt_algorithm)
def decode_access_token(token: str, settings: Settings) -> str:
    try:
        payload=jwt.decode(token, settings.jwt_secret_key or "development-only-secret-key-32-bytes-long", algorithms=[settings.jwt_algorithm])
        subject=payload.get("sub")
        if not isinstance(subject,str) or not subject: raise ValueError
        return subject
    except (jwt.PyJWTError, ValueError) as exc:
        raise AppError("UNAUTHORIZED","身份认证失败",401) from exc

def get_current_user(credentials: HTTPAuthorizationCredentials|None = Depends(_bearer), db: Session = Depends(get_session)) -> User:
    if credentials is None: raise AppError("UNAUTHORIZED","身份认证失败",401)
    from backend.app.core.config import Settings
    user_id=decode_access_token(credentials.credentials, Settings.from_env())
    user=db.get(User,user_id)
    if user is None or user.status != "active": raise AppError("UNAUTHORIZED","身份认证失败",401)
    return user


