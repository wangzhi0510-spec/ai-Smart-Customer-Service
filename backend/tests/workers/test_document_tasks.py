from io import BytesIO
from pathlib import Path
from uuid import uuid4

import backend.app.db

from backend.app.models.document import Document
from backend.app.rag.parsers.base import ParsedPage
from backend.app.workers.document_tasks import DocumentTaskProcessor, DocumentTaskResult


class FakeDB:
    def __init__(self, document):
        self.document = document
        self.commits = 0

    def get(self, model, document_id):
        return self.document if self.document.id == document_id else None

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


class FakeParser:
    def parse(self, path):
        return [ParsedPage("退款规则。" * 100, 1, Path(path).name, "退款")]


class FakeIndexer:
    def __init__(self, fail=False):
        self.fail = fail
        self.deleted = []

    def index(self, chunks, user_id, document_id, version):
        if self.fail:
            raise RuntimeError("milvus timeout")
        return len(chunks)

    def delete_by_document(self, document_id):
        self.deleted.append(document_id)


def make_document(tmp_path):
    path = tmp_path / "guide.txt"
    path.write_text("退款规则。" * 100, encoding="utf-8")
    return Document(
        id=str(uuid4()), user_id=str(uuid4()), original_name="guide.txt", storage_path=str(path),
        media_type="text/plain", size_bytes=path.stat().st_size, content_sha256="a" * 64, status="pending",
    )


def test_document_processor_transitions_pending_to_processing_to_ready(tmp_path):
    document = make_document(tmp_path)
    db = FakeDB(document)

    result = DocumentTaskProcessor(db, parser=FakeParser(), indexer=FakeIndexer()).process(document.id)

    assert isinstance(result, DocumentTaskResult)
    assert result.status == "ready"
    assert document.status == "ready"
    assert document.chunk_count > 0
    assert document.processed_at is not None


def test_document_processor_cleans_vectors_and_marks_failed(tmp_path):
    document = make_document(tmp_path)
    db = FakeDB(document)
    indexer = FakeIndexer(fail=True)

    result = DocumentTaskProcessor(db, parser=FakeParser(), indexer=indexer).process(document.id)

    assert result.status == "failed"
    assert document.status == "failed"
    assert document.error_code == "INDEXING_FAILED"
    assert indexer.deleted == [document.id]

