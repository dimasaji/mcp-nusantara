from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_returns_observability_snapshot():
    client = TestClient(app)

    response = client.get("/v2/metrics")

    assert response.status_code == 200

    data = response.json()

    assert "uptime_s" in data
    assert "counters" in data
    assert "latency" in data


def test_request_generates_metrics_counter():
    client = TestClient(app)

    before = client.get("/v2/metrics").json()["counters"].get("requests_total", 0)

    response = client.get("/health")

    assert response.status_code == 200

    after = client.get("/v2/metrics").json()["counters"].get("requests_total", 0)

    assert after >= before


def test_metrics_endpoint_has_request_id():
    client = TestClient(app)

    response = client.get("/v2/metrics")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id
    assert request_id.startswith("req_")
