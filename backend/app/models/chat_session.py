from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base
from backend.app.models.user import TimestampMixin
class ChatSession(TimestampMixin, Base):
    __tablename__="chat_sessions"
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),index=True,nullable=False)
    title: Mapped[str]=mapped_column(String(255),default="新会话",nullable=False)
    is_deleted: Mapped[bool]=mapped_column(Boolean,default=False,nullable=False)
    messages=relationship("Message",back_populates="session",cascade="all, delete-orphan")

