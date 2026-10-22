"""Outbound privacy tests with synthetic internal state; no model/DB mutation."""
from copy import deepcopy
from types import SimpleNamespace
import json

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app.api import routes
from app.main import app
from app.trust.schemas import RiskLevel, TrustAssessment


PRIVATE = "INTERNAL_SENTINEL_7219"
ROOT_KEYS = {
    "session_id", "response", "trust", "model", "provider_status", "latency_ms",
    "grounding", "understanding", "problem", "evidence", "timestamp",
}
TRUST_KEYS = {
    "supports_claim", "confidence", "risk_level", "requires_human",
    "evidence_count", "evidence_available",
}


def internal_context():
    state = {
        "reasoning": {"facts": [PRIVATE], "inferences": [PRIVATE], "explanation": PRIVATE},
        "policy": {"decision": PRIVATE, "reason": PRIVATE},
        "memory": [{"content": PRIVATE, "metadata": {"unrecognized": PRIVATE}}],
    }
    return {**deepcopy(state), "orchestration": {"data": deepcopy(state)},
            "future_safe_looking_field": {"nested": PRIVATE}}


def sample_payload():
    return {
        "session_id": "current-request", "response": "Public answer.",
        "trust": {"supports_claim": True, "confidence": .8, "risk_level": "low",
                  "requires_human": False, "evidence_count": 1, "evidence_available": True,
                  "issues": [PRIVATE], "details": {"future": PRIVATE}},
        "model": "fixture-model", "provider_status": "ollama", "latency_ms": 12,
        "grounding": {"enabled": True, "grounded": True, "reason": "grounded",
                      "unsupported_sentences": [PRIVATE], "future": PRIVATE},
        "understanding": {"input": PRIVATE, "output": {"entities": [PRIVATE]}},
        "problem": {"goal": "Public goal.", "metadata": {"future": PRIVATE}},
        "evidence": [{"document_id": "PUBLIC-1", "title": "Public citation",
                      "chunk": "Public citation.", "score": .9,
                      "source": PRIVATE, "metadata": {"future": PRIVATE}}],
        "timestamp": "2026-10-06T00:00:00+00:00",
        "gate_pipeline": internal_context(),
        "developer_core": {"orchestration": internal_context()["orchestration"],
                           "observability": {"policy_decision": PRIVATE},
                           "gates": {"9": {"allowed": PRIVATE}}},
        "unknown_public_looking_metadata": {"unknown": PRIVATE},
    }


def assert_public(data):
    assert set(data) == ROOT_KEYS
    assert set(data["trust"]) == TRUST_KEYS
    assert set(data["grounding"]) == {"enabled", "grounded", "reason"}
    assert set(data["understanding"]) == {"intent"}
    assert set(data["problem"]) == {"goal"}
    for item in data["evidence"]:
        assert set(item) == {"document_id", "title", "chunk", "score"}
    assert PRIVATE not in json.dumps(data)


@pytest.mark.parametrize("context", [None, {}, {"policy": None, "memory": PRIVATE}, internal_context()])
def test_projection_excludes_internal_mirrors_unknown_fields_and_never_mutates(context):
    payload = sample_payload()
    payload["gate_pipeline"] = context
    before = deepcopy(payload)
    projected = routes._project_v1_chat_response(payload, intent_name="ask_general_info")
    assert_public(projected)
    assert projected["response"] == "Public answer."
    assert projected["evidence"][0]["chunk"] == ""
    assert projected["trust"]["confidence"] == payload["trust"]["confidence"]
    assert payload == before


def test_unknown_grounding_reason_and_non_scalar_goal_fail_closed_without_stringifying():
    payload = sample_payload()
    payload["grounding"]["reason"] = {"internal": PRIVATE}
    payload["problem"]["goal"] = {"description": PRIVATE}
    projected = routes._project_v1_chat_response(payload, intent_name="unknown")
    assert_public(projected)
    assert projected["problem"]["goal"] is None
    assert projected["grounding"]["reason"] == "not_evaluated"


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), -.1, 1.1, "0.8"])
def test_malformed_public_assessment_is_not_silently_coerced(bad_value):
    payload = sample_payload()
    payload["trust"]["confidence"] = bad_value
    with pytest.raises(ValidationError):
        routes._project_v1_chat_response(payload, intent_name="unknown")


def test_oversized_citation_is_removed_without_mutating_source():
    payload = sample_payload()
    payload["evidence"][0]["chunk"] = "x" * 20001
    projected = routes._project_v1_chat_response(payload, intent_name="unknown")
    assert projected["evidence"][0]["chunk"] == ""
    assert payload["evidence"][0]["chunk"] == "x" * 20001


@pytest.fixture
def controlled_pipeline(monkeypatch, tmp_path):
    monkeypatch.setenv("NUSANTARA_ADMIN_TOKEN", "projection-fixture")
    from app.memory.engine import MemoryEngine
    from app.core.nusantara_config import load_nusantara_config
    configuration = load_nusantara_config(overrides={'llm': {'provider': 'ollama'}})
    monkeypatch.setattr(type(routes.settings), 'configuration_snapshot', lambda self: (configuration, 0))
    state = {"available": True, "reject": False, "empty": False,
             "human": False, "fast": False, "error": None, "generated": 0,
             "closed": 0, "remembered": 0, "context": internal_context()}

    class Provider:
        def __init__(self, **kwargs):
            self.model = "fixture-model"
            self.name = 'ollama'

        async def health_check(self):
            if state["error"]:
                raise state["error"]
            return {"available": state["available"]}

        async def generate(self, request):
            state["generated"] += 1
            return {"content": PRIVATE if state["reject"] else "Public answer."}

        async def close(self):
            state["closed"] += 1

    def language(user_input):
        return {"output": {"intent": {"intent": "ask_document_status" if state["fast"]
                                      else "ask_general_info", "confidence": .95},
                           "entities": []}, "input": PRIVATE, "metadata": PRIVATE}

    citation = SimpleNamespace(document_id="PUBLIC-1", title="Public citation",
                               chunk="Public citation.", source=PRIVATE, score=.9)

    def trust(**kwargs):
        count = len(kwargs["evidence"])
        assessment = TrustAssessment(
            supports_claim=bool(count), confidence=.8 if count else 0.,
            risk_level=RiskLevel.HIGH if state["human"] or not count else RiskLevel.LOW,
            requires_human=state["human"] or not count, evidence_count=count,
            evidence_available=bool(count), issues=[PRIVATE], details={"internal": PRIVATE},
        )
        state["assessment"] = assessment
        return assessment

    def remember(**kwargs):
        state["remembered"] += 1

    monkeypatch.setattr(routes, "OllamaProvider", Provider)
    class FixtureHermes(routes.HermesAgent):
        def __init__(self, **kwargs):
            from app.reasoning.engine import ReasoningEngine
            self.provider = kwargs['provider']
            self.language = SimpleNamespace(process=language)
            self.problem = SimpleNamespace(analyze=lambda **kw: {"goal": "Public goal.", "metadata": PRIVATE})
            self.reasoning = ReasoningEngine()
    monkeypatch.setattr(routes, "HermesAgent", FixtureHermes)
    monkeypatch.setattr(routes, "_knowledge", SimpleNamespace(
        search_knowledge=lambda *args, **kwargs: [] if state["empty"] else [citation],
        scan_knowledge_watch=lambda: None,
    ))
    monkeypatch.setattr(routes, "_trust_engine", SimpleNamespace(evaluate=trust))
    monkeypatch.setattr(routes, "_gate_integration", SimpleNamespace(
        process=lambda **kwargs: deepcopy(state["context"]), remember_response=remember,
        memory=MemoryEngine(storage_root=tmp_path / 'chat-history'),
    ))
    monkeypatch.setattr(routes, "_developer_core", SimpleNamespace(runtime_snapshot=lambda **kwargs: {
        "orchestration": internal_context()["orchestration"],
        "observability": {"policy_decision": PRIVATE}, "request": {"internal": PRIVATE},
    }))
    monkeypatch.setattr(routes, "_grounding_guard", SimpleNamespace(
        build_system_instruction=lambda: "Use approved evidence.",
        validate=lambda **kwargs: SimpleNamespace(
            grounded=not state["reject"] and not state["empty"],
            reason="no_evidence" if state["empty"] else
                   "possible_unsupported_content" if state["reject"] else "grounded",
            unsupported_sentences=[PRIVATE],
        ),
    ))
    return state


@pytest.mark.parametrize("branch", ["local_rule", "fast", "ollama", "offline", "unsupported",
                                     "missing", "requires_human", "policy_sensitive"])
def test_http_branch_projection_preserves_public_behavior_and_excludes_internal_state(
    branch, controlled_pipeline, monkeypatch,
):
    state = controlled_pipeline
    state.update(available=branch != "offline", fast=branch == "fast",
                 reject=branch == "unsupported", empty=branch == "missing",
                 human=branch == "requires_human")
    # Current helper always returns None; cover dormant branch only with a test double.
    if branch == "local_rule":
        monkeypatch.setattr(routes, "_deterministic_response", lambda **kwargs: "Public answer.")
    before = deepcopy(state["context"])
    with TestClient(app) as client:
        response = client.post("/v1/chat", json={"session_id": "current-request",
            "user_input": "Hapus record" if branch == "policy_sensitive" else "Apa status permohonan saya?"},
            headers={"X-Admin-Token": "projection-fixture"})
    if branch == 'offline':
        assert response.status_code == 503
        assert response.headers['X-Chat-Retry-Safe'] == 'pre-provider'
        assert state['generated'] == state['remembered'] == 0
        return
    assert response.status_code == 200
    data = response.json()
    assert_public(data)
    assert response.headers["X-Request-ID"]
    assert data["session_id"] == "current-request"
    assert state["closed"] == state["remembered"] == 1
    assert state["context"] == before
    assessment = state["assessment"]
    assert data["trust"] == {
        "supports_claim": assessment.supports_claim, "confidence": assessment.confidence,
        "risk_level": assessment.risk_level.value, "requires_human": assessment.requires_human,
        "evidence_count": assessment.evidence_count, "evidence_available": assessment.evidence_available,
    }
    if branch in {"unsupported", "missing"}:
        assert data["response"] == "Informasi tersebut belum tersedia secara cukup dalam knowledge base."
        assert not data["grounding"]["grounded"]
    elif branch == "offline":
        assert data["provider_status"] == "offline" and state["generated"] == 0
    elif branch == "fast":
        assert data["response"] == "Public citation."
        assert data["provider_status"] == "evidence_fast_path" and state["generated"] == 0
    elif branch == "local_rule":
        assert data["response"] == "Public answer."
        assert data["provider_status"] == "local_rule"
        assert data["grounding"]["grounded"] is False
        assert data["grounding"]["reason"] == "not_evaluated"
    else:
        assert data["response"] == "Public answer."
    if branch == "requires_human":
        assert data["trust"]["requires_human"] is True


@pytest.mark.parametrize("context,status", [
    (None, 200), ({}, 200),
    ({"reasoning": None, "policy": {"internal": PRIVATE}}, 200),
])
def test_http_partial_context_never_becomes_a_public_dump(context, status, controlled_pipeline):
    # Route currently needs a dict for its internal snapshot access; absence is {}.
    controlled_pipeline["context"] = context or {}
    with TestClient(app) as client:
        response = client.post("/v1/chat", json={"user_input": "Public question?"})
    assert response.status_code == status
    if status == 200:
        assert_public(response.json())
    else:
        # Invalid internal reasoning already fails before projection. Preserve
        # that fail-closed behavior; it must expose only the sanitized error.
        assert response.json() == {"detail": "Terjadi kesalahan internal server"}
        assert PRIVATE not in response.text


def test_http_generic_exception_does_not_echo_internal_exception(controlled_pipeline):
    controlled_pipeline["error"] = RuntimeError(PRIVATE)
    with TestClient(app) as client:
        response = client.post("/v1/chat", json={"user_input": "Public question?"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Terjadi kesalahan internal server"}
    assert PRIVATE not in response.text
    assert controlled_pipeline["closed"] == 1


@pytest.mark.parametrize("status", [503, 504])
def test_http_stage_statuses_remain_safe(status, controlled_pipeline, monkeypatch):
    async def denied(*args, **kwargs):
        raise HTTPException(status, "layanan sedang sibuk" if status == 503 else "batas waktu terlampaui")
    monkeypatch.setattr(routes, "_run_sync_v1", denied)
    with TestClient(app) as client:
        response = client.post("/v1/chat", json={"user_input": "Public question?"})
    assert response.status_code == status
    assert set(response.json()) == {"detail"}
    assert PRIVATE not in response.text


def test_http_provider_unavailable_preserves_existing_shared_handler(controlled_pipeline):
    from app.exceptions import ProviderUnavailableError
    controlled_pipeline["error"] = ProviderUnavailableError("ollama")
    with TestClient(app) as client:
        response = client.post("/v1/chat", json={"user_input": "Public question?"})
    assert response.status_code == 503
    assert response.json()["details"] == {"provider": "ollama"}
    assert PRIVATE not in response.text
    assert "gate_pipeline" not in response.json()


def test_http_validation_stays_outside_chat_pipeline(controlled_pipeline):
    with TestClient(app) as client:
        response = client.post("/v1/chat", json={"user_input": ""})
    assert response.status_code == 422
    assert "detail" in response.json()
    assert PRIVATE not in response.text
    assert controlled_pipeline["closed"] == 0
