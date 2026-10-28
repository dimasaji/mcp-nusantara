"""Offline cloud adapter contracts; keys are synthetic and transport is mocked."""
import asyncio
import ast
import json
from pathlib import Path

import httpx
import pytest

from app.core.nusantara_config import ConfigurationError, load_nusantara_config
from app.models.openrouter import OpenRouterError, OpenRouterProvider
from app.models.ollama import OllamaProvider
from app.models.router import ModelRouter


def config(**values):
    return load_nusantara_config(overrides={"llm": {"provider": "openrouter", **values}})


def result(**changes):
    return {"model": "reported/fixture", "choices": [{"message": {"content": "fixture answer"}}], **changes}


def invoke(handler, request=None, configuration=None):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = OpenRouterProvider(nusantara_config=configuration or config(),
                http_client=client, key_resolver=lambda: "synthetic-test-credential")
            return await adapter.generate(request or {"prompt": "offline fixture"})
    return asyncio.run(run())


def test_defaults_and_explicit_selection():
    local = load_nusantara_config()
    assert local.llm.provider == "ollama" and local.llm.model == "llama3.2:1b"
    assert not local.features.langgraph_workflow
    provider = OllamaProvider(nusantara_config=local)
    assert ModelRouter().register(provider).route().provider is provider
    cloud = config()
    assert cloud.llm.model == "openai/gpt-4o-mini"
    assert cloud.llm.base_url == "https://openrouter.ai/api/v1"
    assert cloud.llm.connection_timeout_s == 30.
    explicit = load_nusantara_config(environment={"LLM_PROVIDER": "openrouter",
        "LLM_MODEL": "approved/model", "LLM_TIMEOUT_SECONDS": "4.0", "LLM_MAX_TOKENS": "100"})
    assert explicit.llm.model == "approved/model" and explicit.llm.connection_timeout_s == 4.


@pytest.mark.parametrize("values", [{"base_url": "http://evil.invalid"},
    {"model": "invalid model"}, {"auth_env_ref": "OTHER_SECRET"}, {"connection_timeout_s": 0.}])
def test_configuration_rejects_unsafe_selection(values):
    with pytest.raises(ConfigurationError):
        config(**values)


def test_missing_key_is_lazy_and_never_sends():
    calls = []
    async def run():
        provider = OpenRouterProvider(nusantara_config=config(),
            key_resolver=lambda: calls.append("resolved") or None)
        assert calls == [] and provider._client is None
        with pytest.raises(OpenRouterError, match="KEY_UNAVAILABLE"):
            await provider.generate({"prompt": "fixture"})
        assert provider._client is None
        assert not (await provider.health_check())["available"]
    asyncio.run(run())
    assert len(calls) == 2


def test_success_usage_output_cap_and_distinct_identity():
    calls = []
    def respond(request):
        calls.append(json.loads(request.content))
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        return httpx.Response(200, json=result(usage={"prompt_tokens": 8, "completion_tokens": 3,
            "total_tokens": 11, "cost": .0002}))
    response = invoke(respond, {"prompt": "fixture", "max_tokens": 9999, "temperature": 0.})
    assert len(calls) == 1 and calls[0]["max_tokens"] == 512
    assert calls[0]["temperature"] == 0.
    assert response["model"] == response["requested_model"] == "openai/gpt-4o-mini"
    assert response["reported_model"] == "reported/fixture"
    assert response["execution_identity"]["identity_status"] == "MISMATCH"
    assert response["provider_status"] == "openrouter"
    assert response["tokens_used"] == 11 and response["usage"]["cost"] == .0002


@pytest.mark.parametrize("usage", [None, {}, {"total_tokens": "12", "cost": float("nan")},
                                       {"prompt_tokens": -1, "completion_tokens": True}])
def test_missing_or_invalid_usage_is_not_fabricated(usage):
    # NaN fixture bypasses HTTP JSON encoder to test defensive metadata parsing.
    response = invoke(lambda request: httpx.Response(200, content=json.dumps(result(usage=usage))))
    assert response["tokens_used"] is None and response["usage"]["cost"] is None
    assert response["usage"]["input_tokens"] is None


@pytest.mark.parametrize("data", [{}, {"error": {"message": "synthetic-private-body"}},
    result(choices=[]), result(choices=[{"message": {"content": " "}}]),
    result(choices=[{"message": {"content": []}}]), result(model={"bad": "value"})])
def test_invalid_response_fails_closed(data):
    with pytest.raises(OpenRouterError, match="INVALID_RESPONSE"):
        invoke(lambda request: httpx.Response(200, json=data))


@pytest.mark.parametrize("status", [302, 401, 429, 500])
def test_http_errors_do_not_retry_follow_redirect_or_expose_body(status, caplog):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(status, text="synthetic-test-credential", headers={"Location": "https://evil.invalid"})
    with pytest.raises(OpenRouterError) as failure:
        invoke(respond)
    assert str(failure.value) == "OpenRouter: HTTP_" + str(status)
    assert len(calls) == 1
    assert "synthetic-test-credential" not in caplog.text


def test_transport_timeout_sanitized_without_retry(caplog):
    calls = []
    def fail(request):
        calls.append(1)
        raise httpx.ReadTimeout("synthetic-test-credential", request=request)
    with pytest.raises(OpenRouterError, match="TIMEOUT") as failure:
        invoke(fail)
    assert len(calls) == 1 and "synthetic-test-credential" not in str(failure.value) + caplog.text


def test_total_deadline_and_cancellation_do_not_replay():
    calls = []
    async def stall(request):
        calls.append(1)
        await asyncio.sleep(60)
    with pytest.raises(OpenRouterError, match="TIMEOUT"):
        invoke(stall, configuration=config(connection_timeout_s=.01))
    async def cancel():
        async with httpx.AsyncClient(transport=httpx.MockTransport(stall)) as client:
            adapter = OpenRouterProvider(nusantara_config=config(), http_client=client,
                                         key_resolver=lambda: "synthetic")
            task = asyncio.create_task(adapter.generate({"prompt": "fixture"}))
            await asyncio.sleep(.01)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
    asyncio.run(cancel())
    assert len(calls) == 2


def test_bounded_response_and_invalid_json():
    with pytest.raises(OpenRouterError, match="RESPONSE_TOO_LARGE"):
        invoke(lambda request: httpx.Response(200, content=b"x" * (2*1024*1024 + 1)))
    with pytest.raises(OpenRouterError, match="REQUEST_FAILED"):
        invoke(lambda request: httpx.Response(200, content=b"not json"))


@pytest.mark.parametrize("generation_request", [{"prompt": " "}, {"prompt": "x", "max_tokens": 0},
    {"prompt": "x", "max_tokens": True}, {"prompt": "x", "temperature": 3.},
    {"prompt": "x", "top_p": 0.}, {"prompt": "x", "system": []}])
def test_invalid_generation_request_never_sends(generation_request):
    def prohibited(_):
        raise AssertionError("must not send")
    with pytest.raises(OpenRouterError, match="INVALID_REQUEST"):
        invoke(prohibited, generation_request)


@pytest.mark.parametrize("reported,expected", [("openai/gpt-4o-mini", "RUNTIME_CONFIRMED"),
                                               (None, "NOT_VERIFIED")])
def test_reported_identity_is_not_loaded_weight_attestation(reported, expected):
    response = invoke(lambda request: httpx.Response(200, json=result(model=reported)))
    assert response["execution_identity"]["identity_status"] == expected
    assert response["reported_model"] == reported


def test_key_failure_and_transport_failure_are_sanitized(caplog):
    def fail(request):
        raise RuntimeError("synthetic-test-credential")
    with pytest.raises(OpenRouterError, match="REQUEST_FAILED") as error:
        invoke(fail)
    assert "synthetic-test-credential" not in str(error.value) + caplog.text


def test_health_is_only_readiness_and_does_not_call_network():
    async def run():
        adapter = OpenRouterProvider(nusantara_config=config(), key_resolver=lambda: "synthetic")
        health = await adapter.health_check()
        assert health["available"] and health["status"] == "NOT_VERIFIED"
        assert adapter._client is None
        assert not adapter.get_model_info()["hard_budget_enforcement"]
        with pytest.raises(OpenRouterError, match="STRUCTURED_UNSUPPORTED"):
            await adapter.generate_structured({"prompt": "fixture"})
        await adapter.close()
    asyncio.run(run())


def test_existing_chat_projection_contract_without_importing_application():
    # Extract the actual pure response projection instead of bootstrapping DB,
    # worker or application. This verifies schema, not live /v1 registration.
    import typing
    from pydantic import BaseModel, ConfigDict, Field
    tree = ast.parse(Path("app/api/routes.py").read_text(encoding="utf-8-sig"))
    targets = {"_project_v1_chat_response"}
    targets.update(node.name for node in tree.body if isinstance(node, ast.ClassDef) and
                   node.name.startswith("_Public"))
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in targets]
    namespace = {"BaseModel": BaseModel, "ConfigDict": ConfigDict, "Field": Field,
                 "Any": typing.Any, "Literal": typing.Literal}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "projection-only", "exec"), namespace)
    payload = {"session_id": "fixture", "response": "answer", "model": "requested/model",
        "provider_status": "openrouter", "latency_ms": 1, "timestamp": "fixture",
        "trust": {"supports_claim": False, "confidence": 0., "risk_level": "low",
                  "requires_human": True, "evidence_count": 0, "evidence_available": False},
        "grounding": {"enabled": True, "grounded": False, "reason": "no_evidence"},
        "understanding": {}, "problem": {}, "evidence": [], "gate_pipeline": {"secret": "private"}}
    public = namespace["_project_v1_chat_response"](payload, intent_name="ask_general_info")
    assert set(public) == {"session_id", "response", "trust", "model", "provider_status", "latency_ms",
        "grounding", "understanding", "problem", "evidence", "timestamp"}
    assert public["provider_status"] == "openrouter" and "private" not in json.dumps(public)


@pytest.mark.parametrize("chosen", ["ollama", "openrouter"])
def test_actual_chat_endpoint_selects_only_explicit_provider_and_projects(chosen):
    """Execute actual endpoint AST, without application/DB/worker startup."""
    import typing
    from types import SimpleNamespace
    from fastapi import HTTPException
    from pydantic import BaseModel, ConfigDict, Field
    from app.hermes.agent import V1CoreResult
    from app.exceptions import ProviderUnavailableError
    tree = ast.parse(Path("app/api/routes.py").read_text(encoding="utf-8-sig"))
    selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and (node.name in {"chat", "ChatRequest", "_project_v1_chat_response"} or
                     node.name.startswith("_Public"))]
    next(node for node in selected if node.name == "chat").decorator_list = []
    calls = {"ollama": 0, "openrouter": 0, "closed": 0, "recorded": 0}
    configuration = load_nusantara_config(overrides={"llm": {"provider": chosen}})
    class LocalFixture:
        model = configuration.llm.model
        async def generate(self, request):
            return {"content": "fixture answer"}
        async def close(self):
            calls["closed"] += 1
    def local_factory(**kwargs):
        calls["ollama"] += 1
        assert kwargs["nusantara_config"] is configuration
        return LocalFixture()
    def cloud_factory(**kwargs):
        calls["openrouter"] += 1
        return OpenRouterProvider(**kwargs, http_client=client, key_resolver=lambda: "synthetic")
    class ExistingCapabilityFixture:
        def __init__(self, **kwargs):
            self.provider = kwargs["provider"]
        async def execute_v1(self, req, **services):
            generated = await self.provider.generate({"prompt": req.user_input})
            payload = {"session_id": req.session_id, "response": generated["content"],
                "trust": {"supports_claim": True, "confidence": .8, "risk_level": "low",
                    "requires_human": False, "evidence_count": 1, "evidence_available": True},
                "model": self.provider.model, "provider_status": chosen, "latency_ms": 1,
                "grounding": {"enabled": True, "grounded": True, "reason": "grounded"},
                "problem": {}, "evidence": [], "timestamp": "fixture"}
            return V1CoreResult(payload=payload, intent_name="ask_general_info")
    def record(**kwargs):
        calls["recorded"] += 1
        assert kwargs["provider_status"] == chosen
    namespace = {"BaseModel": BaseModel, "ConfigDict": ConfigDict, "Field": Field,
        "Any": typing.Any, "Literal": typing.Literal, "HTTPException": HTTPException,
        "ProviderUnavailableError": ProviderUnavailableError,
        "OllamaProvider": local_factory, "OpenRouterProvider": cloud_factory,
        "HermesAgent": ExistingCapabilityFixture,
        "settings": SimpleNamespace(configuration_snapshot=lambda: (configuration, 0), record_v1_execution=record)}
    for name in ("_language", "_knowledge", "_gate_integration", "_trust_engine", "_grounding_guard",
        "_developer_core", "_run_sync_v1", "_extract_understanding_data", "_extract_intent",
        "_reconcile_problem_with_intent", "_extract_entities", "_get_problem_value", "_build_evidence_text",
        "_deterministic_response", "_arithmetic_response", "_build_system_prompt", "_build_user_prompt", "_model_dump"):
        namespace[name] = None  # core dependencies owned by separate Hermes regression tests
    module = ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module="__future__",
        names=[ast.alias(name="annotations")], level=0), *selected], type_ignores=[]))
    exec(compile(module, "chat-only", "exec"), namespace)
    for name, model_type in namespace.copy().items():
        if name.startswith("_Public") or name == "ChatRequest":
            model_type.model_rebuild(_types_namespace=namespace)
    async def run():
        nonlocal client
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request:
                httpx.Response(200, json=result()))) as client:
            public = await namespace["chat"](SimpleNamespace(user_input="fixture question", session_id="fixture", model=None))
            assert public["provider_status"] == chosen
            assert set(public) == {"session_id", "response", "trust", "model", "provider_status", "latency_ms",
                "grounding", "understanding", "problem", "evidence", "timestamp"}
    client = None
    asyncio.run(run())
    assert calls[chosen] == 1 and calls["openrouter" if chosen == "ollama" else "ollama"] == 0
    assert calls["recorded"] == 1

