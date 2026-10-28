"""Nusantara V1 - Gate 15 Operational ChangePlan.

ChangePlan adalah kontrak deterministik untuk merencanakan perubahan.
Gate ini BELUM melakukan patch/write/execute.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PROPOSED = "PROPOSED"
VALIDATED = "VALIDATED"
APPROVED = "APPROVED"
READY = "READY"
REJECTED = "REJECTED"
INVALID = "INVALID"

VALID_STATUSES = frozenset({
    PROPOSED,
    VALIDATED,
    APPROVED,
    READY,
    REJECTED,
    INVALID,
})

# Transisi yang diperbolehkan pada Gate 15.
# READY sengaja tidak dapat dicapai langsung dari PROPOSED.
ALLOWED_TRANSITIONS = {
    PROPOSED: frozenset({VALIDATED, INVALID, REJECTED}),
    VALIDATED: frozenset({APPROVED, INVALID, REJECTED}),
    APPROVED: frozenset({READY, REJECTED}),
    READY: frozenset(),
    REJECTED: frozenset(),
    INVALID: frozenset(),
}

VALID_RISKS = frozenset({
    "low",
    "medium",
    "high",
    "critical",
})


class ChangePlanError(ValueError):
    """Kesalahan kontrak ChangePlan."""


@dataclass(frozen=True)
class ChangePlan:
    change_id: str
    request: str
    scope: str
    affected_files: tuple[str, ...] = field(default_factory=tuple)
    affected_modules: tuple[str, ...] = field(default_factory=tuple)
    affected_symbols: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    dependents: tuple[str, ...] = field(default_factory=tuple)
    directional_impact: dict[str, Any] = field(default_factory=dict)
    risk_signals: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)
    validation_plan: tuple[str, ...] = field(default_factory=tuple)
    rollback_boundary: str = ""
    approval_required: bool = True
    status: str = PROPOSED

    def __post_init__(self) -> None:
        if not isinstance(self.change_id, str) or not self.change_id.strip():
            raise ChangePlanError("change_id wajib diisi")

        if not isinstance(self.request, str) or not self.request.strip():
            raise ChangePlanError("request wajib diisi")

        if not isinstance(self.scope, str) or not self.scope.strip():
            raise ChangePlanError("scope wajib diisi")

        if self.approval_required is not True:
            raise ChangePlanError(
                "approval_required harus True untuk ChangePlan"
            )

        if self.status not in VALID_STATUSES:
            raise ChangePlanError(
                f"status tidak valid: {self.status!r}"
            )

        if not isinstance(self.affected_files, tuple):
            raise ChangePlanError("affected_files harus tuple")

        if not isinstance(self.affected_modules, tuple):
            raise ChangePlanError("affected_modules harus tuple")

        if not isinstance(self.affected_symbols, tuple):
            raise ChangePlanError("affected_symbols harus tuple")

        if not isinstance(self.dependencies, tuple):
            raise ChangePlanError("dependencies harus tuple")

        if not isinstance(self.dependents, tuple):
            raise ChangePlanError("dependents harus tuple")

        if not isinstance(self.risk_signals, tuple):
            raise ChangePlanError("risk_signals harus tuple")

        if not isinstance(self.evidence, tuple):
            raise ChangePlanError("evidence harus tuple")

        if not isinstance(self.validation_plan, tuple):
            raise ChangePlanError("validation_plan harus tuple")

    def to_payload(self) -> dict[str, Any]:
        """Payload deterministik untuk approval/hash.

        Tidak memasukkan timestamp atau metadata runtime.
        """
        return {
            "change_id": self.change_id,
            "request": self.request,
            "scope": self.scope,
            "affected_files": list(self.affected_files),
            "affected_modules": list(self.affected_modules),
            "affected_symbols": list(self.affected_symbols),
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "directional_impact": self.directional_impact,
            "risk_signals": list(self.risk_signals),
            "evidence": list(self.evidence),
            "validation_plan": list(self.validation_plan),
            "rollback_boundary": self.rollback_boundary,
            "approval_required": self.approval_required,
            "status": self.status,
        }

    def transition(self, new_status: str) -> "ChangePlan":
        """Membuat ChangePlan baru dengan status berikutnya.

        Objek lama immutable sehingga payload yang telah disetujui
        tidak dapat diam-diam berubah.
        """
        if new_status not in VALID_STATUSES:
            raise ChangePlanError(f"status tidak valid: {new_status!r}")

        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise ChangePlanError(
                f"transisi tidak diizinkan: {self.status} -> {new_status}"
            )

        return ChangePlan(
            change_id=self.change_id,
            request=self.request,
            scope=self.scope,
            affected_files=self.affected_files,
            affected_modules=self.affected_modules,
            affected_symbols=self.affected_symbols,
            dependencies=self.dependencies,
            dependents=self.dependents,
            directional_impact=dict(self.directional_impact),
            risk_signals=self.risk_signals,
            evidence=self.evidence,
            validation_plan=self.validation_plan,
            rollback_boundary=self.rollback_boundary,
            approval_required=self.approval_required,
            status=new_status,
        )


__all__ = [
    "APPROVED",
    "ALLOWED_TRANSITIONS",
    "ChangePlan",
    "ChangePlanError",
    "INVALID",
    "PROPOSED",
    "READY",
    "REJECTED",
    "VALIDATED",
    "VALID_RISKS",
    "VALID_STATUSES",
]
