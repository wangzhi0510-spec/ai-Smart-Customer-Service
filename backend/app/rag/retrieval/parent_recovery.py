from __future__ import annotations

from .contracts import ContextDocument, SearchHit


def recover_parents(hits: list[SearchHit]) -> list[ContextDocument]:
    grouped: dict[str, ContextDocument] = {}
    for hit in hits:
        item = grouped.get(hit.parent_id)
        if item is None:
            item = ContextDocument(
                parent_id=hit.parent_id, text=hit.child_text, source_name=hit.source_name,
                page_number=hit.page_number, section_title=hit.section_title, score=hit.score,
                document_id=hit.document_id, version=hit.version, child_ids=[hit.id],
            )
            grouped[hit.parent_id] = item
        elif hit.id not in item.child_ids:
            item.text += "\n" + hit.child_text
            item.child_ids.append(hit.id)
            item.score = max(item.score, hit.score)
    return list(grouped.values())
