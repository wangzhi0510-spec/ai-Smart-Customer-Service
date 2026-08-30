from sqlalchemy import String, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base
from backend.app.models.user import TimestampMixin
class Message(TimestampMixin, Base):
    __tablename__="messages"
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    session_id: Mapped[str]=mapped_column(ForeignKey("chat_sessions.id"),index=True,nullable=False)
    role: Mapped[str]=mapped_column(String(16),nullable=False)
    content: Mapped[str]=mapped_column(Text,nullable=False)
    answer_type: Mapped[str|None]=mapped_column(String(16),nullable=True)
    retrieval_strategy: Mapped[str|None]=mapped_column(String(64),nullable=True)
    status: Mapped[str]=mapped_column(String(16),default="completed",nullable=False)
    latency_ms: Mapped[int|None]=mapped_column(Integer,nullable=True)
    session=relationship("ChatSession",back_populates="messages")
    sources=relationship("MessageSource",back_populates="message",cascade="all, delete-orphan")
    feedback=relationship("MessageFeedback",back_populates="message",uselist=False,cascade="all, delete-orphan")
class MessageSource(Base):
    __tablename__="message_sources"
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    message_id: Mapped[str]=mapped_column(ForeignKey("messages.id"),index=True,nullable=False)
    document_id: Mapped[str]=mapped_column(ForeignKey("documents.id"),index=True,nullable=False)
    document_name: Mapped[str]=mapped_column(String(255),nullable=False)
    page_number: Mapped[int|None]=mapped_column(Integer,nullable=True)
    section_title: Mapped[str|None]=mapped_column(String(255),nullable=True)
    excerpt: Mapped[str]=mapped_column(Text,nullable=False)
    retrieval_score: Mapped[float|None]=mapped_column(Float,nullable=True)
    rerank_score: Mapped[float|None]=mapped_column(Float,nullable=True)
    display_order: Mapped[int]=mapped_column(Integer,default=0,nullable=False)
    message=relationship("Message",back_populates="sources")
