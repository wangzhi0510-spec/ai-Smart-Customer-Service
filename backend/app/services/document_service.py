from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.adapters.document_storage import DocumentStorage, StoredFile
from backend.app.adapters.milvus_client import MilvusClient
from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.models.document import Document


class DocumentService:
    ALLOWED_MEDIA_TYPES = {
        ".txt": {"text/plain"},
        ".md": {"text/markdown", "text/plain"},
        ".pdf": {"application/pdf"},
    }

    def __init__(self, db: Session, settings: Settings | None = None, storage: DocumentStorage | None = None, enqueue_task: Callable[[str], object] | None = None, milvus: MilvusClient | None = None):
        self.db = db
        self.settings = settings or Settings.from_env()
        self.enqueue_task = enqueue_task or self._enqueue_task
        self.milvus = milvus or MilvusClient(
            host=self.settings.milvus_host,
            port=self.settings.milvus_port,
            collection_name=self.settings.milvus_collection,
        )
        self.storage = storage or DocumentStorage(
            self.settings.document_storage_path,
            self.settings.max_upload_size_mb * 1024 * 1024,
        )

    @classmethod
    def validate_upload(cls, filename: str | None, content_type: str | None) -> tuple[str, str]:
        suffix = Path(filename or "").suffix.lower()
        if suffix not in cls.ALLOWED_MEDIA_TYPES:
            raise AppError("UNSUPPORTED_FILE_TYPE", "仅支持 TXT、MD、PDF 文件", 415)
        media_type = (content_type or "").split(";", 1)[0].strip().lower()
        if media_type not in cls.ALLOWED_MEDIA_TYPES[suffix]:
            raise AppError("UNSUPPORTED_FILE_TYPE", "文件类型与扩展名不匹配", 415)
        return suffix, media_type

    def create(self, user_id: str, stream, filename: str, content_type: str) -> Document:
        _, media_type = self.validate_upload(filename, content_type)
        document_id = str(uuid4())
        stored: StoredFile | None = None
        try:
            stored = self.storage.save(stream, document_id, filename, user_id=user_id)
            duplicate = self.db.scalar(select(Document).where(
                Document.user_id == user_id,
                Document.content_sha256 == stored.sha256,
                Document.deleted_at.is_(None),
                Document.status != "deleted",
            ))
            if duplicate is not None:
                self.storage.delete(stored.storage_path)
                raise AppError("DUPLICATE_DOCUMENT", "相同内容的文档已存在", 409)
            item = Document(id=document_id, user_id=user_id, original_name=Path(filename).name,
                            storage_path=stored.storage_path, media_type=media_type,
                            size_bytes=stored.size_bytes, content_sha256=stored.sha256, status="pending")
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            if self.settings.app_env == "production":
                try:
                    self.enqueue_task(item.id)
                except Exception as exc:
                    self.db.rollback()
                    item.status = "failed"
                    item.error_code = "DOCUMENT_QUEUE_ERROR"
                    item.error_message = "文档处理任务暂时无法排队"
                    self.db.commit()
                    raise AppError("DOCUMENT_QUEUE_ERROR", "文档处理任务暂时无法排队", 503) from exc
            return item
        except AppError:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            if stored is not None:
                try:
                    self.storage.delete(stored.storage_path)
                except Exception:
                    pass
            raise AppError("DOCUMENT_CREATE_ERROR", "文档暂时无法创建", 503) from exc

    @staticmethod
    def _enqueue_task(document_id: str) -> object:
        from backend.app.workers.document_tasks import process_document_task
        return process_document_task.delay(document_id)

    def list(self, user_id: str) -> list[Document]:
        return list(self.db.scalars(select(Document).where(
            Document.user_id == user_id, Document.deleted_at.is_(None)
        ).order_by(Document.created_at.desc())).all())

    def get(self, user_id: str, document_id: str) -> Document:
        item = self.db.scalar(select(Document).where(
            Document.id == document_id, Document.user_id == user_id, Document.deleted_at.is_(None)
        ))
        if item is None:
            raise AppError("NOT_FOUND", "文档不存在", 404)
        return item

    def delete(self, user_id: str, document_id: str) -> None:
        item = self.db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user_id))
        if item is None or item.deleted_at is not None:
            return
        item.status = "deleting"
        self.db.commit()
        try:
            if item.chunk_count > 0 or item.status in {"ready", "processing", "failed"}:
                self.milvus.delete_by_document(item.id)
            self.storage.delete(item.storage_path)
            item.deleted_at = datetime.now(timezone.utc)
            item.status = "deleted"
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            raise AppError("DOCUMENT_DELETE_ERROR", "文档暂时无法删除", 503) from exc
