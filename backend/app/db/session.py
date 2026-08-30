from collections.abc import Iterator
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from backend.app.core.config import Settings
from backend.app.db.base import Base
_engine = None
def get_engine(settings: Settings | None = None):
    global _engine
    if _engine is None:
        url=(settings or Settings.from_env()).database_url
        if url.startswith("mysql+"): url="sqlite+pysqlite:///:memory:"
        _engine=create_engine(url, future=True, poolclass=StaticPool, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    return _engine
def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session: yield session
