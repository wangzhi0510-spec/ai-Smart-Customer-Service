from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.app.adapters.reranker import Reranker
from .contracts import RetrievalResult, SearchHit
from .parent_recovery import recover_parents
from .rrf import rrf_fuse


class HybridDirectStrategy:
    def __init__(self, embedding: Any, dense_search: Any, sparse_search: Any, reranker: Reranker | None = None,
                 candidate_k: int = 20, top_n: int = 5, rrf_k: int = 60):
        self.embedding = embedding
        self.dense_search = dense_search
        self.sparse_search = sparse_search
        self.reranker = reranker or Reranker()
        self.candidate_k = candidate_k
        self.top_n = top_n
        self.rrf_k = rrf_k

    def retrieve(self, question: str, user_id: UUID | str, source_filter: list[str] | None = None) -> RetrievalResult:
        batch = self.embedding.embed([question])
        dense = self.dense_search.search(batch.dense[0], user_id=user_id, source_filter=source_filter, limit=self.candidate_k)
        sparse = self.sparse_search.search(batch.sparse[0], user_id=user_id, source_filter=source_filter, limit=self.candidate_k)
        filtered = self._filter_hits([*dense, *sparse], user_id, source_filter)
        by_id: dict[str, SearchHit] = {hit.id: hit for hit in filtered}
        fused = rrf_fuse([by_id[hit.id] for hit in dense if hit.id in by_id], [by_id[hit.id] for hit in sparse if hit.id in by_id], self.rrf_k)
        contexts = recover_parents(fused)
        contexts = self.reranker.rank(question, contexts)[: self.top_n]
        warnings = [self.reranker.last_warning] if self.reranker.last_warning else []
        return RetrievalResult(contexts=contexts, warnings=warnings)

    @staticmethod
    def _filter_hits(hits: list[SearchHit], user_id: UUID | str, source_filter: list[str] | None) -> list[SearchHit]:
        return [hit for hit in hits if str(hit.user_id) == str(user_id) and hit.active_version and (not source_filter or hit.source_name in source_filter)]

    def retrieve_hyde(self, *args, **kwargs):
        raise NotImplementedError("HyDE is reserved for phase two")

    def retrieve_subquery(self, *args, **kwargs):
        raise NotImplementedError("SubQuery is reserved for phase two")

    def retrieve_backtracking(self, *args, **kwargs):
        raise NotImplementedError("Backtracking is reserved for phase two")

