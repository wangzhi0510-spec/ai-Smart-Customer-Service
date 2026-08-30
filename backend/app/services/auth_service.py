from __future__ import annotations
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.errors import AppError
from backend.app.core.security import create_access_token,hash_password,verify_password
from backend.app.models.user import User
from backend.app.schemas.auth import PublicUser,TokenResponse
class AuthService:
    def __init__(self, db: Session, settings=None): self.db=db; self.settings=settings
    @staticmethod
    def _parts(identifier: str) -> tuple[str|None,str|None]:
        value=identifier.strip().lower()
        if "@" in value: return value,None
        if re.fullmatch(r"1[3-9]\d{9}",value): return None,value
        raise AppError("VALIDATION_ERROR","请输入有效邮箱或中国大陆手机号",422)
    def register(self, identifier: str, password: str) -> User:
        email,phone=self._parts(identifier)
        if len(password)<8: raise AppError("VALIDATION_ERROR","密码长度至少为 8 位",422)
        query=select(User).where(User.email==email if email else User.phone==phone)
        if self.db.scalar(query): raise AppError("CONFLICT","标识已注册",409)
        user=User(id=__import__("uuid").uuid4().hex,email=email,phone=phone,password_hash=hash_password(password))
        self.db.add(user); self.db.commit(); self.db.refresh(user); return user
    def authenticate(self, identifier: str, password: str) -> TokenResponse:
        email,phone=self._parts(identifier)
        user=self.db.scalar(select(User).where(User.email==email if email else User.phone==phone))
        if user is None or not verify_password(password,user.password_hash): raise AppError("UNAUTHORIZED","标识或密码错误",401)
        settings=self.settings
        token=create_access_token(user.id,settings)
        return TokenResponse(access_token=token,user=PublicUser.model_validate(user,from_attributes=True))

