import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from backend.app.main import create_app

def test_duplicate_identifier_returns_conflict():
    client=TestClient(create_app())
    payload={"identifier":"dup@example.com","password":"StrongPass123!"}
    assert client.post("/api/v1/auth/register",json=payload).status_code == 201
    response=client.post("/api/v1/auth/register",json=payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"

def test_weak_password_and_invalid_identifier_return_validation_error():
    client=TestClient(create_app())
    bad=client.post("/api/v1/auth/register",json={"identifier":"bad","password":"short"})
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "VALIDATION_ERROR"

def test_login_and_me_reject_tampered_or_expired_tokens():
    client=TestClient(create_app())
    payload={"identifier":"me@example.com","password":"StrongPass123!"}
    registered=client.post("/api/v1/auth/register",json=payload).json()
    logged=client.post("/api/v1/auth/login",json=payload)
    assert logged.status_code == 200
    wrong=client.post("/api/v1/auth/login",json={"identifier":"me@example.com","password":"WrongPass123!"})
    assert wrong.status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me",headers={"Authorization":f"Bearer {registered['access_token']}"}).json()["email"] == "me@example.com"
    assert client.get("/api/v1/auth/me",headers={"Authorization":"Bearer tampered"}).status_code == 401
    expired=jwt.encode({"sub":"missing","exp":datetime.now(timezone.utc)-timedelta(minutes=1)},"development-only-secret-key-32-bytes-long",algorithm="HS256")
    assert client.get("/api/v1/auth/me",headers={"Authorization":f"Bearer {expired}"}).status_code == 401



