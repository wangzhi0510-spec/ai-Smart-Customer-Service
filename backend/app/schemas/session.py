from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str = Field(default="新会话", min_length=1, max_length=255)


class SessionRead(BaseModel):
    id: str
    title: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceRead(BaseModel):
    id: str
    document_id: str
    document_name: str
    page_number: int | None = None
    section_title: str | None = None
    excerpt: str
    retrieval_score: float | None = None
    rerank_score: float | None = None
    display_order: int

    model_config = {"from_attributes": True}


class MessageRead(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    answer_type: str | None = None
    retrieval_strategy: str | None = None
    status: str
    latency_ms: int | None = None
    created_at: datetime
    sources: list[SourceRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class FeedbackUpdate(BaseModel):
    rating: Literal["positive", "negative"]
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackRead(BaseModel):
    id: str
    message_id: str
    user_id: str
    rating: Literal["positive", "negative"]
    comment: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
