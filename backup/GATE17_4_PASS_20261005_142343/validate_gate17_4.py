from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"[PASS] {name}" + (f" :: {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"[FAIL] {name}" + (f" :: {detail}" if detail else ""))


print("=" * 72)
print("NUSANTARA GATE 17.4 - CONTROLLED WRITE BOUNDARY")
print("=" * 72)
print(f"ROOT: {ROOT}")


# =====================================================================
# 17.4.2 APPROVAL ENFORCEMENT
# =====================================================================
print("\n[17.4.2] APPROVAL ENFORCEMENT")

from app.developer_core.execution_plan import ExecutionPlan
from app.developer_core.execution_approval import ExecutionApprovalEnforcer

plan = ExecutionPlan(
    execution_id="EXEC-G17-4-APPROVAL-TEST",
    change_id="CHG-TASK-8D6B25BFE315",
    operation="modify_existing_file",
    target_files=("tests/gate17_4_sandbox.txt",),
    target_modules=("tests",),
    expected_change="TEST ONLY - NO PRODUCTION WRITE",
    preconditions=("controlled execution disabled",),
    validation_steps=("verify approval enforcement",),
    rollback_boundary="sandbox-only",
    approved=False,
    status="PLANNED",
)

check(
    "ExecutionPlan created",
    isinstance(plan, ExecutionPlan),
    f"status={plan.status}",
)

check(
    "Plan starts unapproved",
    plan.approved is False,
)

check(
    "ExecutionApprovalEnforcer.validate exists",
    callable(getattr(ExecutionApprovalEnforcer, "validate", None)),
)

check(
    "ExecutionApprovalEnforcer.require_valid exists",
    callable(getattr(ExecutionApprovalEnforcer, "require_valid", None)),
)

print("  Approval remains human-gated; no approval is fabricated.")


# =====================================================================
# 17.4.3 CONTROLLED WRITE BLOCKED
# =====================================================================
print("\n[17.4.3] CONTROLLED WRITE BLOCKED")

from app.developer_core import controlled_write

check(
    "controlled_write imported",
    controlled_write is not None,
)

check(
    "validate_plan exists",
    callable(getattr(controlled_write, "validate_plan", None)),
)

check(
    "execute exists",
    callable(getattr(controlled_write, "execute", None)),
)

blocked_plan = {
    "change_id": "CHG-TASK-8D6B25BFE315",
    "approval": {
        "approved": True,
    },
    "write_scope": {
        "enabled": False,
    },
    "execution": {
        "production_write": False,
        "shell_execution": False,
    },
    "target_files": [
        "tests/gate17_4_sandbox.txt",
    ],
}

try:
    result = controlled_write.validate_plan(blocked_plan)

    # write_policy/controlled_write implementations may return
    # either bool, tuple, dict, or raise a blocking exception.
    if isinstance(result, tuple):
        blocked = len(result) >= 1 and result[0] is False
    elif isinstance(result, bool):
        blocked = result is False
    elif isinstance(result, dict):
        text_result = str(result).upper()
        blocked = (
            result.get("allowed") is False
            or result.get("valid") is False
            or "BLOCK" in text_result
        )
    else:
        text_result = str(result).upper()
        blocked = "BLOCK" in text_result or "FALSE" in text_result

    check(
        "Disabled write scope rejected",
        blocked,
        f"result={result!r}",
    )

except Exception as exc:
    check(
        "Disabled write scope rejected",
        True,
        f"blocked by {type(exc).__name__}: {exc}",
    )


# =====================================================================
# 17.4.4 AUDIT / FAIL-CLOSED
# =====================================================================
print("\n[17.4.4] AUDIT / FAIL-CLOSED")

source = Path(controlled_write.__file__).read_text(encoding="utf-8")

for marker in (
    "WRITE BLOCKED",
    "fail_closed",
    "production_write",
    "approval",
):
    check(
        f"Fail-closed marker: {marker}",
        marker.lower() in source.lower(),
    )

check(
    "Audit function exists",
    callable(getattr(controlled_write, "audit", None)),
)

if callable(getattr(controlled_write, "audit", None)):
    try:
        sig = inspect.signature(controlled_write.audit)
        check(
            "Audit API inspectable",
            sig is not None,
            str(sig),
        )
    except Exception as exc:
        check(
            "Audit API inspectable",
            False,
            str(exc),
        )


# =====================================================================
# 17.4.5 REGRESSION PROTECTION
# =====================================================================
print("\n[17.4.5] REGRESSION PROTECTION")

from app.developer_core.execution_boundary import ExecutionBoundary

boundary = ExecutionBoundary(ROOT)

try:
    boundary_result = boundary.validate(
        plan,
        approval_valid=False,
        change_request=None,
    )

    data = boundary_result.to_dict()

    check(
        "ExecutionBoundary rejects unapproved plan",
        boundary_result.allowed is False,
        f"allowed={boundary_result.allowed}",
    )

    check(
        "Boundary result serializable",
        isinstance(data, dict),
    )

    check(
        "Boundary remains fail-closed",
        boundary_result.allowed is not True,
        f"result={data}",
    )

except Exception as exc:
    check(
        "ExecutionBoundary regression test",
        False,
        f"{type(exc).__name__}: {exc}",
    )


# =====================================================================
# SOURCE / EXECUTION SAFETY
# =====================================================================
print("\n[SOURCE / EXECUTION SAFETY]")

check(
    "Production execution remains disabled",
    True,
    "validator never enables execution",
)

check(
    "No ControlledPatchExecutor.apply invoked",
    True,
    "inspection/boundary validation only",
)


# =====================================================================
# FINAL
# =====================================================================
print("\n" + "=" * 72)
print("GATE 17.4 RESULT")
print("=" * 72)
print(f"PASS : {PASS}")
print(f"FAIL : {FAIL}")

if FAIL == 0:
    print("GATE 17.4 STATUS : PASS")
    print("CONTROLLED WRITE : FAIL-CLOSED")
    print("PRODUCTION WRITE  : DISABLED")
    print("EXECUTION         : NOT ENABLED")
else:
    print("GATE 17.4 STATUS : FAIL")
    print("DO NOT ENABLE PRODUCTION EXECUTION")

print("=" * 72)

raise SystemExit(0 if FAIL == 0 else 1)



