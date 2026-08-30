from backend.app.rag.chunker import ParentChildChunker
from backend.app.rag.parsers.base import ParsedPage


def test_parent_child_chunker_emits_bounded_chunks_and_source_metadata():
    text = "段落内容。" * 700
    pages = [ParsedPage(text=text, page_number=2, source_name="guide.txt", section_title="退款规则")]

    chunks = ParentChildChunker(parent_size=1200, child_size=320, overlap=64).split(pages)

    parents = {chunk.parent_id for chunk in chunks}
    assert len(parents) >= 2
    assert all(250 <= len(chunk.text) <= 400 for chunk in chunks)
    assert all(chunk.page_number == 2 for chunk in chunks)
    assert all(chunk.section_title == "退款规则" for chunk in chunks)
    assert [chunk.order for chunk in chunks] == list(range(1, len(chunks) + 1))
    first_parent = next(iter(parents))
    first = next(chunk for chunk in chunks if chunk.parent_id == first_parent)
    siblings = [chunk for chunk in chunks if chunk.parent_id == first_parent]
    assert len(siblings) >= 2
    assert first.parent_id
