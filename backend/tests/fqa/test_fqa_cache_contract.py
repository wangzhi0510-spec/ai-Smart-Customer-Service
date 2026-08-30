import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.base import Base
from backend.app.fqa.preprocess import normalize_question
from backend.app.services.fqa_service import FQAService


class FakeRedis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, seconds, value):
        self.values[key] = value


def test_exact_cache_is_checked_before_database():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    question = "占位问题"
    redis = FakeRedis()
    cache_key = "fqa:exact:" + hashlib.sha256(normalize_question(question).encode()).hexdigest()

    with Session(engine) as db:
        service = FQAService(db, redis=redis)
        service._cache_set(cache_key, {"answer": "缓存答案", "entry_id": "cached"})
        result = service.query(question, "user-1")

    assert result.answer == "缓存答案"
    assert result.entry_id == "cached"
    assert result.matched is True
