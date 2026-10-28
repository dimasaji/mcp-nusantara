"""Real optional StateGraph, existing Hermes, synthetic offline V1 services."""
import asyncio
import ast
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import typing

import pytest
from pydantic import BaseModel, ConfigDict, Field

from app.core.nusantara_config import load_nusantara_config
from app.hermes.agent import HermesAgent
from app.knowledge.grounding import EvidenceGroundingGuard
from app.trust.engine import TrustEngine
from app.workflow.v1_langgraph import V1LangGraphWorkflow, V1WorkflowError


def projection_and_helpers():
    tree = ast.parse(Path("app/api/routes.py").read_text(encoding="utf-8-sig"))
    helpers = {"_extract_understanding_data", "_extract_intent", "_reconcile_problem_with_intent",
        "_extract_entities", "_get_problem_value", "_build_evidence_text", "_deterministic_response", "_arithmetic_response",
        "_build_system_prompt", "_build_user_prompt", "_model_dump"}
    names = helpers | {"_project_v1_chat_response"}
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and
             (node.name in names or node.name.startswith("_Public"))]
    namespace = {"BaseModel": BaseModel, "ConfigDict": ConfigDict, "Field": Field,
                 "Any": typing.Any, "Literal": typing.Literal, "Dict": typing.Dict}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "v1-pure-helpers", "exec"), namespace)
    return namespace["_project_v1_chat_response"], {name: namespace[name] for name in helpers}


class FixtureProvider:
    def __init__(self, configuration, failure=None, answer=None):
        self.name, self.model = configuration.llm.provider, configuration.llm.model
        self.calls, self.failure = 0, failure
        self.answer = answer or "KTP-el adalah identitas penduduk."

    async def health_check(self):
        return {"available": True}

    async def generate(self, request):
        self.calls += 1
        if self.failure == "timeout":
            await asyncio.sleep(60)
        if self.failure == "error":
            raise RuntimeError("synthetic-private-payload")
        return {"content": self.answer}


def fixture(*, enabled=True, provider="ollama", empty=False, failure=None, answer=None):
    configuration = load_nusantara_config(overrides={"features": {"langgraph_workflow": enabled},
        "llm": {"provider": provider}, "runtime": {"stage_timeout_s": .05 if failure == "timeout" else 10.}})
    model = FixtureProvider(configuration, failure, answer)
    # Constructor is avoided to keep native LanguageEngine/worker startup out
    # of this offline test. execute_v1 is the actual unchanged Hermes method.
    agent = HermesAgent.__new__(HermesAgent)
    agent.provider = model
    observed = {"classified": 0, "searched": 0, "remembered": 0, "gated": 0}
    def understand(*args, **kwargs):
        observed["classified"] += 1
        return {"understanding": {"output": {"intent": {"intent": "ask_general_info", "confidence": .95},
                    "entities": []}}, "problem": {"goal": "Memahami KTP-el", "situation": "Pertanyaan"}}
    agent.run = understand
    citation = SimpleNamespace(document_id="fixture-ktp", title="Fixture KTP-el",
        chunk="KTP-el adalah identitas penduduk.", source="offline fixture", score=.9)
    def search(*args, **kwargs):
        observed["searched"] += 1
        return [] if empty else [citation]
    def process(**kwargs):
        observed["gated"] += 1
        return {"reasoning": {"status": "grounded"}}
    def remember(**kwargs):
        observed["remembered"] += 1
    async def run_sync(fn, *args, **kwargs):
        return fn(*args, **kwargs)
    projector, helpers = projection_and_helpers()
    services = {"knowledge": SimpleNamespace(search_knowledge=search),
        "gates": SimpleNamespace(process=process, remember_response=remember),
        "trust": TrustEngine(), "grounding": EvidenceGroundingGuard(),
        "developer_core": SimpleNamespace(runtime_snapshot=lambda **kwargs: {}),
        "run_sync": run_sync, "helpers": helpers}
    return configuration, agent, services, projector, model, observed


def workflow(parts):
    configuration, agent, services, projector, _, _ = parts
    return V1LangGraphWorkflow(configuration=configuration, agent=agent,
        services=services, project_response=projector)


def request(**updates):
    return SimpleNamespace(user_input="Apa itu KTP-el?", session_id="fixture-session",
                           model=None, stream=False, **updates)


def test_disabled_flag_does_not_import_langgraph_or_execute(monkeypatch):
    import builtins
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.startswith("langgraph"):
            raise AssertionError("must not import optional dependency")
        return original(name, *args, **kwargs)
    parts = fixture(enabled=False)
    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(V1WorkflowError, match="DISABLED"):
        workflow(parts)
    assert parts[4].calls == 0


def test_unavailable_dependency_fails_closed(monkeypatch):
    import builtins
    original = builtins.__import__
    def unavailable(name, *args, **kwargs):
        if name.startswith("langgraph"):
            raise ImportError("not installed")
        return original(name, *args, **kwargs)
    parts = fixture()
    monkeypatch.setattr(builtins, "__import__", unavailable)
    with pytest.raises(V1WorkflowError, match="LANGGRAPH_UNAVAILABLE"):
        workflow(parts)
    assert parts[4].calls == 0


def test_cloud_binding_is_rejected_before_graph_import():
    parts = fixture()
    parts[4].name = "openrouter"
    with pytest.raises(V1WorkflowError, match="PROVIDER_NOT_APPROVED"):
        workflow(parts)
    assert parts[4].calls == 0


graph_available = pytest.mark.skipif(importlib.util.find_spec("langgraph") is None,
                                    reason="Optional LangGraph not installed in this interpreter")


@graph_available
@pytest.mark.parametrize("provider", ["ollama", "openrouter"])
def test_real_stategraph_executes_existing_hermes_once_and_projects(provider):
    parts = fixture(provider=provider)
    public = asyncio.run(workflow(parts).execute(request()))
    assert public["session_id"] == "fixture-session"
    assert public["provider_status"] == provider
    assert public["grounding"]["grounded"] is True
    assert public["response"] == "KTP-el adalah identitas penduduk."
    assert parts[4].calls == 1
    assert parts[5] == {"classified": 1, "searched": 1, "remembered": 1, "gated": 1}
    assert "gate_pipeline" not in public and "developer_core" not in public


@graph_available
@pytest.mark.parametrize("updates", [{"user_input": " "}, {"session_id": ""},
    {"model": "unapproved/model"}, {"stream": True}, {"user_input": "x" * 20001}])
def test_invalid_input_does_not_reach_provider(updates):
    parts = fixture()
    req = request()
    for name, value in updates.items():
        setattr(req, name, value)
    with pytest.raises(V1WorkflowError):
        asyncio.run(workflow(parts).execute(req))
    assert parts[4].calls == 0 and parts[5]["searched"] == 0


@graph_available
@pytest.mark.parametrize("failure,code", [("error", "EXECUTION_FAILED"), ("timeout", "TIMEOUT")])
def test_failure_and_timeout_never_retry_or_expose_private_exception(failure, code, caplog):
    parts = fixture(failure=failure)
    with pytest.raises(V1WorkflowError, match=code) as observed:
        asyncio.run(workflow(parts).execute(request()))
    assert parts[4].calls == 1 and parts[5]["remembered"] == 0
    assert "synthetic-private-payload" not in str(observed.value) + caplog.text


@graph_available
@pytest.mark.parametrize("empty,answer", [(True, None), (False, "Wajib membayar biaya 900 rupiah.")])
def test_existing_grounding_rejects_missing_evidence_and_unsupported_claim(empty, answer):
    parts = fixture(empty=empty, answer=answer)
    public = asyncio.run(workflow(parts).execute(request()))
    assert public["grounding"]["grounded"] is False
    assert public["response"] == "Informasi tersebut belum tersedia secara cukup dalam knowledge base."
    assert parts[4].calls == 1 and parts[5]["gated"] == 1


@graph_available
def test_greeting_and_legacy_core_match_without_paid_request():
    wrapped, legacy = fixture(), fixture(enabled=False)
    req = request()
    req.user_input = "Halo"
    output = asyncio.run(workflow(wrapped).execute(req))
    configuration, agent, services, projector, model, observed = legacy
    core = asyncio.run(agent.execute_v1(req, **services))
    direct = projector(core.payload, intent_name=core.intent_name)
    for field in output.keys() - {"timestamp"}:
        assert output[field] == direct[field]
    assert wrapped[4].calls == model.calls == 0
    assert output["provider_status"] == "local_rule"


@graph_available
def test_provider_mutation_is_rejected_before_execution():
    parts = fixture()
    graph = workflow(parts)
    parts[4].name = "openrouter"
    with pytest.raises(V1WorkflowError, match="PROVIDER_NOT_APPROVED"):
        asyncio.run(graph.execute(request()))
    assert parts[4].calls == 0


@graph_available
def test_graph_has_no_loop_checkpointer_or_retry_policy():
    parts = fixture()
    graph = workflow(parts)._graph
    assert graph.checkpointer is None
    structure = graph.get_graph()
    assert len(structure.nodes) == 8 and len(structure.edges) == 7
    assert all(not node.retry_policy for node in graph.nodes.values())


@graph_available
def test_cancellation_does_not_replay_paid_request():
    parts = fixture(failure="timeout")
    async def run():
        task = asyncio.create_task(workflow(parts).execute(request()))
        async with asyncio.timeout(1):
            while parts[4].calls == 0:
                await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(run())
    assert parts[4].calls == 1 and parts[5]["remembered"] == 0
