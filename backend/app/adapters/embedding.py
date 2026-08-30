from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from backend.app.core.errors import AppError


@dataclass(frozen=True)
class EmbeddingBatch:
    dense: list[list[float]]
    sparse: list[dict[str, float]]


class EmbeddingProvider:
    """Lazy local bge-m3 adapter; tests and deployments may inject a backend."""

    def __init__(self, model_path: str = "", backend: Callable[[list[str]], EmbeddingBatch] | Any | None = None):
        self.model_path = model_path
        self._backend = backend
        self._model = None

    def embed(self, texts: list[str]) -> EmbeddingBatch:
        if not texts:
            return EmbeddingBatch([], [])
        if self._backend is not None:
            result = self._backend(texts) if callable(self._backend) else self._backend.embed(texts)
            if not isinstance(result, EmbeddingBatch):
                raise AppError("EMBEDDING_INVALID_RESPONSE", "Embedding 返回格式无效", 503)
            return result
        if not self.model_path:
            raise AppError("EMBEDDING_UNAVAILABLE", "Embedding 模型未配置", 503)
        if self._model is None:
            try:
                from FlagEmbedding import BGEM3FlagModel

                self._model = BGEM3FlagModel(self.model_path, use_fp16=False)
            except Exception as exc:
                raise AppError("EMBEDDING_UNAVAILABLE", "Embedding 模型暂时不可用", 503) from exc
        try:
            result = self._model.encode(texts, return_dense=True, return_sparse=True)
            dense = result["dense_vecs"].tolist()
            sparse = [dict(item) for item in result["lexical_weights"]]
            return EmbeddingBatch(dense=dense, sparse=sparse)
        except Exception as exc:
            raise AppError("EMBEDDING_FAILED", "Embedding 生成失败", 503) from exc
