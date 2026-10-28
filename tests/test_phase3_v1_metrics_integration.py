from fastapi.testclient import TestClient

from app.main import app


def test_v1_metrics_counter_increases_after_request():
    client = TestClient(app)

    before = client.get("/v1/metrics").json()["metrics"]["requests_total"]

    response = client.get("/health")

    assert response.status_code == 200

    after = client.get("/v1/metrics").json()["metrics"]["requests_total"]

    assert after > before


def test_v1_metrics_latency_is_recorded():
    client = TestClient(app)

    before_data = client.get("/v1/metrics").json()["metrics"]
    before_latency = before_data.get("latency", {}).get("http_request", {}).get("count", 0)

    response = client.get("/health")

    assert response.status_code == 200

    after_data = client.get("/v1/metrics").json()["metrics"]
    after_latency = after_data.get("latency", {}).get("http_request", {}).get("count", 0)

    assert after_latency > before_latency


def test_v1_metrics_keeps_backward_compatible_fields():
    client = TestClient(app)

    response = client.get("/v1/metrics")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "metrics" in data
    assert "version" in data["metrics"]
    assert "uptime_seconds" in data["metrics"]
    assert "requests_total" in data["metrics"]
    assert "latency" in data["metrics"]
