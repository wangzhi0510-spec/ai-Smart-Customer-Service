from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from backend.app.core.errors import AppError


@dataclass
class VectorChunk:
    id: str
    user_id: UUID | str
    document_id: UUID | str
    version: int
    parent_id: str
    child_text: str
    parent_text: str
    source_name: str
    page_number: int
    section_title: str | None
    chunk_order: int
    dense: list[float]
    sparse: dict[str, float]
    active_version: bool = False
    created_at: datetime | None = None


class MilvusClient:
    FIELDS = (
        "id", "user_id", "document_id", "version", "parent_id", "child_text", "parent_text",
        "source_name", "page_number", "section_title", "chunk_order", "dense", "sparse",
        "active_version", "created_at",
    )

    def __init__(self, backend: Any | None = None, host: str = "127.0.0.1", port: int = 19530, collection_name: str = "document_chunks"):
        self.backend = backend
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._memory: list[VectorChunk] = []

    @classmethod
    def schema_fields(cls) -> tuple[str, ...]:
        return cls.FIELDS

    def ensure_collection(self) -> None:
        if self.backend is not None:
            method = getattr(self.backend, "ensure_collection", None)
            if method:
                method()
            return
        try:
            from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

            connections.connect(alias="default", host=self.host, port=self.port)
            if utility.has_collection(self.collection_name):
                return
            schema = CollectionSchema([
                FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
                FieldSchema("user_id", DataType.VARCHAR, max_length=64),
                FieldSchema("document_id", DataType.VARCHAR, max_length=64),
                FieldSchema("version", DataType.INT64), FieldSchema("parent_id", DataType.VARCHAR, max_length=64),
                FieldSchema("child_text", DataType.VARCHAR, max_length=8192), FieldSchema("parent_text", DataType.VARCHAR, max_length=16384),
                FieldSchema("source_name", DataType.VARCHAR, max_length=255), FieldSchema("page_number", DataType.INT64),
                FieldSchema("section_title", DataType.VARCHAR, max_length=512), FieldSchema("chunk_order", DataType.INT64),
                FieldSchema("dense", DataType.FLOAT_VECTOR, dim=1024), FieldSchema("sparse", DataType.SPARSE_FLOAT_VECTOR),
                FieldSchema("active_version", DataType.BOOL), FieldSchema("created_at", DataType.INT64),
            ], description="AI customer service document chunks")
            Collection(self.collection_name, schema=schema)
        except Exception as exc:
            raise AppError("MILVUS_UNAVAILABLE", "Milvus 暂时不可用", 503) from exc

    def insert(self, chunks: list[VectorChunk]) -> int:
        if not chunks:
            return 0
        if self.backend is not None:
            return int(self.backend.insert(chunks))
        self.ensure_collection()
        self._memory.extend(chunks)
        return len(chunks)

    def activate_version(self, document_id: UUID | str, version: int) -> None:
        if self.backend is not None and hasattr(self.backend, "activate_version"):
            self.backend.activate_version(document_id, version)
            return
        for chunk in self._memory:
            if str(chunk.document_id) == str(document_id):
                chunk.active_version = chunk.version == version

    def delete_by_document(self, document_id: UUID | str) -> None:
        if self.backend is not None:
            self.backend.delete_by_document(document_id)
            return
        self._memory = [chunk for chunk in self._memory if str(chunk.document_id) != str(document_id)]

