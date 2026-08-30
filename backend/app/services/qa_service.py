from __future__ import annotations

import time
from dataclasses import dataclass, field

from backend.app.core.errors import AppError
from backend.app.rag.context_builder import build_context
from backend.app.rag.prompts import build_rag_messages


@dataclass(frozen=True)
class QAResult:
    answer: str
    answer_type: str
    retrieval_strategy: str | None = None
    sources: list[dict] = field(default_factory=list)
    latency_ms: int = 0
    warnings: list[str] = field(default_factory=list)


class QAService:
    def __init__(self, fqa, retrieval, llm, history_provider=None, context_token_budget: int = 3000):
        self.fqa = fqa
        self.retrieval = retrieval
        self.llm = llm
        self.history_provider = history_provider
        self.context_token_budget = context_token_budget

    def answer(self, question: str, session_id: str, user_id: str) -> QAResult:
        started = time.perf_counter()
        if not question or not question.strip():
            raise AppError("VALIDATION_ERROR", "问题不能为空", 422)
        fqa = self.fqa.query(question, user_id)
        if fqa.matched:
            return QAResult(fqa.answer or "", "fqa", sources=[], latency_ms=self._latency(started))
        retrieval = self.retrieval.retrieve(question, user_id, None)
        if not retrieval.contexts:
            return QAResult("知识库暂无足够信息回答该问题。", "fallback", retrieval.strategy, [], self._latency(started), retrieval.warnings)
        history = self.history_provider(session_id, user_id) if self.history_provider else []
        context = build_context(retrieval.contexts, self.context_token_budget)
        answer = self.llm.complete(build_rag_messages(question, history, context))
        sources = [
            {"document_id": item.document_id, "document_name": item.source_name, "page_number": item.page_number,
             "section_title": item.section_title, "excerpt": item.text[:500], "retrieval_score": item.score}
            for item in retrieval.contexts
        ]
        return QAResult(answer, "rag", retrieval.strategy, sources, self._latency(started), retrieval.warnings)

    @staticmethod
    def _latency(started: float) -> int:
        return max(0, int((time.perf_counter() - started) * 1000))
