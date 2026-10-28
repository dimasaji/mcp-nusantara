"""Nusantara V1 - Gate 16.3 Execution Approval Enforcement.

Binds:
    ChangePlan
    Human Approval
    ChangeRequest
    ExecutionPlan

Execution is NOT performed here.
This module only authorizes an exact ExecutionPlan.

Fail-closed:
- approval missing
- approval not APPROVED
- approval expired
- payload hash mismatch
- change_id mismatch
- target files mismatch
- approval already consumed
- invalid execution status
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.approval.queue import APPROVED, CONSUMED, ApprovalQueue, payload_hash
from app.developer_core.execution_plan import (
    BOUNDARY_VALIDATED,
    EXECUTABLE,
    ExecutionPlan,
)


@dataclass(frozen=True)
class ExecutionApprovalResult:
    allowed: bool
    execution_id: str
    change_id: str
    approval_id: str
    payload_hash: str
    errors: tuple[str, ...]
    checked_rules: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "execution_id": self.execution_id,
            "change_id": self.change_id,
            "approval_id": self.approval_id,
            "payload_hash": self.payload_hash,
            "errors": list(self.errors),
            "checked_rules": list(self.checked_rules),
        }


class ExecutionApprovalError(PermissionError):
    """ExecutionPlan tidak memenuhi approval contract."""


class ExecutionApprovalEnforcer:
    """Deterministic approval gate untuk ExecutionPlan."""

    def __init__(self, approval_queue: ApprovalQueue):
        self.queue = approval_queue

    def validate(
        self,
        plan: ExecutionPlan,
        approval_id: str,
    ) -> ExecutionApprovalResult:

        errors: list[str] = []
        checked: list[str] = []

        # ----------------------------------------------------------
        # 1. ExecutionPlan type
        # ----------------------------------------------------------
        checked.append("execution_plan_type")

        if not isinstance(plan, ExecutionPlan):
            return ExecutionApprovalResult(
                allowed=False,
                execution_id="",
                change_id="",
                approval_id=approval_id,
                payload_hash="",
                errors=("execution_plan tidak valid",),
                checked_rules=tuple(checked),
            )

        # ----------------------------------------------------------
        # 2. Approval existence
        # ----------------------------------------------------------
        checked.append("approval_exists")

        approval = self.queue.get(approval_id)

        if approval is None:
            errors.append(
                "approval tidak ditemukan"
            )

            return ExecutionApprovalResult(
                allowed=False,
                execution_id=plan.execution_id,
                change_id=plan.change_id,
                approval_id=approval_id,
                payload_hash=payload_hash(plan.to_payload()),
                errors=tuple(errors),
                checked_rules=tuple(checked),
            )

        # ----------------------------------------------------------
        # 3. Approval status
        # ----------------------------------------------------------
        checked.append("approval_status")

        if approval.status != APPROVED:
            errors.append(
                f"approval status tidak APPROVED: {approval.status}"
            )

        # ----------------------------------------------------------
        # 4. Approval expiry
        # ----------------------------------------------------------
        checked.append("approval_expiry")

        now = datetime.now(timezone.utc)

        if approval.expires_at:
            expires_at = approval.expires_at

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(
                    tzinfo=timezone.utc
                )

            if now >= expires_at:
                errors.append("approval sudah expired")

        # ----------------------------------------------------------
        # 5. Payload hash
        # ----------------------------------------------------------
        checked.append("payload_hash_binding")

        current_hash = payload_hash(plan.to_payload())

        if approval.payload_hash != current_hash:
            errors.append(
                "payload ExecutionPlan berbeda dari approval"
            )

        # ----------------------------------------------------------
        # 6. Change ID binding
        # ----------------------------------------------------------
        checked.append("change_id_binding")

        approved_payload = self._approval_payload(approval)

        if approved_payload:
            approved_change_id = approved_payload.get(
                "change_id"
            )

            if approved_change_id != plan.change_id:
                errors.append(
                    "change_id berbeda dari approval"
                )

        # ----------------------------------------------------------
        # 7. Target file binding
        # ----------------------------------------------------------
        checked.append("target_file_binding")

        if approved_payload:
            approved_files = tuple(
                approved_payload.get(
                    "target_files",
                    [],
                )
            )

            if approved_files != plan.target_files:
                errors.append(
                    "target_files berbeda dari approval"
                )

        # ----------------------------------------------------------
        # 8. Plan approval flag
        # ----------------------------------------------------------
        checked.append("plan_approved_flag")

        if plan.approved is not True:
            errors.append(
                "ExecutionPlan approved flag belum True"
            )

        # ----------------------------------------------------------
        # 9. Status boundary
        # ----------------------------------------------------------
        checked.append("execution_status")

        if plan.status not in (
            BOUNDARY_VALIDATED,
            EXECUTABLE,
        ):
            errors.append(
                f"ExecutionPlan status tidak valid: {plan.status}"
            )

        # ----------------------------------------------------------
        # 10. Approval must not already be consumed
        # ----------------------------------------------------------
        checked.append("approval_replay_protection")

        if approval.status == CONSUMED:
            errors.append(
                "approval sudah consumed dan tidak dapat replay"
            )

        # ----------------------------------------------------------
        # FINAL
        # ----------------------------------------------------------

        return ExecutionApprovalResult(
            allowed=not errors,
            execution_id=plan.execution_id,
            change_id=plan.change_id,
            approval_id=approval_id,
            payload_hash=current_hash,
            errors=tuple(errors),
            checked_rules=tuple(checked),
        )

    def require_valid(
        self,
        plan: ExecutionPlan,
        approval_id: str,
    ) -> ExecutionApprovalResult:

        result = self.validate(
            plan,
            approval_id,
        )

        if not result.allowed:
            raise ExecutionApprovalError(
                "Execution Approval BLOCKED: "
                + "; ".join(result.errors)
            )

        return result

    @staticmethod
    def _approval_payload(approval) -> dict:
        """Extract canonical payload if available.

        ApprovalQueue stores the hash as its authoritative binding.
        Some queue implementations may expose payload directly;
        when unavailable, hash verification remains authoritative.
        """
        payload = getattr(approval, "payload", None)

        if isinstance(payload, dict):
            return payload

        return {}


__all__ = [
    "ExecutionApprovalResult",
    "ExecutionApprovalError",
    "ExecutionApprovalEnforcer",
]
