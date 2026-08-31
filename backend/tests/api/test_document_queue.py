from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_upload_dispatches_document_processing_task(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', 'sqlite+pysqlite:///:memory:')
    app = create_app()
    client = TestClient(app)
    token = client.post(
        '/api/v1/auth/register',
        json={'identifier': f'{uuid4().hex[:8]}@example.com', 'password': 'StrongPass123!'},
    ).json()['access_token']

    sent = []
    monkeypatch.setattr('backend.app.workers.document_tasks.process_document_task.delay', lambda document_id: sent.append(document_id))

    response = client.post(
        '/api/v1/documents',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': ('guide.txt', b'hello', 'text/plain')},
    )

    assert response.status_code == 202
    assert sent == [response.json()['id']]



