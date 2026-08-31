from __future__ import annotations

import json
from pathlib import Path

from backend.evaluation.evaluate import evaluate_cases, load_dataset


ROOT = Path(__file__).resolve().parents[3]


def test_dataset_has_required_fields_and_sample_documents_exist():
    dataset = load_dataset(ROOT / "backend/evaluation/dataset.json")
    assert dataset["version"]
    assert len(dataset["cases"]) >= 4
    required = {"id", "question", "expected_source", "should_fallback", "keywords"}
    assert all(required <= case.keys() for case in dataset["cases"])
    assert all((ROOT / "sample-data" / name).is_file() for name in {case["expected_source"] for case in dataset["cases"] if not case["should_fallback"]})


def test_evaluation_metrics_cover_hit_source_fallback_and_latency():
    docs = {
        "product.md": "专业版支持多用户协作，提供 30 天免费试用。",
        "refund.txt": "购买后七天内可以申请退款，退款原路返回。",
    }
    cases = [
        {"id": "hit", "question": "如何申请退款", "expected_source": "refund.txt", "should_fallback": False, "keywords": ["退款", "七天"]},
        {"id": "fallback", "question": "你会唱歌吗", "expected_source": None, "should_fallback": True, "keywords": ["唱歌"]},
    ]
    report = evaluate_cases(cases, docs)
    assert report["metrics"]["retrieval_hit_rate"] == 1.0
    assert report["metrics"]["source_correctness"] == 1.0
    assert report["metrics"]["fallback_accuracy"] == 1.0
    assert report["metrics"]["average_latency_ms"] >= 0
    assert report["cases"][0]["retrieved_source"] == "refund.txt"
    assert report["cases"][1]["fallback"] is True


def test_dataset_is_valid_json():
    json.loads((ROOT / "backend/evaluation/dataset.json").read_text(encoding="utf-8"))