from fastapi.testclient import TestClient

from backend.app.core.errors import AppError, error_envelope
from backend.app.main import create_app


def test_error_envelope_has_stable_shape() -> None:
    error = AppError(code="VALIDATION_ERROR", message="参数无效", status_code=422)

    assert error_envelope(error, "req-123") == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "参数无效",
            "details": {},
            "request_id": "req-123",
        }
    }


def test_http_error_contains_request_id_and_shared_error_code() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/does-not-exist", headers={"X-Request-ID": "req-456"})

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "req-456"
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["request_id"] == "req-456"

