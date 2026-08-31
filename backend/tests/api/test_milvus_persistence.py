import sys
import types
from uuid import uuid4

from backend.app.adapters.milvus_client import MilvusClient, VectorChunk


class FakeCollection:
    def __init__(self):
        self.indexes = []
        self.inserted = []
        self.upserted = []
        self.deleted_exprs = []
        self.query_rows = []

    def create_index(self, field_name, index_params):
        self.indexes.append(types.SimpleNamespace(field_name=field_name))

    def insert(self, rows):
        self.inserted.extend(rows)
        return types.SimpleNamespace(insert_count=len(rows))

    def query(self, expr, output_fields=None):
        return [dict(row) for row in self.query_rows]

    def upsert(self, rows):
        self.upserted.extend(rows)

    def delete(self, expr):
        self.deleted_exprs.append(expr)


def fake_module(collection):
    return types.SimpleNamespace(
        Collection=lambda name, schema=None: collection,
        CollectionSchema=lambda fields, description=None: (fields, description),
        DataType=types.SimpleNamespace(
            VARCHAR='varchar', INT64='int64', FLOAT_VECTOR='float_vector',
            SPARSE_FLOAT_VECTOR='sparse_float_vector', BOOL='bool',
        ),
        FieldSchema=lambda *args, **kwargs: (args, kwargs),
        connections=types.SimpleNamespace(connect=lambda **kwargs: None),
        utility=types.SimpleNamespace(has_collection=lambda name: True),
    )


def make_row():
    return VectorChunk(
        id='chunk-1', user_id=uuid4(), document_id=uuid4(), version=1,
        parent_id='parent-1', child_text='refund policy', parent_text='refund policy parent',
        source_name='policy.txt', page_number=1, section_title=None, chunk_order=0,
        dense=[0.1, 0.2], sparse={'refund': 1.0},
    )


def test_insert_persists_vectors_to_real_milvus_collection(monkeypatch):
    collection = FakeCollection()
    monkeypatch.setitem(sys.modules, 'pymilvus', fake_module(collection))
    row = make_row()

    assert MilvusClient(collection_name='customer_service_chunks').insert([row]) == 1
    assert len(collection.inserted) == 1
    assert collection.inserted[0]['id'] == 'chunk-1'


def test_activate_version_updates_real_milvus_rows(monkeypatch):
    collection = FakeCollection()
    document_id = uuid4()
    collection.query_rows = [{
        'id': 'chunk-1', 'user_id': 'user-1', 'document_id': str(document_id), 'version': 2,
        'parent_id': 'parent-1', 'child_text': 'text', 'parent_text': 'parent',
        'source_name': 'policy.txt', 'page_number': 1, 'section_title': '', 'chunk_order': 0,
        'dense': [0.1, 0.2], 'sparse': {'refund': 1.0}, 'active_version': False, 'created_at': 1,
    }]
    monkeypatch.setitem(sys.modules, 'pymilvus', fake_module(collection))

    MilvusClient(collection_name='customer_service_chunks').activate_version(document_id, 2)

    assert collection.upserted[0]['active_version'] is True
