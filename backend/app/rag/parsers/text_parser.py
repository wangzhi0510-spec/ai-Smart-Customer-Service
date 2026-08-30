from __future__ import annotations

from pathlib import Path

from backend.app.core.errors import AppError
from .base import ParsedPage


class TextParser:
    def parse(self, path: Path) -> list[ParsedPage]:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise AppError("INVALID_DOCUMENT_ENCODING", "TXT 文件必须使用 UTF-8 编码", 422) from exc
        return [ParsedPage(text=text, page_number=1, source_name=path.name)]

