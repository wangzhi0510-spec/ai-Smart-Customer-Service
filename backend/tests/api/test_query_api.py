from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.qa_service import QAResult


def register(client, identifier):
    return client.post("/api/v1/auth/register", json={"identifier": identifier, "password": "StrongPass123!"}).json()["access_token"]


def test_query_requires_auth_and_validates_question_length():
    client = TestClient(create_app())
    assert client.post("/api/v1/query", json={"session_id": "x", "question": "hi"}).status_code == 401
    token = register(client, f"{uuid4().hex[:8]}@example.com")
    response = client.post("/api/v1/query", headers={"Authorization": f"Bearer {token}"}, json={"session_id": "x", "question": "a" * 501})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_query_returns_fake_qa_result_and_persists_contract(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = create_app()
    app.state.qa_service = type("QA", (), {"answer": lambda self, question, session_id, user_id: QAResult("标准答案", "fqa")})()
    client = TestClient(app)
    token = register(client, f"{uuid4().hex[:8]}@example.com")
    session = client.post("/api/v1/sessions", headers={"Authorization": f"Bearer {token}"}, json={}).json()["id"]

    response = client.post("/api/v1/query", headers={"Authorization": f"Bearer {token}"}, json={"session_id": session, "question": "退款"})

    assert response.status_code == 200
    assert response.json()["answer"] == "标准答案"
    assert response.json()["answer_type"] == "fqa"
