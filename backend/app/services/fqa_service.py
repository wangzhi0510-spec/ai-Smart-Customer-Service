from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.fqa.bm25_search import BM25Search
from backend.app.fqa.preprocess import normalize_question
from backend.app.models.fqa import FQAEntry


@dataclass(frozen=True)
class FQAResult:
    answer: str | None
    matched: bool
    entry_id: str | None
    score: float
    should_use_rag: bool


class FQAService:
    def __init__(self, db: Session, redis: Any | None = None, threshold: float = 0.92):
        self.db = db
        self.redis = redis
        self.threshold = threshold

    def query(self, question: str, user_id: str) -> FQAResult:
        normalized = normalize_question(question)
        cache_key = "fqa:exact:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        cached = self._cache_get(cache_key)
        if cached is not None:
            return FQAResult(cached["answer"], True, cached["entry_id"], 1.0, False)

        entries = list(
            self.db.scalars(
                select(FQAEntry).where(
                    FQAEntry.is_active.is_(True), or_(FQAEntry.user_id.is_(None), FQAEntry.user_id == user_id)
                )
            ).all()
        )
        exact = next((entry for entry in entries if normalize_question(entry.question) == normalized), None)
        if exact is not None:
            result = {"answer": exact.answer, "entry_id": exact.id}
            self._cache_set(cache_key, result)
            return FQAResult(exact.answer, True, exact.id, 1.0, False)

        candidates = BM25Search([{"id": e.id, "answer": e.answer, "question": e.question, "threshold": e.similarity_threshold} for e in entries]).search(question, 5)
        if not candidates:
            return FQAResult(None, False, None, 0.0, True)
        candidate = candidates[0]
        threshold = float(candidate.get("threshold", self.threshold))
        if candidate["score"] < threshold:
            return FQAResult(None, False, None, float(candidate["score"]), True)
        return FQAResult(candidate["answer"], True, candidate["id"], float(candidate["score"]), False)

    def _cache_get(self, key: str) -> dict[str, str] | None:
        if self.redis is None:
            return None
        try:
            value = self.redis.get(key)
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            return json.loads(value) if value else None
        except Exception:
            return None

    def _cache_set(self, key: str, value: dict[str, str]) -> None:
        if self.redis is None:
            return
        try:
            encoded = json.dumps(value, ensure_ascii=False)
            if hasattr(self.redis, "setex"):
                self.redis.setex(key, 86400, encoded)
            else:
                self.redis.set(key, encoded)
                if hasattr(self.redis, "expire"):
                    self.redis.expire(key, 86400)
        except Exception:
            pass
