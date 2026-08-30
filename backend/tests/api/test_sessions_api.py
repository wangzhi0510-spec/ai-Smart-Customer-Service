from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.db.session import get_session
from backend.app.models.message import Message
from backend.app.main import create_app
from backend.app.services.session_service import SessionService

def register(client, identifier):
    response=client.post("/api/v1/auth/register",json={"identifier":identifier,"password":"StrongPass123!"})
    assert response.status_code == 201
    body=response.json()
    return body["access_token"], body["user"]["id"]

def auth(token): return {"Authorization":f"Bearer {token}"}

def test_sessions_are_isolated_and_delete_is_idempotent():
    client=TestClient(create_app())
    token_a,_=register(client,f"{uuid4().hex[:8]}@example.com")
    token_b,_=register(client,f"{uuid4().hex[:8]}@example.com")
    created=client.post("/api/v1/sessions",headers=auth(token_a),json={"title":"订单咨询"})
    assert created.status_code == 201
    session_id=created.json()["id"]
    assert client.get("/api/v1/sessions",headers=auth(token_a)).json()[0]["id"] == session_id
    assert client.get("/api/v1/sessions",headers=auth(token_b)).json() == []
    second=client.post("/api/v1/sessions",headers=auth(token_a),json={"title":"第二个"})
    assert second.status_code == 201
    assert len(client.get("/api/v1/sessions?page=1&page_size=1",headers=auth(token_a)).json()) == 1
    assert client.get(f"/api/v1/sessions/{session_id}",headers=auth(token_b)).status_code == 404
    assert client.delete(f"/api/v1/sessions/{session_id}",headers=auth(token_a)).status_code == 204
    assert client.delete(f"/api/v1/sessions/{session_id}",headers=auth(token_a)).status_code == 204
    assert client.get(f"/api/v1/sessions/{session_id}",headers=auth(token_a)).status_code == 404

def test_history_and_feedback_are_owner_scoped_and_feedback_updates():
    client=TestClient(create_app())
    token_a,_=register(client,f"{uuid4().hex[:8]}@example.com")
    token_b,_=register(client,f"{uuid4().hex[:8]}@example.com")
    session_id=client.post("/api/v1/sessions",headers=auth(token_a),json={}).json()["id"]
    message_id=str(uuid4())
    with next(get_session()) as db:
        db.add(Message(id=message_id,session_id=session_id,role="assistant",content="已处理",answer_type="fqa",status="completed"))
        db.commit()
    history=client.get(f"/api/v1/sessions/{session_id}/messages",headers=auth(token_a))
    assert history.status_code == 200
    assert history.json()[0]["id"] == message_id
    assert client.get(f"/api/v1/sessions/{session_id}/messages",headers=auth(token_b)).status_code == 404
    assert client.put(f"/api/v1/messages/{message_id}/feedback",headers=auth(token_b),json={"rating":"positive"}).status_code == 404
    first=client.put(f"/api/v1/messages/{message_id}/feedback",headers=auth(token_a),json={"rating":"positive","comment":"有帮助"})
    assert first.status_code == 200
    feedback_id=first.json()["id"]
    second=client.put(f"/api/v1/messages/{message_id}/feedback",headers=auth(token_a),json={"rating":"negative"})
    assert second.status_code == 200
    assert second.json()["id"] == feedback_id
    assert second.json()["rating"] == "negative"
