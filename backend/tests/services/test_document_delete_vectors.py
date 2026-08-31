import backend.app.db
from types import SimpleNamespace

from backend.app.core.config import Settings
from backend.app.services.document_service import DocumentService


class FakeDB:
    def __init__(self, document):
        self.document = document
        self.commits = 0

    def scalar(self, query):
        return self.document

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


class FakeStorage:
    def __init__(self):
        self.deleted = []

    def delete(self, path):
        self.deleted.append(path)


class FakeMilvus:
    def __init__(self):
        self.deleted = []

    def delete_by_document(self, document_id):
        self.deleted.append(document_id)


def test_delete_ready_document_removes_its_milvus_vectors(tmp_path):
    document = SimpleNamespace(
        id='doc-1', user_id='user-1', storage_path=str(tmp_path / 'doc-1' / 'guide.txt'),
        status='ready', chunk_count=3, deleted_at=None,
    )
    storage = FakeStorage()
    milvus = FakeMilvus()
    service = DocumentService(
        FakeDB(document),
        settings=Settings(document_storage_path=str(tmp_path)),
        storage=storage,
        milvus=milvus,
    )

    service.delete('user-1', 'doc-1')

    assert milvus.deleted == ['doc-1']
    assert storage.deleted == [document.storage_path]
    assert document.status == 'deleted'
    assert document.deleted_at is not None
