import json
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.api.sse import serialize_event
from backend.app.main import create_app
from backend.app.services.qa_service import QAResult


def test_serialize_event_uses_sse_type_and_json_data():
    encoded = serialize_event("delta", {"text": "你好\n世界"})

    assert encoded.startswith("event: delta\n")
    assert json.loads(encoded.split("data: ", 1)[1].split("\n\n", 1)[0])["text"] == "你好\n世界"


def test_stream_emits_start_delta_source_done_in_order(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = create_app()

    class QA:
        def answer(self, question, session_id, user_id):
            return QAResult("完整答案", "rag", "hybrid_direct", [{"document_id": "d1", "document_name": "guide.txt", "page_number": 2, "section_title": "退款", "excerpt": "规则", "retrieval_score": .9}])

        async def stream(self, question, session_id, user_id):
            yield "第一段"
            yield "第二段"

    app.state.qa_service = QA()
    client = TestClient(app)
    token = client.post("/api/v1/auth/register", json={"identifier": f"{uuid4().hex[:8]}@example.com", "password": "StrongPass123!"}).json()["access_token"]
    session = client.post("/api/v1/sessions", headers={"Authorization": f"Bearer {token}"}, json={}).json()["id"]

    response = client.post("/api/v1/query/stream", headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"}, json={"session_id": session, "question": "退款"})
    events = [line for line in response.text.splitlines() if line.startswith("event:")]

    assert response.status_code == 200
    assert [line.split(": ", 1)[1] for line in events] == ["start", "delta", "delta", "source", "done"]
