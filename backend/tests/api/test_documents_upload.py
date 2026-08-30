from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import create_app


def register(client, identifier):
    response = client.post(
        "/api/v1/auth/register", json={"identifier": identifier, "password": "StrongPass123!"}
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_upload_creates_pending_document_and_enforces_owner_scope(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app())
    token_a = register(client, f"{uuid4().hex[:8]}@example.com")
    token_b = register(client, f"{uuid4().hex[:8]}@example.com")

    uploaded = client.post(
        "/api/v1/documents",
        headers=auth(token_a),
        files={"file": ("guide.txt", "退款规则".encode("utf-8"), "text/plain")},
    )

    assert uploaded.status_code == 202
    body = uploaded.json()
    assert body["status"] == "pending"
    assert body["original_name"] == "guide.txt"
    document_id = body["id"]
    assert client.get(f"/api/v1/documents/{document_id}", headers=auth(token_b)).status_code == 404
    assert len(client.get("/api/v1/documents", headers=auth(token_a)).json()) == 1
    assert client.delete(f"/api/v1/documents/{document_id}", headers=auth(token_a)).status_code == 204
    assert client.get(f"/api/v1/documents/{document_id}", headers=auth(token_a)).status_code == 404


def test_upload_rejects_unsupported_empty_and_oversized_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app())
    token = register(client, f"{uuid4().hex[:8]}@example.com")

    unsupported = client.post(
        "/api/v1/documents",
        headers=auth(token),
        files={"file": ("guide.exe", "退款规则".encode("utf-8"), "application/octet-stream")},
    )
    empty = client.post(
        "/api/v1/documents",
        headers=auth(token),
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert unsupported.status_code == 415
    assert unsupported.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert empty.status_code == 422
    assert empty.json()["error"]["code"] == "EMPTY_FILE"



