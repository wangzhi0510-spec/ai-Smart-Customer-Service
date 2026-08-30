from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.core.errors import AppError


@dataclass(frozen=True)
class ParsedPage:
    text: str
    page_number: int
    source_name: str
    section_title: str | None = None


class DocumentParser:
    def parse(self, path: Path) -> list[ParsedPage]:
        suffix = path.suffix.lower()
        if suffix == ".txt":
            from .text_parser import TextParser

            return TextParser().parse(path)
        if suffix == ".md":
            from .markdown_parser import MarkdownParser

            return MarkdownParser().parse(path)
        if suffix == ".pdf":
            from .pdf_parser import PdfParser

            return PdfParser().parse(path)
        raise AppError("UNSUPPORTED_FILE_TYPE", "不支持的文档格式", 415)
