from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_request_id_header():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id
    assert request_id.startswith("req_")


def test_request_id_is_unique_per_request():
    client = TestClient(app)

    r1 = client.get("/health")
    r2 = client.get("/health")

    id1 = r1.headers.get("X-Request-ID")
    id2 = r2.headers.get("X-Request-ID")

    assert id1
    assert id2
    assert id1 != id2
