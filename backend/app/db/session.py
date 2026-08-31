from collections.abc import Iterator
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from backend.app.core.config import Settings
from backend.app.db.base import Base
_engine = None
_engine_url = None
def get_engine(settings: Settings | None = None):
    global _engine, _engine_url
    url=(settings or Settings.from_env()).database_url
    if _engine is None or _engine_url != url:
        if _engine is not None:
            _engine.dispose()
        kwargs = {"future": True}
        if url == "sqlite+pysqlite:///:memory:":
            kwargs.update(poolclass=StaticPool, connect_args={"check_same_thread": False})
        _engine=create_engine(url, **kwargs)
        _engine_url=url
    return _engine
def get_session() -> Iterator[Session]:
    with Session(get_engine()) as session: yield session
