"""Live HTTP regression smoke tests for V1 runtime."""

import os
import requests


BASE_URL = os.getenv("NUSANTARA_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT = float(os.getenv("NUSANTARA_TEST_TIMEOUT", "60"))


def _post(path, payload):
    try:
        return requests.post(
            f"{BASE_URL}{path}",
            json=payload,
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
            "request_id": "req-live-1",
        },
    )
    assert r.status_code != 500, f"/v1/chat 500: {r.text[:1000]}"


def test_v1_live_problem_analyze_does_not_500():
    r = _post(
        "/v1/problem/analyze",
        {
            "user_input": "Bagaimana cara membuat KTP?",
            "session_id": "smoke-live",
            "request_id": "req-live-2",
        },
    )
    assert r.status_code != 500, f"/v1/problem/analyze 500: {r.text[:1000]}"


def test_v1_live_knowledge_search_does_not_500():
    r = _post(
        "/v1/knowledge/search",
        {
            "query": "Apa itu paspor?",
            "top_k": 3,
            "filter": {},
            "session_id": "smoke-live",
            "user_input": "Apa itu paspor?",
            "request_id": "req-live-3",
        },
    )
    assert r.status_code != 500, f"/v1/knowledge/search 500: {r.text[:1000]}"
