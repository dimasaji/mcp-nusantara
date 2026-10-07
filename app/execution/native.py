"""Delegate to existing governance; actor identity comes from trusted wiring."""
from typing import Any

from app.governance.tools import GovernedToolRegistry, ToolOutcome


class NativeExecutor:
    def __init__(self, registry: GovernedToolRegistry, *, role: str,
                 permissions: frozenset[str], requested_by: str):
        self.registry = registry
        self._role = role
        self._permissions = frozenset(permissions)
        self._requested_by = requested_by

    def execute(self, name: str, arguments: dict[str, Any], *,
                approval_id: str | None = None) -> ToolOutcome:
        return self.registry.execute(name, arguments, role=self._role,
                                     permissions=set(self._permissions),
                                     requested_by=self._requested_by, approval_id=approval_id)
