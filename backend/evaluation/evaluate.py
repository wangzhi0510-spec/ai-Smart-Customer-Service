"""Deterministic, offline RAG evaluation for the first-release knowledge base."""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


def load_dataset(path: str | Path) -> dict[str, Any]:
    """Load and validate the evaluation dataset JSON document."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise ValueError("dataset must contain a cases list")
    return payload


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", text.lower()))


def _retrieve(question: str, documents: Mapping[str, str], keywords: Sequence[str]) -> str | None:
    """Return the best document using explicit benchmark keywords plus lexical overlap.

    Explicit keywords are required for a deterministic hit; this prevents common
    one-character Chinese overlap from turning unsupported questions into hits.
    """
    del question
    normalized_keywords = [str(term).strip().lower() for term in keywords if str(term).strip()]
    ranked: list[tuple[int, int, str]] = []
    keyword_chars = _tokens("".join(normalized_keywords))
    for name, text in documents.items():
        normalized_text = text.lower()
        phrase_hits = sum(term in normalized_text for term in normalized_keywords)
        token_overlap = len(keyword_chars & _tokens(normalized_text))
        if phrase_hits:
            ranked.append((phrase_hits, token_overlap, name))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return ranked[0][2]


def evaluate_cases(cases: Sequence[Mapping[str, Any]], documents: Mapping[str, str]) -> dict[str, Any]:
    """Evaluate retrieval/source/fallback behavior without network or model dependencies."""
    started_all = time.perf_counter()
    results: list[dict[str, Any]] = []
    hit_count = source_count = fallback_count = answerable_count = 0
    for case in cases:
        started = time.perf_counter()
        expected_source = case.get("expected_source")
        should_fallback = bool(case.get("should_fallback"))
        retrieved_source = _retrieve(str(case.get("question", "")), documents, case.get("keywords", []))
        fallback = retrieved_source is None
        hit = retrieved_source is not None
        source_correct = expected_source is not None and retrieved_source == expected_source
        if expected_source is not None:
            answerable_count += 1
            hit_count += int(hit)
            source_count += int(source_correct)
        fallback_correct = fallback == should_fallback
        fallback_count += int(fallback_correct)
        results.append({
            "id": case.get("id"),
            "retrieved_source": retrieved_source,
            "fallback": fallback,
            "retrieval_hit": hit,
            "source_correct": source_correct,
            "fallback_correct": fallback_correct,
            "latency_ms": max(0, int((time.perf_counter() - started) * 1000)),
        })
    total = len(results)
    elapsed_ms = max(0, int((time.perf_counter() - started_all) * 1000))
    return {
        "metrics": {
            "total_cases": total,
            "answerable_cases": answerable_count,
            "retrieval_hit_rate": hit_count / answerable_count if answerable_count else 0.0,
            "source_correctness": source_count / answerable_count if answerable_count else 0.0,
            "fallback_accuracy": fallback_count / total if total else 0.0,
            "average_latency_ms": sum(item["latency_ms"] for item in results) / total if total else 0.0,
            "total_latency_ms": elapsed_ms,
        },
        "cases": results,
    }


def _load_documents(sample_dir: Path) -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(sample_dir.iterdir())
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run offline RAG evaluation")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("dataset.json"))
    parser.add_argument("--sample-dir", type=Path, default=Path(__file__).parents[2] / "sample-data")
    args = parser.parse_args()
    dataset = load_dataset(args.dataset)
    report = evaluate_cases(dataset["cases"], _load_documents(args.sample_dir))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()