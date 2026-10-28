from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.approval.audit_trail import AuditTrail
from app.approval.queue import ApprovalQueue, APPROVED, CONSUMED
from app.developer_core.change_plan import ChangePlan
from app.developer_core.execution_plan import (
    ExecutionPlan,
    BOUNDARY_VALIDATED,
)
from app.developer_core.execution_approval import (
    ExecutionApprovalEnforcer,
)
from dataclasses import replace


def make_plan():
    return ExecutionPlan(
        execution_id="exec-gate16-003",
        change_id="change-gate16-003",
        operation="modify_existing_file",
        target_files=("app/developer_core/test_target.py",),
        target_modules=("app.developer_core",),
        expected_change="ubah implementasi test secara terkontrol",
        preconditions=("target file harus ada",),
        validation_steps=("python syntax validation",),
        rollback_boundary="hanya target_files",
        approved=True,
        status=BOUNDARY_VALIDATED,
    )


def main():
    print("=" * 72)
    print("NUSANTARA GATE 16.3")
    print("EXECUTION APPROVAL ENFORCEMENT")
    print("=" * 72)

    audit = AuditTrail()
    queue = ApprovalQueue(audit)
    enforcer = ExecutionApprovalEnforcer(queue)

    # ------------------------------------------------------------
    # 16.3.1 VALID EXECUTION PLAN
    # ------------------------------------------------------------
    plan = make_plan()

    assert plan.approved is True
    assert plan.status == BOUNDARY_VALIDATED

    print("[PASS] 16.3.1 Valid ExecutionPlan")

    # ------------------------------------------------------------
    # 16.3.2 SUBMIT EXACT PAYLOAD
    # ------------------------------------------------------------
    approval = queue.submit(
        kind="execution_plan",
        payload=plan.to_payload(),
        summary="Gate 16.3 execution approval test",
        risk="medium",
        requested_by="developer-core",
    )

    print("[PASS] 16.3.2 Approval submitted")

    # ------------------------------------------------------------
    # 16.3.3 PENDING MUST BLOCK
    # ------------------------------------------------------------
    result = enforcer.validate(
        plan,
        approval.approval_id,
    )

    assert result.allowed is False
    assert any(
        "APPROVED" in e
        for e in result.errors
    )

    print("[PASS] 16.3.3 Pending approval blocked")

    # ------------------------------------------------------------
    # 16.3.4 HUMAN APPROVAL
    # ------------------------------------------------------------
    decided = queue.decide(
        approval.approval_id,
        decision="approved",
        reviewer="human-reviewer",
        reason="Approved for controlled execution test",
    )

    assert decided.status == APPROVED

    print("[PASS] 16.3.4 Human approval recorded")

    # ------------------------------------------------------------
    # 16.3.5 EXACT PAYLOAD MUST PASS
    # ------------------------------------------------------------
    result = enforcer.validate(
        plan,
        approval.approval_id,
    )

    assert result.allowed is True
    assert result.errors == ()

    print("[PASS] 16.3.5 Exact approved payload accepted")

    # ------------------------------------------------------------
    # 16.3.6 TAMPERED PLAN MUST BLOCK
    # ------------------------------------------------------------
    tampered = replace(
        plan,
        expected_change="PERUBAHAN TIDAK DISETUJUI",
    )

    result = enforcer.validate(
        tampered,
        approval.approval_id,
    )

    assert result.allowed is False
    assert any(
        "payload" in e.lower()
        for e in result.errors
    )

    print("[PASS] 16.3.6 Payload tampering blocked")

    # ------------------------------------------------------------
    # 16.3.7 TARGET FILE TAMPERING MUST BLOCK
    # ------------------------------------------------------------
    tampered_files = replace(
        plan,
        target_files=("app/developer_core/OTHER.py",),
    )

    result = enforcer.validate(
        tampered_files,
        approval.approval_id,
    )

    assert result.allowed is False

    print("[PASS] 16.3.7 Target file tampering blocked")

    # ------------------------------------------------------------
    # 16.3.8 APPROVED FLAG FALSE MUST BLOCK
    # ------------------------------------------------------------
    unapproved_plan = replace(
        plan,
        approved=False,
    )

    result = enforcer.validate(
        unapproved_plan,
        approval.approval_id,
    )

    assert result.allowed is False

    print("[PASS] 16.3.8 approved=False blocked")

    # ------------------------------------------------------------
    # 16.3.9 INVALID STATUS MUST BLOCK
    # ------------------------------------------------------------
    planned_plan = replace(
        plan,
        status="PLANNED",
    )

    result = enforcer.validate(
        planned_plan,
        approval.approval_id,
    )

    assert result.allowed is False

    print("[PASS] 16.3.9 Invalid execution status blocked")

    # ------------------------------------------------------------
    # 16.3.10 CONSUME APPROVAL
    # ------------------------------------------------------------
    consumed = queue.consume(
        approval.approval_id,
        plan.to_payload(),
    )

    assert consumed is True

    print("[PASS] 16.3.10 Approval consumed")

    # ------------------------------------------------------------
    # 16.3.11 REPLAY MUST BLOCK
    # ------------------------------------------------------------
    result = enforcer.validate(
        plan,
        approval.approval_id,
    )

    assert result.allowed is False
    assert any(
        "consumed" in e.lower()
        for e in result.errors
    )

    print("[PASS] 16.3.11 Approval replay blocked")

    # ------------------------------------------------------------
    # AUDIT
    # ------------------------------------------------------------
    assert audit.verify() is True

    print("[PASS] 16.3.12 Audit chain verifies")

    print("-" * 72)
    print("VALIDATION CHECKS : 12")
    print("PASS              : 12")
    print("FAIL              : 0")
    print("-" * 72)
    print("GATE 16.3 FINAL   : PASS")
    print("EXECUTION         : NOT ENABLED")
    print("=" * 72)


if __name__ == "__main__":
    main()




