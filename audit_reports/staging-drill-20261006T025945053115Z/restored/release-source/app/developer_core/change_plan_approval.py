"""Nusantara V1 - Gate 15 Operational Approval Binding.

ChangePlan -> ApprovalQueue -> Human Approval -> ChangeRequest.

Approval menggunakan payload ChangePlan secara langsung sehingga
payload hash benar-benar mengikat ChangePlan yang disetujui.
Tidak melakukan patch/write/execute.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.approval.change_request import ChangeRequest
from app.approval.queue import APPROVED, ApprovalQueue, ApprovalRequest, payload_hash
from app.developer_core.change_plan import ChangePlan
from app.developer_core.change_plan_validator import validate_change_plan


class ChangePlanApprovalError(PermissionError):
    """Approval ChangePlan tidak memenuhi kontrak."""


@dataclass(frozen=True)
class ChangePlanApproval:
    change_id: str
    approval_id: str
    payload_hash: str
    risk: str


class ChangePlanApprovalBinding:
    """Boundary approval untuk ChangePlan."""

    def __init__(self, queue: ApprovalQueue):
        self.queue = queue

    def submit(
        self,
        plan: ChangePlan,
        *,
        requested_by: str,
    ) -> ApprovalRequest:
        """Submit payload ChangePlan secara langsung ke ApprovalQueue."""
        result = validate_change_plan(plan)

        if not result.valid:
            raise ChangePlanApprovalError(
                "ChangePlan tidak valid: " + "; ".join(result.errors)
            )

        if plan.approval_required is not True:
            raise ChangePlanApprovalError(
                "approval_required harus True"
            )

        risk = _effective_risk(plan)
        payload = plan.to_payload()

        return self.queue.submit(
            "change_plan",
            payload,
            risk=risk,
            requested_by=requested_by,
            summary={
                "change_id": plan.change_id,
                "request": plan.request[:200],
                "scope": plan.scope[:200],
                "affected_files": list(plan.affected_files),
                "rollback_boundary": plan.rollback_boundary[:300],
            },
        )

    def binding(self, plan: ChangePlan, approval_id: str) -> ChangePlanApproval:
        """Verifikasi bahwa approval memang milik ChangePlan ini."""
        req = self.queue.get(approval_id)

        if req is None:
            raise ChangePlanApprovalError("approval tidak ditemukan")

        expected_hash = payload_hash(plan.to_payload())

        if req.payload_hash != expected_hash:
            raise ChangePlanApprovalError(
                "payload ChangePlan berbeda dari payload yang disetujui"
            )

        return ChangePlanApproval(
            change_id=plan.change_id,
            approval_id=req.approval_id,
            payload_hash=expected_hash,
            risk=req.risk,
        )

    def consume_to_change_request(
        self,
        plan: ChangePlan,
        approval_id: str,
    ) -> ChangeRequest:
        """Consume approval satu kali dan menghasilkan ChangeRequest."""
        req = self.queue.get(approval_id)

        if req is None:
            raise ChangePlanApprovalError("approval tidak ditemukan")

        if req.status != APPROVED:
            raise ChangePlanApprovalError(
                f"approval belum approved: {req.status}"
            )

        payload = plan.to_payload()

        if req.payload_hash != payload_hash(payload):
            raise ChangePlanApprovalError(
                "payload ChangePlan berbeda dari payload yang disetujui"
            )

        if not self.queue.consume(approval_id, payload):
            raise ChangePlanApprovalError(
                "approval tidak dapat digunakan"
            )

        return ChangeRequest(
            change_request_id=f"cr-{plan.change_id}",
            proposal_id=plan.change_id,
            approval_id=req.approval_id,
            reviewer=req.reviewer or "",
            decision_reason=req.reason or "",
            affected_files=list(plan.affected_files),
            risk=req.risk,
            rollback_plan=plan.rollback_boundary,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="open",
        )


def _effective_risk(plan: ChangePlan) -> str:
    """Risk level deterministic dari risk_signals."""
    levels = ("low", "medium", "high", "critical")

    found = [
        signal.strip().lower()
        for signal in plan.risk_signals
        if isinstance(signal, str)
        and signal.strip().lower() in levels
    ]

    if not found:
        raise ChangePlanApprovalError(
            "ChangePlan tidak memiliki risk level valid"
        )

    return max(found, key=levels.index)


__all__ = [
    "ChangePlanApproval",
    "ChangePlanApprovalBinding",
    "ChangePlanApprovalError",
]
