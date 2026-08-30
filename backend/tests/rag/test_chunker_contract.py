from backend.app.rag.chunker import ParentChildChunker
from backend.app.rag.parsers.base import ParsedPage


def test_chunk_record_exposes_parent_text_with_document_sized_parent():
    pages = [ParsedPage(text="知识内容。" * 700, page_number=1, source_name="guide.txt")]

    chunks = ParentChildChunker().split(pages)

    assert all(1000 <= len(chunk.parent_text) <= 1500 for chunk in chunks)
