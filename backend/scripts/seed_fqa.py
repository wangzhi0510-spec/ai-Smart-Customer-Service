from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_engine
from backend.app.models.fqa import FQAEntry


def seed_entries(db: Session, entries: list[dict[str, Any]]) -> int:
    """Insert or update active FQA entries by normalized question text."""
    changed = 0
    for item in entries:
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if not question or not answer:
            raise ValueError("每条 FQA 必须包含非空 question 和 answer")
        existing = db.scalar(select(FQAEntry).where(FQAEntry.question == question, FQAEntry.user_id == item.get("user_id")))
        if existing is None:
            existing = FQAEntry(
                id=str(uuid4()),
                question=question,
                answer=answer,
                user_id=item.get("user_id"),
                similarity_threshold=float(item.get("similarity_threshold", 0.92)),
                is_active=bool(item.get("is_active", True)),
            )
            db.add(existing)
        else:
            existing.answer = answer
            existing.similarity_threshold = float(item.get("similarity_threshold", existing.similarity_threshold))
            existing.is_active = bool(item.get("is_active", existing.is_active))
        changed += 1
    db.commit()
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="从 JSON 数组导入 FQA 条目")
    parser.add_argument("path", type=Path, help="JSON 文件路径")
    args = parser.parse_args()
    payload = json.loads(args.path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("FQA JSON 须为数组")
    with Session(get_engine()) as db:
        print(f"seeded {seed_entries(db, payload)} FQA entries")


if __name__ == "__main__":
    main()

