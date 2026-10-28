"""Live HTTP regression smoke tests for V1 runtime."""

import os
import requests
import pytest


BASE_URL = os.getenv("NUSANTARA_BASE_URL", "http://127.0.0.1:8000")
pytestmark = pytest.mark.skipif(not os.getenv("NUSANTARA_BASE_URL"),
    reason="live HTTP tests require an explicitly selected runtime URL")
TIMEOUT = float(os.getenv("NUSANTARA_TEST_TIMEOUT", "60"))


def _post(path, payload):
    try:
        return requests.post(
            f"{BASE_URL}{path}",
            json=payload,
            headers={"X-Admin-Token": os.environ["NUSANTARA_TEST_ADMIN_TOKEN"]}
                if os.getenv("NUSANTARA_TEST_ADMIN_TOKEN") else {},
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise AssertionError(f"V1 API tidak dapat diakses: {BASE_URL}. Error: {exc}") from exc


def test_v1_live_chat_does_not_500():
    r = _post(
        "/v1/chat",
        {
            "session_id": "smoke-live",
            "user_input": "halo",
        },
    )
    assert r.status_code == 200, r.text[:1000]
    assert isinstance(r.json()["response"], str)


def test_v1_live_problem_analyze_does_not_500():
    r = _post(
        "/v1/problem/analyze",
        {
            "user_input": "Bagaimana cara membuat KTP?",
            "session_id": "smoke-live",
        },
    )
    assert r.status_code == 200, r.text[:1000]


def test_v1_live_knowledge_search_does_not_500():
    r = _post(
        "/v1/knowledge/search",
        {
            "query": "Apa itu paspor?",
            "top_k": 3,
            "filter": {},
            "session_id": "smoke-live",
            "user_input": "Apa itu paspor?",
        },
    )
    assert r.status_code == 200, r.text[:1000]
    assert isinstance(r.json()["results"], list)
