from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base
from backend.app.models.user import TimestampMixin
class MessageFeedback(TimestampMixin, Base):
    __tablename__="message_feedback"
    __table_args__=(UniqueConstraint("message_id","user_id",name="uq_feedback_message_user"),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    message_id: Mapped[str]=mapped_column(ForeignKey("messages.id"),index=True,nullable=False)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),index=True,nullable=False)
    rating: Mapped[str]=mapped_column(String(16),nullable=False)
    comment: Mapped[str|None]=mapped_column(Text,nullable=True)
    message=relationship("Message",back_populates="feedback")
