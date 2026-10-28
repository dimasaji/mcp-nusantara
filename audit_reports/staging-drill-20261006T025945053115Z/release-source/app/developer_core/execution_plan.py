"""Nusantara V1 - Gate 16.1 Execution Plan Schema.

ExecutionPlan mendeskripsikan perubahan yang DIIZINKAN untuk dieksekusi.
Schema ini tidak melakukan write, patch, subprocess, atau execution.

Gate 16.1:
    ChangeRequest -> ExecutionPlan -> Boundary Validation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PLANNED = "PLANNED"
BOUNDARY_VALIDATED = "BOUNDARY_VALIDATED"
EXECUTABLE = "EXECUTABLE"
BLOCKED = "BLOCKED"


VALID_STATUSES = (
    PLANNED,
    BOUNDARY_VALIDATED,
    EXECUTABLE,
    BLOCKED,
)


ALLOWED_TRANSITIONS = {
    PLANNED: (BOUNDARY_VALIDATED, BLOCKED),
    BOUNDARY_VALIDATED: (EXECUTABLE, BLOCKED),
    EXECUTABLE: (BLOCKED,),
    BLOCKED: (),
}


VALID_OPERATIONS = (
    "modify_existing_file",
    "create_file",
    "delete_file",
)


@dataclass(frozen=True)
class ExecutionPlan:
    """Immutable description of a controlled execution."""

    execution_id: str
    change_id: str

    operation: str
    target_files: tuple[str, ...]
    target_modules: tuple[str, ...]

    expected_change: str
    preconditions: tuple[str, ...]
    validation_steps: tuple[str, ...]
    rollback_boundary: str

    approved: bool = False
    status: str = PLANNED

    def __post_init__(self) -> None:
        if not self.execution_id.strip():
            raise ValueError("execution_id wajib diisi")

        if not self.change_id.strip():
            raise ValueError("change_id wajib diisi")

        if self.operation not in VALID_OPERATIONS:
            raise ValueError(
                f"operation tidak valid: {self.operation}"
            )

        if not self.target_files:
            raise ValueError(
                "target_files wajib berisi minimal satu file"
            )

        if not self.target_modules:
            raise ValueError(
                "target_modules wajib berisi minimal satu module"
            )

        if not self.expected_change.strip():
            raise ValueError(
                "expected_change wajib diisi"
            )

        if not self.preconditions:
            raise ValueError(
                "preconditions wajib tersedia"
            )

        if not self.validation_steps:
            raise ValueError(
                "validation_steps wajib tersedia"
            )

        if not self.rollback_boundary.strip():
            raise ValueError(
                "rollback_boundary wajib diisi"
            )

        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"status tidak valid: {self.status}"
            )

        if not isinstance(self.approved, bool):
            raise ValueError(
                "approved harus boolean"
            )

        for name, value in (
            ("target_files", self.target_files),
            ("target_modules", self.target_modules),
            ("preconditions", self.preconditions),
            ("validation_steps", self.validation_steps),
        ):
            if not isinstance(value, tuple):
                raise ValueError(
                    f"{name} harus tuple immutable"
                )

    def to_payload(self) -> dict[str, Any]:
        """Payload deterministik tanpa timestamp/random metadata."""
        return {
            "execution_id": self.execution_id,
            "change_id": self.change_id,
            "operation": self.operation,
            "target_files": list(self.target_files),
            "target_modules": list(self.target_modules),
            "expected_change": self.expected_change,
            "preconditions": list(self.preconditions),
            "validation_steps": list(self.validation_steps),
            "rollback_boundary": self.rollback_boundary,
            "approved": self.approved,
            "status": self.status,
        }

    def transition(
        self,
        new_status: str,
        *,
        approval_valid: bool = False,
    ) -> "ExecutionPlan":
        """Return immutable plan dengan status baru.

        Tidak melakukan execution.
        """
        if new_status not in VALID_STATUSES:
            raise ValueError(
                f"status target tidak valid: {new_status}"
            )

        allowed = ALLOWED_TRANSITIONS[self.status]

        if new_status not in allowed:
            raise ValueError(
                f"transition tidak diizinkan: "
                f"{self.status} -> {new_status}"
            )

        if new_status == EXECUTABLE and not approval_valid:
            raise PermissionError(
                "EXECUTABLE membutuhkan approval yang valid"
            )

        if new_status == EXECUTABLE and not self.approved:
            raise PermissionError(
                "EXECUTABLE membutuhkan approved=True"
            )

        return ExecutionPlan(
            execution_id=self.execution_id,
            change_id=self.change_id,
            operation=self.operation,
            target_files=self.target_files,
            target_modules=self.target_modules,
            expected_change=self.expected_change,
            preconditions=self.preconditions,
            validation_steps=self.validation_steps,
            rollback_boundary=self.rollback_boundary,
            approved=self.approved,
            status=new_status,
        )


__all__ = [
    "PLANNED",
    "BOUNDARY_VALIDATED",
    "EXECUTABLE",
    "BLOCKED",
    "VALID_STATUSES",
    "ALLOWED_TRANSITIONS",
    "VALID_OPERATIONS",
    "ExecutionPlan",
]
