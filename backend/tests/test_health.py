from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_live_health_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

