from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
import hashlib
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.adapters.document_storage import DocumentStorage
from backend.app.core.config import Settings
from backend.app.core.security import hash_password
from backend.app.db.session import get_engine
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.app.services.document_service import DocumentService

DEFAULT_FILES = ("公司产品介绍.txt", "常见问题FAQ.md", "退换货政策.txt")
MEDIA_TYPES = {".txt": "text/plain", ".md": "text/markdown"}


@dataclass(frozen=True)
class SeedResult:
    user_id: str
    created_documents: int
    reused_documents: int
    document_ids: tuple[str, ...]


def seed_demo_knowledge(
    db: Session,
    settings: Settings,
    knowledge_dir: Path,
    enqueue_task=None,
) -> SeedResult:
    identifier = getattr(settings, "demo_user_identifier", "")
    password = getattr(settings, "demo_user_password", "")
    if not identifier or not password:
        raise RuntimeError("DEMO_USER_IDENTIFIER and DEMO_USER_PASSWORD are required")
    email = identifier.strip().lower() if "@" in identifier else None
    phone = identifier.strip() if email is None else None
    user = db.scalar(select(User).where(User.email == email if email else User.phone == phone))
    if user is None:
        user = User(id=uuid4().hex, email=email, phone=phone, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)

    storage = DocumentStorage(settings.document_storage_path, settings.max_upload_size_mb * 1024 * 1024)
    service = DocumentService(db, settings=settings, storage=storage, enqueue_task=enqueue_task)
    created = 0
    reused = 0
    ids: list[str] = []
    for filename in DEFAULT_FILES:
        source = knowledge_dir / filename
        if not source.is_file():
            raise RuntimeError(f"missing demo document: {filename}")
        content = source.read_bytes()
        import hashlib

        digest = hashlib.sha256(content).hexdigest()
        existing = db.scalar(
            select(Document).where(
                Document.user_id == user.id,
                Document.original_name == filename,
                Document.content_sha256 == digest,
                Document.deleted_at.is_(None),
            )
        )
        if existing is not None:
            reused += 1
            ids.append(existing.id)
            continue
        item = service.create(user.id, BytesIO(content), filename, MEDIA_TYPES[source.suffix.lower()])
        created += 1
        ids.append(item.id)
    return SeedResult(user.id, created, reused, tuple(ids))


def wait_for_ready(db: Session, document_ids: tuple[str, ...], timeout_seconds: int = 600) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        db.expire_all()
        rows = [db.get(Document, document_id) for document_id in document_ids]
        failed = next((row for row in rows if row is not None and row.status == "failed"), None)
        if failed is not None:
            raise RuntimeError(f"demo document failed: {failed.error_code or 'INDEXING_FAILED'}")
        if rows and all(row is not None and row.status == "ready" for row in rows):
            return
        time.sleep(2)
    raise TimeoutError("timed out waiting for demo documents")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed demo knowledge documents idempotently")
    parser.add_argument("--knowledge-dir", type=Path, default=Path("/seed-data"))
    parser.add_argument("--wait-timeout", type=int, default=600)
    args = parser.parse_args()
    settings = Settings.from_env()
    with Session(get_engine(settings)) as db:
        result = seed_demo_knowledge(db, settings, args.knowledge_dir)
        wait_for_ready(db, result.document_ids, args.wait_timeout)
        print(f"demo seed ready: created={result.created_documents} reused={result.reused_documents}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())