"""The deployed V1 metrics contract and HTTP request correlation."""
from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_returns_observability_snapshot():
    client = TestClient(app)

    response = client.get("/v1/metrics")

    assert response.status_code == 200

    data = response.json()["metrics"]

    assert "uptime_seconds" in data
    assert "requests_total" in data
    assert "latency" in data


def test_request_generates_metrics_counter():
    client = TestClient(app)

    before = client.get("/v1/metrics").json()["metrics"]["requests_total"]

    response = client.get("/health")

    assert response.status_code == 200

    after = client.get("/v1/metrics").json()["metrics"]["requests_total"]

    # The final metrics poll adds one request; /health must add the other.
    assert after == before + 2


def test_metrics_endpoint_has_request_id():
    client = TestClient(app)

    response = client.get("/v1/metrics")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id
    assert request_id.startswith("req_")
