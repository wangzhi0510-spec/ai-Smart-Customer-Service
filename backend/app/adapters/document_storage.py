from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from backend.app.core.errors import AppError


@dataclass(frozen=True)
class StoredFile:
    storage_path: str
    size_bytes: int
    sha256: str


class DocumentStorage:
    """Secure, streaming local storage for uploaded knowledge documents."""

    def __init__(self, root: str | Path, max_size_bytes: int):
        self.root = Path(root).resolve()
        self.max_size_bytes = max_size_bytes
        self.root.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        stream: BinaryIO,
        document_id: str,
        original_name: str,
        user_id: str | None = None,
    ) -> StoredFile:
        safe_name = self._safe_name(original_name)
        if not document_id or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", str(document_id)):
            raise AppError("VALIDATION_ERROR", "文档标识无效", 422)
        owner = self._safe_component(user_id) if user_id else None
        directory = self.root / owner / str(document_id) if owner else self.root / str(document_id)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / safe_name
        temp = directory / f".{safe_name}.{os.getpid()}.tmp"
        digest = hashlib.sha256()
        size = 0
        try:
            with temp.open("wb") as output:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > self.max_size_bytes:
                        raise AppError("FILE_TOO_LARGE", "文件大小超过限制", 413)
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            if size == 0:
                raise AppError("EMPTY_FILE", "文件不能为空", 422)
            os.replace(temp, target)
            return StoredFile(str(target), size, digest.hexdigest())
        except AppError:
            temp.unlink(missing_ok=True)
            raise
        except OSError as exc:
            temp.unlink(missing_ok=True)
            raise AppError("STORAGE_ERROR", "文件暂时无法保存", 503) from exc

    def delete(self, storage_path: str) -> None:
        candidate = Path(storage_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise AppError("STORAGE_ERROR", "存储路径无效", 500) from exc
        try:
            candidate.unlink(missing_ok=True)
            parent = candidate.parent
            while parent != self.root and parent.exists():
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
        except OSError as exc:
            raise AppError("STORAGE_ERROR", "文件暂时无法删除", 503) from exc

    @staticmethod
    def _safe_name(original_name: str) -> str:
        name = Path(str(original_name or "")).name
        name = name.replace("\x00", "").strip()
        if not name or name in {".", ".."}:
            raise AppError("VALIDATION_ERROR", "文件名无效", 422)
        name = re.sub(r"[^\w.()\-\u4e00-\u9fff ]", "_", name, flags=re.UNICODE)
        return name[:255]

    @staticmethod
    def _safe_component(value: str) -> str:
        component = re.sub(r"[^A-Za-z0-9_-]", "_", str(value))
        if not component or component in {".", ".."}:
            raise AppError("VALIDATION_ERROR", "用户标识无效", 422)
        return component[:128]

