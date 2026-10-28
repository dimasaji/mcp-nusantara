"""Tool governance: LLM tidak pernah menjalankan tool tanpa registry + policy + audit."""
from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.approval.queue import ApprovalQueue
from app.core.hardening import CircuitBreaker, safe_call, validate_schema
from app.observability.metrics import metrics


class ToolClass(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    EXTERNAL = "external"


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(str, Enum):  # nilai sama dengan app.policy.schemas.PolicyDecision
    ALLOW = "ALLOW"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    REQUIRE_HUMAN = "REQUIRE_HUMAN"
    DENY = "DENY"


@dataclass(frozen=True)
class ToolSpec:
    tool_name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    tool_class: ToolClass
    risk: Risk
    permission: str = ""
    timeout_s: float = 10.0
    audit_required: bool = True


@dataclass
class ToolOutcome:
    status: str  # executed | pending_approval | denied | invalid_input | failed | unknown_tool
    tool: str
    output: Any = None
    error: str | None = None
    approval_id: str | None = None
    decision: str | None = None


PolicyFn = Callable[[ToolSpec, str], tuple[Decision, str]]


def default_tool_policy(spec: ToolSpec, role: str) -> tuple[Decision, str]:
    """Kebijakan bawaan: CRITICAL ditolak, HIGH butuh manusia, WRITE/EXECUTE/DELETE/EXTERNAL
    minimal konfirmasi. Fail-closed."""
    if spec.risk == Risk.CRITICAL:
        return Decision.DENY, "risiko kritis ditolak"
    if spec.risk == Risk.HIGH:
        return Decision.REQUIRE_HUMAN, "risiko tinggi butuh persetujuan manusia"
    if spec.tool_class in (ToolClass.DELETE, ToolClass.EXECUTE):
        return Decision.REQUIRE_HUMAN, f"tool {spec.tool_class.value} butuh persetujuan manusia"
    if spec.tool_class in (ToolClass.WRITE, ToolClass.EXTERNAL) or spec.risk == Risk.MEDIUM:
        return Decision.REQUIRE_CONFIRMATION, "perlu konfirmasi"
    return Decision.ALLOW, "read/low-risk"


@dataclass
class _Entry:
    spec: ToolSpec
    handler: Callable[[dict[str, Any]], Any]
    breaker: CircuitBreaker


class GovernedToolRegistry:
    def __init__(self, approvals: ApprovalQueue, policy: PolicyFn = default_tool_policy):
        self.approvals = approvals
        self.policy = policy
        self._tools: dict[str, _Entry] = {}

    def register(self, spec: ToolSpec, handler: Callable[[dict[str, Any]], Any]) -> None:
        if inspect.iscoroutinefunction(handler):
            raise TypeError("handler tool harus sync (jalankan async di luar registry)")
        if spec.tool_name in self._tools:
            raise ValueError(f"tool '{spec.tool_name}' sudah terdaftar")
        self._tools[spec.tool_name] = _Entry(spec, handler, CircuitBreaker(spec.tool_name))

    def visible_tools(self, role: str, permissions: set[str]) -> list[dict[str, Any]]:
        """Hanya tool yang boleh dilihat model: permission terpenuhi & bukan DENY."""
        out = []
        for e in self._tools.values():
            s = e.spec
            if s.permission and s.permission not in permissions:
                continue
            if self.policy(s, role)[0] == Decision.DENY:
                continue
            out.append({"name": s.tool_name, "description": s.description,
                        "input_schema": s.input_schema, "risk": s.risk.value,
                        "class": s.tool_class.value})
        return out

    def execute(self, name: str, args: dict[str, Any], *, role: str, permissions: set[str],
                requested_by: str, approval_id: str | None = None) -> ToolOutcome:
        audit = self.approvals.audit
        entry = self._tools.get(name)
        if entry is None:  # nama tool dari model tidak dipercaya
            audit.record("tool.unknown", tool=name, requested_by=requested_by)
            return ToolOutcome("unknown_tool", name, error="tool tidak terdaftar", decision=Decision.DENY.value)
        s = entry.spec
        if s.permission and s.permission not in permissions:
            audit.record("tool.denied", tool=name, reason="permission", requested_by=requested_by)
            return ToolOutcome("denied", name, error="permission tidak cukup", decision=Decision.DENY.value)
        decision, why = self.policy(s, role)
        audit.record("tool.policy", tool=name, decision=decision.value, reason=why,
                     risk=s.risk.value, requested_by=requested_by)
        if decision == Decision.DENY:
            return ToolOutcome("denied", name, error=why, decision=decision.value)
        errs = validate_schema(args, s.input_schema)
        if errs:
            return ToolOutcome("invalid_input", name, error="; ".join(errs), decision=decision.value)
        if decision != Decision.ALLOW:
            granted = bool(approval_id) and self.approvals.consume(approval_id, {"tool": name, "args": args})
            if not granted:
                req = self.approvals.submit(
                    "tool_call", {"tool": name, "args": args}, risk=s.risk.value,
                    requested_by=requested_by, summary={"tool": name, "class": s.tool_class.value, "reason": why})
                return ToolOutcome("pending_approval", name, approval_id=req.approval_id,
                                   decision=decision.value, error=why)
        res = safe_call(entry.handler, args, timeout_s=s.timeout_s, breaker=entry.breaker)
        metrics.incr(f"tool.{name}.{'ok' if res.ok else 'fail'}")
        if s.audit_required:
            audit.record("tool.executed", tool=name, ok=res.ok, error=res.error,
                         duration_ms=round(res.duration_ms, 2), requested_by=requested_by)
        if not res.ok:
            return ToolOutcome("failed", name, error=f"{res.error_type}: {res.error}", decision=decision.value)
        oerrs = validate_schema(res.value, s.output_schema)
        if oerrs:
            return ToolOutcome("failed", name, error="output tidak sesuai skema: " + "; ".join(oerrs),
                               decision=decision.value)
        return ToolOutcome("executed", name, output=res.value, decision=decision.value)
