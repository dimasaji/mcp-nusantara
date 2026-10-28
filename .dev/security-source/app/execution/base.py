"""Structural executor contracts independent of any Hermes implementation."""
from typing import Any, Protocol, runtime_checkable

from app.governance.tools import ToolOutcome


@runtime_checkable
class ExecutorInterface(Protocol):
    def execute(self, name: str, arguments: dict[str, Any], *,
                approval_id: str | None = None) -> ToolOutcome: ...


@runtime_checkable
class AgentExecutorInterface(Protocol):
    def run(self, user_input: str, session_id: str,
            evidence: list[Any] | None = None,
            context: dict[str, Any] | None = None) -> dict[str, Any]: ...
