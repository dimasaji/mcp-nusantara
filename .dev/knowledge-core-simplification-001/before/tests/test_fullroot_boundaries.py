"""Actual reused gateway/executor behavior in isolated, governed fixtures."""
import asyncio

import pytest

from app.approval import ApprovalQueue, AuditTrail
from app.execution.base import AgentExecutorInterface, ExecutorInterface
from app.execution.native import NativeExecutor
from app.governance.mcp_bridge import register_builtin_tools
from app.governance.tools import GovernedToolRegistry, Risk, ToolClass, ToolSpec
from app.models.gateway import ModelGateway
from app.models.mock import MockProvider
from app.models.router import ModelRouter
from app.v2.hermes_adapter import HermesV2Adapter
from app.v2.orchestrator import V2Orchestrator


def executor(tmp_path):
    audit = AuditTrail(tmp_path / "audit.jsonl")
    registry = GovernedToolRegistry(ApprovalQueue(audit))
    register_builtin_tools(registry)
    return NativeExecutor(registry, role="user", permissions=frozenset(), requested_by="fixture")


def test_sync_and_async_provider_results_use_existing_response_contract():
    class AsyncMock(MockProvider):
        async def generate(self, request):
            return super().generate(request)
    for provider in [MockProvider(mock_response="answer"), AsyncMock(mock_response="answer")]:
        gateway = ModelGateway(ModelRouter().register(provider))
        assert asyncio.run(gateway.generate_text("fixture")) == "answer"
        assert gateway.select(task="coding").model_name == provider.model


def test_gateway_integration_and_fallback_remain_orchestrator_owned(tmp_path):
    audit = AuditTrail(tmp_path / "audit.jsonl")
    gateway = ModelGateway(ModelRouter().register(MockProvider(mock_response="local answer")))
    runtime = V2Orchestrator(generate=gateway.generate_text, audit=audit)
    result = asyncio.run(runtime.handle("fixture", "isolated"))
    assert result.response == "local answer" and result.status == "ok"
    unavailable = V2Orchestrator(generate=ModelGateway(ModelRouter()).generate_text, audit=audit)
    failed = asyncio.run(unavailable.handle("fixture", "isolated"))
    assert failed.status == "degraded"
    assert any("RuntimeError" in value for value in failed.degraded)


def test_gateway_rejects_unrecognized_output():
    class InvalidMock(MockProvider):
        def generate(self, request):
            return {"unexpected": "value"}
    gateway = ModelGateway(ModelRouter().register(InvalidMock()))
    with pytest.raises(TypeError, match="must contain text"):
        asyncio.run(gateway.generate_text("fixture"))


def test_executor_uses_governance_for_allowed_invalid_and_unknown_tools(tmp_path):
    runtime = executor(tmp_path)
    assert isinstance(runtime, ExecutorInterface)
    assert runtime.execute("calculator", {"expression": "2+2"}).output == {"result": 4}
    assert runtime.execute("calculator", {}).status == "invalid_input"
    assert runtime.execute("missing", {}).status == "unknown_tool"


def test_executor_cannot_grant_permissions_from_tool_payload(tmp_path):
    runtime = executor(tmp_path)
    runtime.registry.register(ToolSpec("private", "fixture", {"type": "object"},
                                     {"type": "object"}, ToolClass.READ, Risk.LOW,
                                     permission="admin"), lambda args: {})
    result = runtime.execute("private", {"role": "admin", "permissions": ["admin"]})
    assert result.status == "denied"
    assert (tmp_path / "audit.jsonl").exists()


def test_hermes_adapter_satisfies_optional_agent_protocol_without_worker():
    class Fixture:
        def run(self, **kwargs):
            return {"understanding": {"fixture": True}, "problem": None, "reasoning": None}
    adapter = HermesV2Adapter(agent=Fixture())
    assert isinstance(adapter, AgentExecutorInterface)
    assert adapter.run("fixture", "isolated")["understanding"] == {"fixture": True}
