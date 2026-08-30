from __future__ import annotations

from pathlib import Path

from backend.app.core.errors import AppError
from .base import ParsedPage


class PdfParser:
    def parse(self, path: Path) -> list[ParsedPage]:
        try:
            import fitz
        except ImportError as exc:
            raise AppError("PDF_PARSER_UNAVAILABLE", "PDF 解析依赖未安装", 503) from exc

        try:
            document = fitz.open(path)
            pages = [
                ParsedPage(page.get_text("text"), index + 1, path.name)
                for index, page in enumerate(document)
            ]
            document.close()
        except Exception as exc:
            raise AppError("INVALID_DOCUMENT", "PDF 文件无法解析", 422) from exc
        if not pages or not any(page.text.strip() for page in pages):
            raise AppError("OCR_UNSUPPORTED", "扫描型 PDF 暂不支持 OCR", 422)
        return pages

