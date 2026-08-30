from pathlib import Path

import pytest

from backend.app.core.errors import AppError
from backend.app.rag.cleaner import clean_pages
from backend.app.rag.parsers.base import DocumentParser, ParsedPage


def test_text_parser_preserves_source_and_page(tmp_path):
    path = tmp_path / "guide.txt"
    path.write_text("退款规则\n订单满 100 元可退款。", encoding="utf-8")

    pages = DocumentParser().parse(path)

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert pages[0].source_name == "guide.txt"
    assert "退款规则" in pages[0].text


def test_markdown_parser_tracks_heading_and_cleaner_preserves_code():
    path = Path("manual.md")
    path.write_text("# 退款\n\n说明   内容\n\n## API\n\n```python\nprint('ok')\n```", encoding="utf-8")
    try:
        pages = DocumentParser().parse(path)
        cleaned = clean_pages(pages)
    finally:
        path.unlink(missing_ok=True)

    assert [page.section_title for page in pages] == ["退款", "API"]
    assert "说明 内容" in cleaned[0].text
    assert "print('ok')" in "\n".join(page.text for page in cleaned)


def test_scanned_pdf_returns_explicit_ocr_unsupported_error(tmp_path):
    path = tmp_path / "scan.pdf"
    path.write_bytes(b"%PDF-scan")

    with pytest.raises(AppError) as error:
        DocumentParser().parse(path)

    assert error.value.code in {"OCR_UNSUPPORTED", "PDF_PARSER_UNAVAILABLE"}


def test_cleaner_drops_blank_pages_but_keeps_metadata():
    pages = [ParsedPage(text="  标题\n\n正文  ", page_number=3, source_name="x.txt", section_title="标题"), ParsedPage(text="  ", page_number=4, source_name="x.txt")]

    cleaned = clean_pages(pages)

    assert len(cleaned) == 1
    assert cleaned[0].page_number == 3
    assert cleaned[0].section_title == "标题"
    assert cleaned[0].text == "标题\n正文"
