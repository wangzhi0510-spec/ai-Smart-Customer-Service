from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .parsers.base import ParsedPage


@dataclass(frozen=True)
class ChunkRecord:
    id: str
    parent_id: str
    text: str
    source_name: str
    page_number: int
    section_title: str | None
    order: int
    parent_order: int
    parent_text: str


class ParentChildChunker:
    def __init__(self, parent_size: int = 1200, child_size: int = 320, overlap: int = 64):
        if parent_size <= 0 or child_size <= 0 or overlap < 0 or overlap >= child_size:
            raise ValueError("invalid chunk sizes")
        self.parent_size = parent_size
        self.child_size = child_size
        self.overlap = overlap

    def split(self, pages: list[ParsedPage]) -> list[ChunkRecord]:
        records: list[ChunkRecord] = []
        order = 1
        parent_order = 1
        for page in pages:
            text = page.text.strip()
            if not text:
                continue
            for parent_text in self._windows(text, self.parent_size, min(self.overlap, self.parent_size // 4), min_size=1000, max_size=1500):
                parent_id = str(uuid4())
                for child_text in self._windows(parent_text, self.child_size, self.overlap, min_size=250, max_size=400):
                    records.append(
                        ChunkRecord(
                            id=str(uuid4()),
                            parent_id=parent_id,
                            text=child_text,
                            source_name=page.source_name,
                            page_number=page.page_number,
                            section_title=page.section_title,
                            order=order,
                            parent_order=parent_order,
                            parent_text=parent_text,
                        )
                    )
                    order += 1
                parent_order += 1
        return records

    @staticmethod
    def _windows(text: str, size: int, overlap: int, min_size: int | None = None, max_size: int | None = None) -> list[str]:
        upper = max_size or size
        lower = min_size or 1
        if len(text) <= upper:
            return [text]
        count = max(2, (len(text) - overlap + (size - overlap) - 1) // (size - overlap))
        while count > 2 and (len(text) + (count - 1) * overlap) // count < lower:
            count -= 1
        chunk_size = (len(text) + (count - 1) * overlap + count - 1) // count
        if chunk_size < lower:
            return [text]
        chunk_size = min(chunk_size, upper)
        last_start = len(text) - chunk_size
        starts = sorted(set(round(last_start * index / (count - 1)) for index in range(count)))
        return [text[start : start + chunk_size] for start in starts]

