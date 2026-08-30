from __future__ import annotations

from uuid import UUID

from backend.app.adapters.embedding import EmbeddingProvider
from backend.app.adapters.milvus_client import MilvusClient, VectorChunk
from backend.app.rag.chunker import ChunkRecord


class DocumentIndexer:
    def __init__(self, embedding: EmbeddingProvider, milvus: MilvusClient):
        self.embedding = embedding
        self.milvus = milvus

    def index(self, chunks: list[ChunkRecord], user_id: UUID | str, document_id: UUID | str, version: int) -> int:
        if not chunks:
            return 0
        batch = self.embedding.embed([chunk.text for chunk in chunks])
        if len(batch.dense) != len(chunks) or len(batch.sparse) != len(chunks):
            raise ValueError("embedding batch length mismatch")
        vectors = [
            VectorChunk(
                id=chunk.id, user_id=user_id, document_id=document_id, version=version,
                parent_id=chunk.parent_id, child_text=chunk.text, parent_text=chunk.parent_text,
                source_name=chunk.source_name, page_number=chunk.page_number, section_title=chunk.section_title,
                chunk_order=chunk.order, dense=batch.dense[index], sparse=batch.sparse[index], active_version=False,
            )
            for index, chunk in enumerate(chunks)
        ]
        ensure = getattr(self.milvus, "ensure_collection", None)
        if ensure is not None:
            ensure()
        return self.milvus.insert(vectors)

    def activate_version(self, document_id: UUID | str, version: int) -> None:
        self.milvus.activate_version(document_id, version)

    def delete_by_document(self, document_id: UUID | str) -> None:
        self.milvus.delete_by_document(document_id)


