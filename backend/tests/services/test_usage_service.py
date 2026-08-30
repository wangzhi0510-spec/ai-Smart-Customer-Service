from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.core.errors import AppError
from backend.app.db.base import Base
from backend.app.models.usage import UsageRecord
from backend.app.services.usage_service import UsageService


class FakeRedis:
    def __init__(self):
        self.values = {}

    def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    def decr(self, key):
        self.values[key] = max(0, int(self.values.get(key, 0)) - 1)
        return self.values[key]

    def expire(self, key, seconds):
        return True


def test_usage_reserves_the_101st_question_as_quota_exceeded():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    user_id = uuid4()
    redis = FakeRedis()

    with Session(engine) as db:
        service = UsageService(db, redis=redis, daily_limit=100)
        for _ in range(100):
            service.reserve(user_id)

        with pytest.raises(AppError) as exc_info:
            service.reserve(user_id)

        assert exc_info.value.code == "DAILY_QUOTA_EXCEEDED"
        record = db.scalar(select(UsageRecord).where(UsageRecord.user_id == str(user_id)))
        assert record.question_count == 100


def test_compensate_removes_a_failed_reservation_from_redis_and_mysql():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    user_id = uuid4()
    redis = FakeRedis()

    with Session(engine) as db:
        service = UsageService(db, redis=redis, daily_limit=100)
        reservation = service.reserve(user_id)
        assert reservation.count == 1

        service.compensate(reservation)

        record = db.scalar(select(UsageRecord).where(UsageRecord.user_id == str(user_id)))
        assert record.question_count == 0
        assert redis.values[reservation.redis_key] == 0
