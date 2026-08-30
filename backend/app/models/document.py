from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base
from backend.app.models.user import TimestampMixin
class Document(TimestampMixin, Base):
    __tablename__="documents"
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),index=True,nullable=False)
    original_name: Mapped[str]=mapped_column(String(255),nullable=False)
    storage_path: Mapped[str]=mapped_column(String(1024),nullable=False)
    media_type: Mapped[str]=mapped_column(String(128),nullable=False)
    size_bytes: Mapped[int]=mapped_column(Integer,nullable=False)
    content_sha256: Mapped[str]=mapped_column(String(64),nullable=False)
    status: Mapped[str]=mapped_column(String(16),default="pending",nullable=False)
    version: Mapped[int]=mapped_column(Integer,default=1,nullable=False)
    supersedes_document_id: Mapped[str|None]=mapped_column(ForeignKey("documents.id"),nullable=True)
    error_code: Mapped[str|None]=mapped_column(String(64),nullable=True)
    error_message: Mapped[str|None]=mapped_column(String(1024),nullable=True)
    chunk_count: Mapped[int]=mapped_column(Integer,default=0,nullable=False)
    processing_started_at: Mapped[DateTime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    processed_at: Mapped[DateTime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    deleted_at: Mapped[DateTime|None]=mapped_column(DateTime(timezone=True),nullable=True)
