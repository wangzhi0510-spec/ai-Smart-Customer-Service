from __future__ import annotations

import logging
from typing import Any, Callable

from backend.app.rag.retrieval.contracts import ContextDocument

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, backend: Callable[[str, list[ContextDocument]], list[ContextDocument]] | Any | None = None):
        self.backend = backend
        self.last_warning: str | None = None

    def rank(self, question: str, contexts: list[ContextDocument]) -> list[ContextDocument]:
        self.last_warning = None
        if self.backend is None:
            self.last_warning = "RERANKER_UNAVAILABLE"
            logger.warning("reranker unavailable; preserving retrieval order")
            return contexts
        try:
            ranked = self.backend(question, contexts) if callable(self.backend) else self.backend.rank(question, contexts)
            return list(ranked)
        except Exception:
            self.last_warning = "RERANKER_UNAVAILABLE"
            logger.warning("reranker failed; preserving retrieval order")
            return contexts
