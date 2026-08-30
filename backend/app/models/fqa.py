from sqlalchemy import String, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base
from backend.app.models.user import TimestampMixin
class FQAEntry(TimestampMixin, Base):
    __tablename__="fqa_entries"
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    user_id: Mapped[str|None]=mapped_column(ForeignKey("users.id"),nullable=True,index=True)
    question: Mapped[str]=mapped_column(String(1000),nullable=False)
    answer: Mapped[str]=mapped_column(Text,nullable=False)
    similarity_threshold: Mapped[float]=mapped_column(Float,default=0.92,nullable=False)
    is_active: Mapped[bool]=mapped_column(Boolean,default=True,nullable=False)
