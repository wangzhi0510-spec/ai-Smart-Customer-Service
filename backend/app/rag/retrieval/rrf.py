from __future__ import annotations

from collections import OrderedDict

from .contracts import SearchHit


def rrf_fuse(dense: list[SearchHit], sparse: list[SearchHit], k: int = 60) -> list[SearchHit]:
    scores: dict[str, float] = {}
    values: dict[str, SearchHit] = {}
    for results in (dense, sparse):
        for rank, hit in enumerate(results, start=1):
            scores[hit.id] = scores.get(hit.id, 0.0) + 1.0 / (k + rank)
            values.setdefault(hit.id, hit)
    fused = []
    for identifier, hit in values.items():
        fused.append(SearchHit(**{**hit.__dict__, "score": scores[identifier]}))
    return sorted(fused, key=lambda item: (-item.score, item.chunk_order, item.id))

