"""Nusantara V1 - Gate 16.2 Execution Boundary.

Execution Boundary adalah pagar keamanan sebelum execution.

Boundary:
- hanya repository root yang diizinkan
- path traversal ditolak
- absolute path ditolak
- target file harus berada di workspace
- sensitive/system paths ditolak
- operation harus masuk allowlist
- approval harus valid
- execution plan harus konsisten dengan ChangeRequest

TIDAK ADA:
- write
- patch
- delete
- subprocess
- shell
- execute
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.approval.change_request import ChangeRequest
from app.developer_core.execution_plan import (
    BOUNDARY_VALIDATED,
    EXECUTABLE,
    ExecutionPlan,
    VALID_OPERATIONS,
)


SENSITIVE_NAMES = {
    ".env",
    ".git",
    ".gitconfig",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}


@dataclass(frozen=True)
class BoundaryResult:
    allowed: bool
    errors: tuple[str, ...]
    checked_rules: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "errors": list(self.errors),
            "checked_rules": list(self.checked_rules),
        }


class ExecutionBoundaryError(PermissionError):
    """ExecutionPlan melanggar execution boundary."""


class ExecutionBoundary:
    """Deterministic security boundary sebelum execution."""

    def __init__(self, workspace_root: str | Path):
        self.root = Path(workspace_root).resolve()

    def validate(
        self,
        plan: ExecutionPlan,
        *,
        approval_valid: bool = False,
        change_request: ChangeRequest | None = None,
    ) -> BoundaryResult:

        errors: list[str] = []
        checked: list[str] = []

        # ----------------------------------------------------------
        # 1. Plan type
        # ----------------------------------------------------------
        checked.append("execution_plan_type")

        if not isinstance(plan, ExecutionPlan):
            return BoundaryResult(
                False,
                ("execution_plan harus berupa ExecutionPlan",),
                tuple(checked),
            )

        # ----------------------------------------------------------
        # 2. Operation allowlist
        # ----------------------------------------------------------
        checked.append("operation_allowlist")

        if plan.operation not in VALID_OPERATIONS:
            errors.append(
                f"operation tidak diizinkan: {plan.operation}"
            )

        # ----------------------------------------------------------
        # 3. Approval
        # ----------------------------------------------------------
        checked.append("approval_required")

        if not plan.approved:
            errors.append(
                "ExecutionPlan belum approved"
            )

        if not approval_valid:
            errors.append(
                "approval_valid=False"
            )

        # ----------------------------------------------------------
        # 4. Status
        # ----------------------------------------------------------
        checked.append("execution_status")

        if plan.status not in (
            BOUNDARY_VALIDATED,
            EXECUTABLE,
        ):
            errors.append(
                f"status belum melewati boundary: {plan.status}"
            )

        # ----------------------------------------------------------
        # 5. ChangeRequest binding
        # ----------------------------------------------------------
        checked.append("change_request_binding")

        if change_request is not None:
            if change_request.proposal_id != plan.change_id:
                errors.append(
                    "change_id tidak sama dengan ChangeRequest"
                )

            if list(change_request.affected_files) != list(
                plan.target_files
            ):
                errors.append(
                    "target_files berbeda dari ChangeRequest"
                )

        # ----------------------------------------------------------
        # 6. Workspace boundary
        # ----------------------------------------------------------
        checked.append("workspace_boundary")

        for raw_path in plan.target_files:
            self._validate_path(raw_path, errors)

        # ----------------------------------------------------------
        # 7. No wildcard / broad target
        # ----------------------------------------------------------
        checked.append("target_specificity")

        for raw_path in plan.target_files:
            normalized = raw_path.replace("\\", "/")

            if normalized in ("*", "**", ".", "./"):
                errors.append(
                    f"target terlalu luas: {raw_path}"
                )

            if "*" in normalized:
                errors.append(
                    f"wildcard target tidak diizinkan: {raw_path}"
                )

        # ----------------------------------------------------------
        # 8. Required execution metadata
        # ----------------------------------------------------------
        checked.append("execution_metadata")

        if not plan.expected_change.strip():
            errors.append("expected_change kosong")

        if not plan.preconditions:
            errors.append("preconditions kosong")

        if not plan.validation_steps:
            errors.append("validation_steps kosong")

        if not plan.rollback_boundary.strip():
            errors.append("rollback_boundary kosong")

        return BoundaryResult(
            allowed=not errors,
            errors=tuple(errors),
            checked_rules=tuple(checked),
        )

    def require_allowed(
        self,
        plan: ExecutionPlan,
        *,
        approval_valid: bool = False,
        change_request: ChangeRequest | None = None,
    ) -> BoundaryResult:
        """Fail-closed helper.

        Hanya melakukan validasi.
        Tidak melakukan execution.
        """
        result = self.validate(
            plan,
            approval_valid=approval_valid,
            change_request=change_request,
        )

        if not result.allowed:
            raise ExecutionBoundaryError(
                "Execution Boundary BLOCKED: "
                + "; ".join(result.errors)
            )

        return result

    def _validate_path(
        self,
        raw_path: str,
        errors: list[str],
    ) -> None:
        if not isinstance(raw_path, str) or not raw_path.strip():
            errors.append("target path kosong")
            return

        normalized = raw_path.replace("\\", "/")

        # Absolute Windows / POSIX path
        candidate = Path(raw_path)

        if candidate.is_absolute():
            errors.append(
                f"absolute path tidak diizinkan: {raw_path}"
            )
            return

        # Explicit traversal
        parts = Path(normalized).parts

        if ".." in parts:
            errors.append(
                f"path traversal tidak diizinkan: {raw_path}"
            )
            return

        # Sensitive path components
        lowered_parts = {
            part.lower()
            for part in parts
        }

        if lowered_parts & {
            name.lower()
            for name in SENSITIVE_NAMES
        }:
            errors.append(
                f"sensitive path tidak diizinkan: {raw_path}"
            )
            return

        resolved = (self.root / raw_path).resolve()

        try:
            resolved.relative_to(self.root)
        except ValueError:
            errors.append(
                f"path berada di luar workspace: {raw_path}"
            )


__all__ = [
    "BoundaryResult",
    "ExecutionBoundary",
    "ExecutionBoundaryError",
]
