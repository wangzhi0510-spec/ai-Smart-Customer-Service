from datetime import date
from sqlalchemy import String, Integer, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base
from backend.app.models.user import TimestampMixin
class UsageRecord(TimestampMixin, Base):
    __tablename__="usage_records"
    __table_args__=(UniqueConstraint("user_id","usage_date",name="uq_usage_user_date"),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),index=True,nullable=False)
    usage_date: Mapped[date]=mapped_column(Date,nullable=False)
    question_count: Mapped[int]=mapped_column(Integer,default=0,nullable=False)

