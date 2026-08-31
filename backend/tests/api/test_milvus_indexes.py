import sys
import types

from backend.app.adapters.milvus_client import MilvusClient


class FakeCollection:
    instances = []

    def __init__(self, name, schema=None):
        self.name = name
        self.schema = schema
        self.indexes = []
        self.index_calls = []
        FakeCollection.instances.append(self)

    def create_index(self, field_name, index_params):
        self.index_calls.append((field_name, index_params))


def test_ensure_collection_creates_dense_and_sparse_indexes(monkeypatch):
    FakeCollection.instances.clear()
    utility = types.SimpleNamespace(has_collection=lambda name: False)
    fake_pymilvus = types.SimpleNamespace(
        Collection=FakeCollection,
        CollectionSchema=lambda fields, description=None: (fields, description),
        DataType=types.SimpleNamespace(
            VARCHAR='varchar', INT64='int64', FLOAT_VECTOR='float_vector',
            SPARSE_FLOAT_VECTOR='sparse_float_vector', BOOL='bool',
        ),
        FieldSchema=lambda *args, **kwargs: (args, kwargs),
        connections=types.SimpleNamespace(connect=lambda **kwargs: None),
        utility=utility,
    )
    monkeypatch.setitem(sys.modules, 'pymilvus', fake_pymilvus)

    MilvusClient(collection_name='customer_service_chunks').ensure_collection()

    collection = FakeCollection.instances[-1]
    assert {field for field, _ in collection.index_calls} == {'dense', 'sparse'}
    params = dict(collection.index_calls)
    assert params['dense']['metric_type'] == 'COSINE'
    assert params['sparse']['metric_type'] == 'IP'


def test_ensure_collection_is_idempotent_for_existing_indexes(monkeypatch):
    FakeCollection.instances.clear()
    existing = types.SimpleNamespace(field_name='dense')
    collection = FakeCollection('customer_service_chunks')
    collection.indexes = [existing]
    utility = types.SimpleNamespace(has_collection=lambda name: True)
    fake_pymilvus = types.SimpleNamespace(
        Collection=lambda name: collection,
        CollectionSchema=None,
        DataType=None,
        FieldSchema=None,
        connections=types.SimpleNamespace(connect=lambda **kwargs: None),
        utility=utility,
    )
    monkeypatch.setitem(sys.modules, 'pymilvus', fake_pymilvus)

    MilvusClient(collection_name='customer_service_chunks').ensure_collection()

    assert [field for field, _ in collection.index_calls] == ['sparse']
