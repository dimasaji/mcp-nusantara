from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_phase4_v1_chat_exposes_trust_assessment():
    client = TestClient(app)

    response = client.post(
        "/v1/chat",
        json={
            "session_id": "phase4-trust-test",
            "user_input": "Apa itu KTP-el?",
            "stream": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "trust" in data

    trust = data["trust"]

    assert "supports_claim" in trust
    assert "confidence" in trust
    assert "risk_level" in trust
    assert "requires_human" in trust


def test_phase4_v1_chat_trust_confidence_is_bounded():
    client = TestClient(app)

    response = client.post(
        "/v1/chat",
        json={
            "session_id": "phase4-trust-bound",
            "user_input": "Apa itu KTP-el?",
            "stream": False,
        },
    )

    assert response.status_code == 200

    trust = response.json()["trust"]

    assert 0.0 <= trust["confidence"] <= 1.0
    assert trust["risk_level"] in {
        "low",
        "medium",
        "high",
        "critical",
    }
    assert isinstance(trust["requires_human"], bool)
