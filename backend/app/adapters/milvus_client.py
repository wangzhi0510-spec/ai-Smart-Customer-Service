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
                collection = Collection(self.collection_name)
                self._ensure_indexes(collection)
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
            collection = Collection(self.collection_name, schema=schema)
            self._ensure_indexes(collection)
        except Exception as exc:
            raise AppError("MILVUS_UNAVAILABLE", "Milvus 暂时不可用", 503) from exc

    @staticmethod
    def _ensure_indexes(collection: Any) -> None:
        existing = {getattr(index, "field_name", None) for index in (getattr(collection, "indexes", None) or [])}
        index_specs = {
            "dense": {"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 128}},
            "sparse": {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP", "params": {"drop_ratio_build": 0.2}},
        }
        for field_name, index_params in index_specs.items():
            if field_name not in existing:
                collection.create_index(field_name=field_name, index_params=index_params)

    def search_dense(self, vector: list[float], *, user_id: str, source_filter: list[str] | None, limit: int):
        return self._search(vector, "dense", user_id=user_id, source_filter=source_filter, limit=limit)

    def search_sparse(self, vector: dict[str, float], *, user_id: str, source_filter: list[str] | None, limit: int):
        return self._search(vector, "sparse", user_id=user_id, source_filter=source_filter, limit=limit)

    def _search(self, vector: Any, anns_field: str, *, user_id: str, source_filter: list[str] | None, limit: int):
        if self.backend is not None:
            method = getattr(self.backend, f"search_{anns_field}", None)
            if method is None:
                raise AppError("MILVUS_UNAVAILABLE", "Milvus 检索暂时不可用", 503)
            return method(vector, user_id=user_id, source_filter=source_filter, limit=limit)
        try:
            from pymilvus import Collection
            from backend.app.rag.retrieval.contracts import SearchHit

            self.ensure_collection()
            collection = Collection(self.collection_name)
            collection.load()
            escaped_user = str(user_id).replace('"', '\\"')
            expr = f'user_id == "{escaped_user}" and active_version == true'
            if source_filter:
                names = ','.join(f'"{str(name).replace(chr(34), chr(92)+chr(34))}"' for name in source_filter)
                expr += f" and source_name in [{names}]"
            metric = "COSINE" if anns_field == "dense" else "IP"
            params = {"metric_type": metric, "params": {"nprobe": 16}}
            hits = collection.search(
                data=[vector], anns_field=anns_field, param=params, limit=limit,
                expr=expr, output_fields=[
                    "user_id", "document_id", "version", "parent_id", "child_text", "parent_text",
                    "source_name", "page_number", "section_title", "active_version", "chunk_order",
                ],
            )
            return [
                SearchHit(
                    id=str(hit.id), score=float(hit.distance), user_id=row.get("user_id", ""),
                    document_id=row.get("document_id", ""), version=int(row.get("version", 1)),
                    parent_id=row.get("parent_id", ""), child_text=row.get("child_text", ""),
                    parent_text=row.get("parent_text", ""), source_name=row.get("source_name", ""),
                    page_number=row.get("page_number"), section_title=row.get("section_title"),
                    active_version=bool(row.get("active_version", True)), chunk_order=int(row.get("chunk_order", 0)),
                )
                for hit in hits[0] for row in [hit.entity]
            ]
        except AppError:
            raise
        except Exception as exc:
            raise AppError("MILVUS_UNAVAILABLE", "Milvus 检索暂时不可用", 503) from exc
    def insert(self, chunks: list[VectorChunk]) -> int:
        if not chunks:
            return 0
        if self.backend is not None:
            return int(self.backend.insert(chunks))
        try:
            from pymilvus import Collection

            self.ensure_collection()
            collection = Collection(self.collection_name)
            rows = [
                {
                    "id": chunk.id,
                    "user_id": str(chunk.user_id),
                    "document_id": str(chunk.document_id),
                    "version": chunk.version,
                    "parent_id": chunk.parent_id,
                    "child_text": chunk.child_text,
                    "parent_text": chunk.parent_text,
                    "source_name": chunk.source_name,
                    "page_number": chunk.page_number,
                    "section_title": chunk.section_title or "",
                    "chunk_order": chunk.chunk_order,
                    "dense": chunk.dense,
                    "sparse": chunk.sparse,
                    "active_version": chunk.active_version,
                    "created_at": int((chunk.created_at or datetime.now(timezone.utc)).timestamp()),
                }
                for chunk in chunks
            ]
            result = collection.insert(rows)
            flush = getattr(collection, "flush", None)
            if flush is not None:
                flush()
            return int(getattr(result, "insert_count", len(rows)))
        except AppError:
            raise
        except Exception as exc:
            raise AppError("MILVUS_UNAVAILABLE", "Milvus 写入暂时不可用", 503) from exc

    def activate_version(self, document_id: UUID | str, version: int) -> None:
        if self.backend is not None and hasattr(self.backend, "activate_version"):
            self.backend.activate_version(document_id, version)
            return
        if self.backend is None:
            for chunk in self._memory:
                if str(chunk.document_id) == str(document_id):
                    chunk.active_version = chunk.version == version
            try:
                from pymilvus import Collection

                self.ensure_collection()
                collection = Collection(self.collection_name)
                escaped_document = str(document_id).replace('"', '\\"')
                rows = collection.query(
                    expr=f'document_id == "{escaped_document}"',
                    output_fields=list(self.FIELDS),
                )
                updates = [
                    {**row, "active_version": int(row.get("version", 0)) == version}
                    for row in rows
                ]
                if updates:
                    collection.upsert(updates)
                    flush = getattr(collection, "flush", None)
                    if flush is not None:
                        flush()
            except AppError:
                raise
            except Exception as exc:
                raise AppError("MILVUS_UNAVAILABLE", "Milvus 更新暂时不可用", 503) from exc

    def delete_by_document(self, document_id: UUID | str) -> None:
        if self.backend is not None:
            self.backend.delete_by_document(document_id)
            return
        self._memory = [chunk for chunk in self._memory if str(chunk.document_id) != str(document_id)]
        try:
            from pymilvus import Collection

            self.ensure_collection()
            collection = Collection(self.collection_name)
            escaped_document = str(document_id).replace('"', '\\"')
            collection.delete(expr=f'document_id == "{escaped_document}"')
            flush = getattr(collection, "flush", None)
            if flush is not None:
                flush()
        except AppError:
            raise
        except Exception as exc:
            raise AppError("MILVUS_UNAVAILABLE", "Milvus 删除暂时不可用", 503) from exc
