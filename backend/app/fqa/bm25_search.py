from __future__ import annotations

import math
from collections import Counter
from typing import Any, Mapping

from backend.app.fqa.preprocess import tokenize


class BM25Search:
    def __init__(self, entries: list[Mapping[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.entries = list(entries)
        self.k1 = k1
        self.b = b
        self.documents = [tokenize(str(entry.get("question", ""))) for entry in self.entries]
        self.avgdl = sum(map(len, self.documents)) / len(self.documents) if self.documents else 0.0
        document_frequency = Counter(token for document in self.documents for token in set(document))
        count = len(self.documents)
        self.idf = {
            token: math.log(1 + (count - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequency.items()
        }

    def search(self, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_tokens = tokenize(question)
        if not query_tokens or not self.documents:
            return []
        results: list[dict[str, Any]] = []
        for entry, document in zip(self.entries, self.documents):
            frequencies = Counter(document)
            score = 0.0
            for token in query_tokens:
                if token not in frequencies:
                    continue
                length = len(document)
                denominator = frequencies[token] + self.k1 * (
                    1 - self.b + self.b * length / self.avgdl if self.avgdl else 1
                )
                score += self.idf.get(token, 0.0) * frequencies[token] * (self.k1 + 1) / denominator
            if score > 0:
                result = dict(entry)
                result["score"] = score / (score + 1.0)
                results.append(result)
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

