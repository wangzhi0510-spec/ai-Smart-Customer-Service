from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.app.db.base import Base
from backend.app.services.auth_service import AuthService

def test_auth_service_registers_email_and_returns_no_password():
    engine=create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user=AuthService(db).register("person@example.com", "StrongPass123!")
        assert user.email == "person@example.com"
        assert user.password_hash != "StrongPass123!"
        assert user.password_hash.startswith("$argon2")

