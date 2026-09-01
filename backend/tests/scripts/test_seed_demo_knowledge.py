from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.db.base import Base
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.scripts.seed_demo_knowledge import seed_demo_knowledge

ROOT = Path(__file__).parents[3]
KNOWLEDGE_DIR = ROOT / "examples" / "knowledge_base"
EXPECTED_FILES = {"公司产品介绍.txt", "常见问题FAQ.md", "退换货政策.txt"}


def test_demo_knowledge_documents_match_delivery_size():
    files = {path.name for path in KNOWLEDGE_DIR.iterdir() if path.is_file()}
    assert files == EXPECTED_FILES
    total = sum(len(path.read_text(encoding="utf-8")) for path in KNOWLEDGE_DIR.iterdir())
    assert 2000 <= total <= 5000


def test_seed_demo_knowledge_is_idempotent():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    queued: list[str] = []
    settings = Settings(
        APP_ENV="production",
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        DOCUMENT_STORAGE_PATH=str(ROOT / ".pytest_seed_documents"),
        DEMO_USER_IDENTIFIER="demo@example.com",
        DEMO_USER_PASSWORD="DemoPassword123!",
    )

    with Session(engine) as db:
        first = seed_demo_knowledge(db, settings, KNOWLEDGE_DIR, queued.append)
        second = seed_demo_knowledge(db, settings, KNOWLEDGE_DIR, queued.append)
        assert first.created_documents == 3
        assert second.created_documents == 0
        assert second.reused_documents == 3
        assert len(queued) == 3
        assert len(db.scalars(select(User)).all()) == 1
        assert len(db.scalars(select(Document)).all()) == 3