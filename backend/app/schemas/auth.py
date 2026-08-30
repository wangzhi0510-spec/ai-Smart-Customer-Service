from pydantic import BaseModel, Field, field_validator
import re
class AuthRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        value=value.strip().lower()
        if not (re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) or re.fullmatch(r"1[3-9]\d{9}", value)):
            raise ValueError("请输入有效邮箱或中国大陆手机号")
        return value
class PublicUser(BaseModel):
    id: str
    email: str|None = None
    phone: str|None = None
    status: str
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: PublicUser

