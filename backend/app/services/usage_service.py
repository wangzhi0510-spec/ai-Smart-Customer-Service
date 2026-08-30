from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.errors import AppError
from backend.app.models.usage import UsageRecord


@dataclass(frozen=True)
class UsageReservation:
    user_id: str
    usage_date: date
    redis_key: str
    count: int
    persisted: bool = True


class UsageService:
    def __init__(self, db: Session, redis: Any | None = None, daily_limit: int = 100):
        self.db = db
        self.redis = redis
        self.daily_limit = daily_limit

    def reserve(self, user_id: UUID | str) -> UsageReservation:
        user_id_text = str(user_id)
        usage_date = datetime.now(timezone.utc).date()
        redis_key = f"usage:{user_id_text}:{usage_date.isoformat()}"
        redis_count: int | None = None
        redis_available = self.redis is not None
        if redis_available:
            try:
                redis_count = int(self.redis.incr(redis_key))
                if redis_count == 1:
                    self.redis.expire(redis_key, 172800)
                if redis_count > self.daily_limit:
                    self.redis.decr(redis_key)
                    raise AppError("DAILY_QUOTA_EXCEEDED", "今日提问次数已达上限", 429)
            except AppError:
                raise
            except Exception:
                # A Redis outage must fall back to the durable DB check, never to an unlimited path.
                redis_available = False
                redis_count = None

        try:
            record = self.db.scalar(
                select(UsageRecord).where(
                    UsageRecord.user_id == user_id_text,
                    UsageRecord.usage_date == usage_date,
                )
            )
            if record is None:
                record = UsageRecord(
                    id=str(uuid4()), user_id=user_id_text, usage_date=usage_date, question_count=0
                )
                self.db.add(record)
            if record.question_count >= self.daily_limit:
                self.db.rollback()
                if redis_available and redis_count is not None:
                    self.redis.decr(redis_key)
                raise AppError("DAILY_QUOTA_EXCEEDED", "今日提问次数已达上限", 429)
            record.question_count += 1
            self.db.commit()
            return UsageReservation(user_id_text, usage_date, redis_key, record.question_count)
        except AppError:
            raise
        except Exception as exc:
            self.db.rollback()
            if redis_available and redis_count is not None:
                try:
                    self.redis.decr(redis_key)
                except Exception:
                    pass
            raise AppError("USAGE_PERSISTENCE_ERROR", "配额记录暂时不可用", 503) from exc

    def compensate(self, reservation: UsageReservation) -> None:
        try:
            record = self.db.scalar(
                select(UsageRecord).where(
                    UsageRecord.user_id == reservation.user_id,
                    UsageRecord.usage_date == reservation.usage_date,
                )
            )
            if record is not None and record.question_count > 0:
                record.question_count -= 1
                self.db.commit()
        except Exception:
            self.db.rollback()
        if self.redis is not None:
            try:
                self.redis.decr(reservation.redis_key)
            except Exception:
                pass

