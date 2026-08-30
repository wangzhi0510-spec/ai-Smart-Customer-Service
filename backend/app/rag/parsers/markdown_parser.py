from __future__ import annotations

import re
from pathlib import Path

from backend.app.core.errors import AppError
from .base import ParsedPage


class MarkdownParser:
    _heading = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")

    def parse(self, path: Path) -> list[ParsedPage]:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise AppError("INVALID_DOCUMENT_ENCODING", "Markdown 文件必须使用 UTF-8 编码", 422) from exc

        pages: list[ParsedPage] = []
        section: str | None = None
        current: list[str] = []
        page_number = 1
        for line in lines:
            match = self._heading.match(line)
            if match and current:
                pages.append(ParsedPage("\n".join(current), page_number, path.name, section))
                page_number += 1
                current = []
            if match:
                section = match.group(1).strip()
            current.append(line)
        if current or not pages:
            pages.append(ParsedPage("\n".join(current), page_number, path.name, section))
        return pages

