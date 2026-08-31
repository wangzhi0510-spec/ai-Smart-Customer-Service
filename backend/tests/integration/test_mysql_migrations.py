from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_alembic_upgrade_creates_core_tables_in_clean_database(tmp_path, monkeypatch):
    database_path = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database_path}")

    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(config, "head")

    tables = set(inspect(create_engine(f"sqlite+pysqlite:///{database_path}")).get_table_names())
    assert {"users", "chat_sessions", "messages", "documents", "message_sources"}.issubset(tables)
