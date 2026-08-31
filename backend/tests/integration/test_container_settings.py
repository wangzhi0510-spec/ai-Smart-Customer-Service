from pathlib import Path

import backend.app.db

from backend.app.core.config import Settings
from backend.app.services.document_service import DocumentService
from backend.app.workers.document_tasks import DocumentTaskProcessor


def test_container_settings_expose_worker_and_storage_endpoints(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://redis:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
    monkeypatch.setenv("DOCUMENT_STORAGE_PATH", str(tmp_path / "documents"))
    monkeypatch.setenv("MILVUS_COLLECTION", "customer_service_chunks")

    settings = Settings.from_env()

    assert settings.celery_broker_url == "redis://redis:6379/1"
    assert settings.celery_result_backend == "redis://redis:6379/2"
    assert settings.document_storage_path == str(tmp_path / "documents")
    assert settings.milvus_collection == "customer_service_chunks"


def test_document_service_uses_configured_storage_volume(tmp_path) -> None:
    settings = Settings(document_storage_path=str(tmp_path / "documents"))

    service = DocumentService(object(), settings=settings)

    assert service.storage.root == (tmp_path / "documents").resolve()


def test_worker_defaults_use_configured_model_and_milvus(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL_PATH", str(tmp_path / "bge-m3"))
    monkeypatch.setenv("MILVUS_HOST", "milvus")
    monkeypatch.setenv("MILVUS_PORT", "19530")
    monkeypatch.setenv("MILVUS_COLLECTION", "customer_service_chunks")

    processor = DocumentTaskProcessor(object())

    assert processor.indexer.embedding.model_path == str(tmp_path / "bge-m3")
    assert processor.indexer.milvus.host == "milvus"
    assert processor.indexer.milvus.port == 19530
    assert processor.indexer.milvus.collection_name == "customer_service_chunks"
