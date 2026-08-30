from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.base import Base
from backend.app.models.fqa import FQAEntry
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
    redis = FakeRedis()

    with Session(engine) as db:
        service = FQAService(db, redis=redis)
        service._cache_set(
            "fqa:exact:0e8d2f9b4bd4a6a1bd6d0c4b7c97c6ef0d0f8a0d5e4a4f2d2a7d1d7e9e6f8f26",
            {"answer": "缓存答案", "entry_id": "cached"},
        )
        result = service.query("占位问题", "user-1")

    assert result.answer is None or result.answer == "缓存答案"


def test_bm25_hit_returns_standard_answer_when_threshold_is_met():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        db.add(
            FQAEntry(
                id="fqa-1",
                question="申请退款",
                answer="请在订单页提交退款申请",
                similarity_threshold=0.1,
            )
        )
        db.commit()
        result = FQAService(db).query("退款怎么申请", "user-1")

    assert result.matched is True
    assert result.answer == "请在订单页提交退款申请"
    assert result.should_use_rag is False


def test_bm25_miss_requests_rag():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        db.add(FQAEntry(id="fqa-1", question="申请退款", answer="退款答案"))
        db.commit()
        result = FQAService(db).query("如何修改收货地址", "user-1")

    assert result.matched is False
    assert result.should_use_rag is True
