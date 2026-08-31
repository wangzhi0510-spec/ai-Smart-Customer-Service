from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.rag.retrieval.contracts import ContextDocument, RetrievalResult
from backend.app.services.qa_service import QAService


def auth(token):
    return {"Authorization": f"Bearer {token}"}


class FakeFQA:
    def query(self, question, user_id):
        return type("FQAResult", (), {"matched": False, "answer": None})()


class FakeRetrieval:
    def __init__(self, document_id):
        self.document_id = document_id

    def retrieve(self, question, user_id, source_filter=None):
        return RetrievalResult(
            contexts=[
                ContextDocument(
                    parent_id="refund-parent",
                    text="Refunds are available within 30 days.",
                    source_name="refund-policy.txt",
                    page_number=1,
                    section_title="Refunds",
                    score=0.9,
                    document_id=self.document_id,
                    version=1,
                )
            ]
        )


class FakeLLM:
    def complete(self, messages):
        assert any("Refunds are available within 30 days." in message.content for message in messages)
        return "Refunds are available within 30 days."


@pytest.mark.integration
def test_core_api_flow_covers_auth_upload_query_feedback_and_delete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = create_app()
    client = TestClient(app)

    identifier = f"{uuid4().hex[:8]}@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={"identifier": identifier, "password": "StrongPass123!"},
    )
    assert registered.status_code == 201
    token = registered.json()["access_token"]

    session = client.post("/api/v1/sessions", headers=auth(token), json={})
    assert session.status_code == 201
    session_id = session.json()["id"]

    uploaded = client.post(
        "/api/v1/documents",
        headers=auth(token),
        files={"file": ("refund-policy.txt", BytesIO(b"Refunds are available within 30 days."), "text/plain")},
    )
    assert uploaded.status_code == 202
    document_id = uploaded.json()["id"]
    app.state.qa_service = QAService(FakeFQA(), FakeRetrieval(document_id), FakeLLM())

    streamed = client.post(
        "/api/v1/query/stream",
        headers=auth(token),
        json={"session_id": session_id, "question": "What is the refund period?"},
    )
    assert streamed.status_code == 200
    assert "event: start" in streamed.text
    assert "event: delta" in streamed.text
    assert "event: source" in streamed.text
    assert "event: done" in streamed.text

    messages = client.get(f"/api/v1/sessions/{session_id}/messages", headers=auth(token))
    assert messages.status_code == 200
    assistant = next(item for item in messages.json() if item["role"] == "assistant")
    assert assistant["content"] == "Refunds are available within 30 days."

    feedback = client.put(
        f"/api/v1/messages/{assistant['id']}/feedback",
        headers=auth(token),
        json={"rating": "positive", "comment": "helpful"},
    )
    assert feedback.status_code == 200
    assert feedback.json()["rating"] == "positive"

    deleted = client.delete(f"/api/v1/documents/{document_id}", headers=auth(token))
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/documents/{document_id}", headers=auth(token)).status_code == 404
