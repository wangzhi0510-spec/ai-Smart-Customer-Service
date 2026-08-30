from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
class User(TimestampMixin, Base):
    __tablename__="users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str|None] = mapped_column(String(320), unique=True, nullable=True)
    phone: Mapped[str|None] = mapped_column(String(32), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
