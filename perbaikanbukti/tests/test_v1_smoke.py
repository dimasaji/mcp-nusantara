"""Regression smoke test for live /v1 endpoints.

Goal: catch HIGH-severity AttributeErrors / NamesErrors that the rest of the
test suite never exercises because it mocks the routes module. F-S2
(ProblemEngine.analyze missing) and F-S3 (KnowledgeSearchRequest attrs
missing + gate_context/model_status/latency_ms undefined) were discovered
this way.

This test runs against the real `app.api.routes` module via FastAPI
TestClient, so it loads the full module-level initialization (LanguageEngine
IndoBERT, etc). On machines where Ollama is offline, /v1/chat still proceeds
into HermesAgent and surfaces F-S2 AttributeError. /v1/knowledge/search is
also exercised to surface F-S3.

If the test passes without 500 errors, those routes are not regressed.
If a 500 is raised, the message should name a known or new root cause.
"""
from fastapi.testclient import TestClient


def _client():
    from app.main import app
    return TestClient(app)


def test_v1_chat_does_not_500():
    """F-S2 regression check: /v1/chat must not raise AttributeError."""
    with _client() as c:
        r = c.post(
            "/v1/chat",
            json={
                "session_id": "smoke",
                "user_input": "halo",
                "request_id": "req-smoke-1",
            },
        )
    assert r.status_code != 500, (
        f"/v1/chat 500 detected — likely F-S2 ProblemEngine.analyze missing. "
        f"Body: {r.text[:500]}"
    )


def test_v1_problem_analyze_does_not_500():
    """F-S2 regression check: /v1/problem/analyze must not raise AttributeError."""
    with _client() as c:
        r = c.post(
            "/v1/problem/analyze",
            json={
                "user_input": "Bagaimana cara membuat KTP?",
                "session_id": "smoke",
                "request_id": "req-smoke-2",
            },
        )
    assert r.status_code != 500, (
        f"/v1/problem/analyze 500 detected — likely F-S2. "
        f"Body: {r.text[:500]}"
    )


def test_v1_knowledge_search_does_not_500():
    """F-S3 regression check: /v1/knowledge/search must not raise NameError."""
    with _client() as c:
        r = c.post(
            "/v1/knowledge/search",
            json={
                "query": "Apa itu paspor?",
                "top_k": 3,
                "filter": {},
                "session_id": "smoke",
                "user_input": "Apa itu paspor?",
                "request_id": "req-smoke-3",
            },
        )
    assert r.status_code != 500, (
        f"/v1/knowledge/search 500 detected — likely F-S3 "
        "(KnowledgeSearchRequest missing attrs / undefined gate_context). "
        f"Body: {r.text[:500]}"
    )