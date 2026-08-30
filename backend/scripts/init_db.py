from pathlib import Path
from alembic import command
from alembic.config import Config
from backend.app.db.base import Base
import backend.app.db
from backend.app.db.session import get_engine

def init_db() -> None:
    engine=get_engine()
    Base.metadata.create_all(bind=engine)

def main() -> None:
    init_db()
if __name__ == "__main__": main()

