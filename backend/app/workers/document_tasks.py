from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.core.errors import AppError
from backend.app.db.session import get_engine
from backend.app.models.document import Document
from backend.app.rag.chunker import ParentChildChunker
from backend.app.rag.cleaner import clean_pages
from backend.app.rag.parsers.base import DocumentParser
from backend.app.adapters.embedding import EmbeddingProvider
from backend.app.adapters.milvus_client import MilvusClient
from backend.app.rag.indexer import DocumentIndexer
from .celery_app import celery_app


@dataclass(frozen=True)
class DocumentTaskResult:
    document_id: str
    status: str
    chunk_count: int = 0
    error_code: str | None = None


class DocumentTaskProcessor:
    def __init__(self, db, parser=None, chunker=None, indexer=None):
        self.db = db
        self.parser = parser or DocumentParser()
        self.chunker = chunker or ParentChildChunker()
        self.indexer = indexer or DocumentIndexer(EmbeddingProvider(), MilvusClient())

    def process(self, document_id: str) -> DocumentTaskResult:
        document = self.db.get(Document, document_id)
        if document is None:
            raise AppError("NOT_FOUND", "文档不存在", 404)
        if document.status not in {"pending", "processing"}:
            return DocumentTaskResult(document.id, document.status, document.chunk_count, document.error_code)
        document.status = "processing"
        document.processing_started_at = datetime.now(timezone.utc)
        self.db.commit()
        try:
            pages = clean_pages(self.parser.parse(Path(document.storage_path)))
            chunks = self.chunker.split(pages)
            count = self.indexer.index(chunks, document.user_id, document.id, document.version)
            activate = getattr(self.indexer, "activate_version", None)
            if activate is not None:
                activate(document.id, document.version)
            document.status = "ready"
            document.chunk_count = count
            document.error_code = None
            document.error_message = None
            document.processed_at = datetime.now(timezone.utc)
            self.db.commit()
            return DocumentTaskResult(document.id, "ready", count)
        except AppError as exc:
            self._fail(document, exc.code, exc.message)
            raise
        except Exception as exc:
            try:
                self.indexer.delete_by_document(document.id)
            finally:
                self._fail(document, "INDEXING_FAILED", "文档入库失败")
            return DocumentTaskResult(document.id, "failed", 0, "INDEXING_FAILED")

    def _fail(self, document: Document, code: str, message: str) -> None:
        document.status = "failed"
        document.error_code = code
        document.error_message = message
        self.db.commit()


def process_document(document_id: str, db=None, parser=None, chunker=None, indexer=None) -> DocumentTaskResult:
    if db is None:
        from sqlalchemy.orm import Session

        with Session(get_engine()) as session:
            return DocumentTaskProcessor(session, parser, chunker, indexer).process(document_id)
    return DocumentTaskProcessor(db, parser, chunker, indexer).process(document_id)


@celery_app.task(bind=True, name="backend.app.workers.document_tasks.process_document", autoretry_for=(ConnectionError, TimeoutError), retry_backoff=True, max_retries=3)
def process_document_task(self, document_id: str):
    return process_document(document_id)

