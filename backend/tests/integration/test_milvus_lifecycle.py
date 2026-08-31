from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.adapters.embedding import EmbeddingBatch, EmbeddingProvider
from backend.app.adapters.milvus_client import MilvusClient, VectorChunk
from backend.app.db.base import Base
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.app.rag.indexer import DocumentIndexer
from backend.app.rag.parsers.base import ParsedPage
from backend.app.rag.retrieval.contracts import SearchHit
from backend.app.rag.retrieval.hybrid_direct import HybridDirectStrategy
from backend.app.workers.document_tasks import DocumentTaskProcessor


class FakeMilvusBackend:
    def __init__(self, fail_insert=False):
        self.rows = []
        self.ensure_calls = 0
        self.fail_insert = fail_insert

    def ensure_collection(self):
        self.ensure_calls += 1

    def insert(self, chunks):
        if self.fail_insert:
            raise RuntimeError("milvus unavailable")
        self.rows.extend(chunks)
        return len(chunks)

    def activate_version(self, document_id, version):
        for row in self.rows:
            if str(row.document_id) == str(document_id):
                row.active_version = row.version == version

    def delete_by_document(self, document_id):
        self.rows = [row for row in self.rows if str(row.document_id) != str(document_id)]


class FakeParser:
    def parse(self, path):
        return [ParsedPage("Refunds are available within 30 days. " * 40, 1, Path(path).name, "Refunds")]


def make_indexer(backend):
    def embed(texts):
        return EmbeddingBatch(
            dense=[[0.1, 0.2] for _ in texts],
            sparse=[{"refund": 1.0} for _ in texts],
        )

    return DocumentIndexer(EmbeddingProvider(backend=embed), MilvusClient(backend=backend))


def make_database_document(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    document_path = tmp_path / "refund-policy.txt"
    document_path.write_text("Refunds are available within 30 days.", encoding="utf-8")
    user_id = str(uuid4())
    document_id = str(uuid4())
    db = Session(engine)
    db.add(User(id=user_id, email=f"{uuid4().hex[:8]}@example.com", password_hash="test-hash"))
    db.add(
        Document(
            id=document_id,
            user_id=user_id,
            original_name=document_path.name,
            storage_path=str(document_path),
            media_type="text/plain",
            size_bytes=document_path.stat().st_size,
            content_sha256="a" * 64,
            status="pending",
        )
    )
    db.commit()
    return db, document_id


@pytest.mark.integration
def test_milvus_lifecycle_ensures_inserts_activates_and_deletes_rows():
    backend = FakeMilvusBackend()
    client = MilvusClient(backend=backend, collection_name="test_chunks")
    document_id = uuid4()
    row = VectorChunk(
        id="chunk-1",
        user_id=uuid4(),
        document_id=document_id,
        version=1,
        parent_id="parent-1",
        child_text="refund policy",
        parent_text="refund policy parent",
        source_name="policy.txt",
        page_number=1,
        section_title=None,
        chunk_order=0,
        dense=[0.1, 0.2],
        sparse={"refund": 1.0},
    )

    client.ensure_collection()
    assert backend.ensure_calls == 1
    assert client.insert([row]) == 1
    client.activate_version(document_id, 1)
    assert backend.rows[0].active_version is True

    client.delete_by_document(document_id)
    assert backend.rows == []


@pytest.mark.integration
def test_document_worker_indexes_activates_and_deletes_vectors(tmp_path):
    db, document_id = make_database_document(tmp_path)
    backend = FakeMilvusBackend()
    indexer = make_indexer(backend)

    result = DocumentTaskProcessor(db, parser=FakeParser(), indexer=indexer).process(document_id)

    document = db.get(Document, document_id)
    assert result.status == "ready"
    assert document.status == "ready"
    assert document.chunk_count == len(backend.rows) > 0
    assert all(row.active_version for row in backend.rows)

    indexer.delete_by_document(document_id)
    assert backend.rows == []
    db.close()


@pytest.mark.integration
def test_document_worker_cleans_vectors_and_marks_database_row_failed(tmp_path):
    db, document_id = make_database_document(tmp_path)
    backend = FakeMilvusBackend(fail_insert=True)

    result = DocumentTaskProcessor(db, parser=FakeParser(), indexer=make_indexer(backend)).process(document_id)

    document = db.get(Document, document_id)
    assert result.status == "failed"
    assert document.status == "failed"
    assert document.error_code == "INDEXING_FAILED"
    assert backend.rows == []
    db.close()


class FakeSearch:
    def __init__(self, hits):
        self.hits = hits

    def search(self, embedding, *, user_id, source_filter, limit):
        return self.hits


class FakeQueryEmbedding:
    def embed(self, texts):
        return EmbeddingBatch(dense=[[0.1, 0.2]], sparse=[{"refund": 1.0}])


def search_hit(identifier, user_id, source_name="refund-policy.txt", active=True):
    return SearchHit(
        id=identifier,
        score=0.9,
        user_id=user_id,
        document_id=f"document-{identifier}",
        version=1,
        parent_id=f"parent-{identifier}",
        child_text="refund period",
        parent_text="Refunds are available within 30 days.",
        source_name=source_name,
        page_number=1,
        section_title="Refunds",
        active_version=active,
    )


@pytest.mark.integration
def test_hybrid_retrieval_enforces_user_source_and_active_version_filters():
    hits = [
        search_hit("allowed", "user-1"),
        search_hit("other-user", "user-2"),
        search_hit("other-source", "user-1", source_name="account-guide.txt"),
        search_hit("inactive", "user-1", active=False),
    ]
    strategy = HybridDirectStrategy(FakeQueryEmbedding(), FakeSearch(hits), FakeSearch(hits), top_n=5)

    result = strategy.retrieve("What is the refund period?", "user-1", ["refund-policy.txt"])

    assert [context.parent_id for context in result.contexts] == ["parent-allowed"]
