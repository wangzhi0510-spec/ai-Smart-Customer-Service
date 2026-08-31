from __future__ import annotations

from typing import Any

from backend.app.adapters.milvus_client import MilvusClient


class MilvusSearchAdapter:
    """Search adapter exposing the retrieval strategy contract over Milvus."""

    def __init__(self, client: MilvusClient, mode: str):
        if mode not in {"dense", "sparse"}:
            raise ValueError("mode must be dense or sparse")
        self.client = client
        self.mode = mode

    def search(self, query: Any, *, user_id: str, source_filter: list[str] | None, limit: int):
        method = self.client.search_dense if self.mode == "dense" else self.client.search_sparse
        return method(query, user_id=user_id, source_filter=source_filter, limit=limit)
