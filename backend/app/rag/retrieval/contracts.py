from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class SearchHit:
    id: str
    score: float
    user_id: UUID | str
    document_id: UUID | str
    version: int
    parent_id: str
    child_text: str
    parent_text: str
    source_name: str
    page_number: int | None = None
    section_title: str | None = None
    active_version: bool = True
    chunk_order: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextDocument:
    parent_id: str
    text: str
    source_name: str
    page_number: int | None
    section_title: str | None
    score: float
    document_id: UUID | str | None = None
    version: int | None = None
    child_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RetrievalResult:
    contexts: list[ContextDocument]
    strategy: str = "hybrid_direct"
    warnings: list[str] = field(default_factory=list)

