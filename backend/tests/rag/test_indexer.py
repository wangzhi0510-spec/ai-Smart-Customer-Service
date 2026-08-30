from uuid import uuid4

from backend.app.rag.chunker import ChunkRecord
from backend.app.rag.indexer import DocumentIndexer
from backend.app.adapters.embedding import EmbeddingBatch
from backend.app.adapters.milvus_client import MilvusClient


class FakeEmbedding:
    def embed(self, texts: list[str]) -> EmbeddingBatch:
        return EmbeddingBatch(
            dense=[[float(index), 1.0] for index, _ in enumerate(texts)],
            sparse=[{"token": float(index + 1)} for index, _ in enumerate(texts)],
        )


class FakeMilvus:
    def __init__(self):
        self.inserted = []

    def insert(self, chunks):
        self.inserted.extend(chunks)
        return len(chunks)


def test_indexer_builds_dense_sparse_vectors_and_metadata():
    document_id = uuid4()
    chunks = [
        ChunkRecord("child-1", "parent-1", "退款规则", "guide.txt", 2, "退款", 1, 1, "退款规则完整父块")
    ]
    milvus = FakeMilvus()

    result = DocumentIndexer(FakeEmbedding(), milvus).index(
        chunks, user_id=uuid4(), document_id=document_id, version=3
    )

    assert result == 1
    vector = milvus.inserted[0]
    assert vector.document_id == document_id
    assert vector.version == 3
    assert vector.active_version is False
    assert vector.parent_id == "parent-1"
    assert vector.page_number == 2
    assert vector.dense == [0.0, 1.0]
    assert vector.sparse == {"token": 1.0}


def test_milvus_schema_contains_filter_and_source_fields():
    fields = MilvusClient.schema_fields()

    assert {"user_id", "document_id", "version", "parent_id", "page_number", "source_name", "active_version", "dense", "sparse"} <= set(fields)
