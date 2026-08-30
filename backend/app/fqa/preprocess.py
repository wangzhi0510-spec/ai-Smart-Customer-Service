from __future__ import annotations

import re

try:
    import jieba
except ImportError:  # pragma: no cover - exercised only in minimal installations
    jieba = None


def normalize_question(text: str) -> str:
    """Normalize only formatting; preserve words for exact-match cache keys."""
    return re.sub(r"\s+", " ", text.strip().lower())


def tokenize(text: str) -> list[str]:
    normalized = normalize_question(text)
    if not normalized:
        return []
    if jieba is not None:
        return [token for token in jieba.lcut(normalized) if token.strip()]
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", normalized)

