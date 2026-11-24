"""Nusantara V1 - Gate 16.1/16.2 Boundary Validator.

Validates:
    16.1 ExecutionPlan Schema
    16.2 Execution Boundary

IMPORTANT:
    This validator MUST NOT modify repository source files.
    No write / patch / delete / subprocess / shell execution.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.developer_core.execution_plan import (
    BLOCKED,
    BOUNDARY_VALIDATED,
    EXECUTABLE,
    PLANNED,
    ExecutionPlan,
)
from app.developer_core.execution_boundary import ExecutionBoundary


PASS = 0
FAIL = 0


def check(name: str, condition: bool) -> None:
    global PASS, FAIL

    if condition:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}")


def make_plan(
    *,
    execution_id: str = "ex-test",
    change_id: str = "cp-test",
    operation: str = "modify_existing_file",
    target_files: tuple[str, ...] = ("app/test.py",),
    approved: bool = False,
    status: str = PLANNED,
) -> ExecutionPlan:
    return ExecutionPlan(
        execution_id=execution_id,
        change_id=change_id,
        operation=operation,
        target_files=target_files,
        target_modules=("test_module",),
        expected_change="controlled test change",
        preconditions=("approval valid",),
        validation_steps=("validation test",),
        rollback_boundary="git checkpoint",
        approved=approved,
        status=status,
    )


def main() -> int:
    print("=" * 72)
    print("NUSANTARA GATE 16.1 / 16.2")
    print("EXECUTION PLAN + EXECUTION BOUNDARY")
    print("=" * 72)

    boundary = ExecutionBoundary(ROOT)

    # ==============================================================
    # 16.1 EXECUTION PLAN SCHEMA
    # ==============================================================

    print("\n[16.1] EXECUTION PLAN SCHEMA")
    print("-" * 72)

    # 16.1.1 Valid plan
    try:
        plan = make_plan()
        check(
            "16.1.1 Valid ExecutionPlan",
            plan.status == PLANNED
            and plan.approved is False,
        )
    except Exception:
        check("16.1.1 Valid ExecutionPlan", False)

    # 16.1.2 Required field rejection
    try:
        ExecutionPlan(
            execution_id="",
            change_id="cp-test",
            operation="modify_existing_file",
            target_files=("app/test.py",),
            target_modules=("test_module",),
            expected_change="test",
            preconditions=("approval",),
            validation_steps=("test",),
            rollback_boundary="checkpoint",
        )
        check("16.1.2 Required field rejection", False)
    except ValueError:
        check("16.1.2 Required field rejection", True)

    # 16.1.3 Invalid operation rejection
    try:
        ExecutionPlan(
            execution_id="ex-invalid",
            change_id="cp-test",
            operation="execute_shell",
            target_files=("app/test.py",),
            target_modules=("test_module",),
            expected_change="test",
            preconditions=("approval",),
            validation_steps=("test",),
            rollback_boundary="checkpoint",
        )
        check("16.1.3 Invalid operation rejection", False)
    except ValueError:
        check("16.1.3 Invalid operation rejection", True)

    # 16.1.4 Immutable payload
    try:
        plan = make_plan()
        payload = plan.to_payload()

        mutation_blocked = False

        try:
            plan.status = EXECUTABLE
        except Exception:
            mutation_blocked = True

        check(
            "16.1.4 Immutable ExecutionPlan",
            mutation_blocked
            and payload["status"] == PLANNED,
        )
    except Exception:
        check("16.1.4 Immutable ExecutionPlan", False)

    # 16.1.5 Invalid transition
    try:
        plan = make_plan()

        try:
            plan.transition(EXECUTABLE, approval_valid=True)
            transition_blocked = False
        except ValueError:
            transition_blocked = True

        check(
            "16.1.5 Invalid transition blocked",
            transition_blocked,
        )
    except Exception:
        check("16.1.5 Invalid transition blocked", False)

    # ==============================================================
    # 16.2 EXECUTION BOUNDARY
    # ==============================================================

    print("\n[16.2] EXECUTION BOUNDARY")
    print("-" * 72)

    # 16.2.1 Valid boundary
    try:
        plan = make_plan(
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        result = boundary.validate(
            plan,
            approval_valid=True,
        )

        check(
            "16.2.1 Valid boundary PASS",
            result.allowed is True
            and not result.errors,
        )
    except Exception:
        check("16.2.1 Valid boundary PASS", False)

    # 16.2.2 Path traversal
    try:
        plan = make_plan(
            target_files=("../secret.txt",),
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        result = boundary.validate(
            plan,
            approval_valid=True,
        )

        check(
            "16.2.2 Path traversal BLOCK",
            result.allowed is False,
        )
    except Exception:
        check("16.2.2 Path traversal BLOCK", False)

    # 16.2.3 Absolute path
    try:
        absolute_target = str(ROOT / "secret.txt")

        plan = make_plan(
            target_files=(absolute_target,),
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        result = boundary.validate(
            plan,
            approval_valid=True,
        )

        check(
            "16.2.3 Absolute path BLOCK",
            result.allowed is False,
        )
    except Exception:
        check("16.2.3 Absolute path BLOCK", False)

    # 16.2.4 Wildcard
    try:
        plan = make_plan(
            target_files=("app/*.py",),
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        result = boundary.validate(
            plan,
            approval_valid=True,
        )

        check(
            "16.2.4 Wildcard target BLOCK",
            result.allowed is False,
        )
    except Exception:
        check("16.2.4 Wildcard target BLOCK", False)

    # 16.2.5 Sensitive path
    try:
        plan = make_plan(
            target_files=(".env",),
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        result = boundary.validate(
            plan,
            approval_valid=True,
        )

        check(
            "16.2.5 Sensitive path BLOCK",
            result.allowed is False,
        )
    except Exception:
        check("16.2.5 Sensitive path BLOCK", False)

    # 16.2.6 Approval enforcement
    try:
        plan = make_plan(
            approved=False,
            status=BOUNDARY_VALIDATED,
        )

        result = boundary.validate(
            plan,
            approval_valid=False,
        )

        check(
            "16.2.6 Approval enforcement BLOCK",
            result.allowed is False,
        )
    except Exception:
        check("16.2.6 Approval enforcement BLOCK", False)

    # 16.2.7 ChangeRequest binding
    try:
        plan = make_plan(
            change_id="cp-A",
            target_files=("app/test.py",),
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        # Lightweight fake object: only fields required by boundary.
        class FakeChangeRequest:
            proposal_id = "cp-B"
            affected_files = ("app/test.py",)

        result = boundary.validate(
            plan,
            approval_valid=True,
            change_request=FakeChangeRequest(),
        )

        check(
            "16.2.7 ChangeRequest binding BLOCK",
            result.allowed is False,
        )
    except Exception:
        check("16.2.7 ChangeRequest binding BLOCK", False)

    # 16.2.8 Fail-closed require_allowed
    try:
        plan = make_plan(
            approved=False,
            status=BOUNDARY_VALIDATED,
        )

        blocked = False

        try:
            boundary.require_allowed(
                plan,
                approval_valid=False,
            )
        except PermissionError:
            blocked = True

        check(
            "16.2.8 Fail-closed boundary",
            blocked,
        )
    except Exception:
        check("16.2.8 Fail-closed boundary", False)

    # ==============================================================
    # FINAL
    # ==============================================================

    total = PASS + FAIL

    print("\n" + "=" * 72)
    print("GATE 16.1 / 16.2 FINAL")
    print("=" * 72)
    print(f"VALIDATION CHECKS : {total}")
    print(f"PASS              : {PASS}")
    print(f"FAIL              : {FAIL}")
    print("-" * 72)

    if FAIL == 0:
        print("GATE 16.1 / 16.2 : PASS")
        print("EXECUTION         : NOT ENABLED")
        return 0

    print("GATE 16.1 / 16.2 : FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
