import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.approval.queue import ApprovalQueue, ApprovalError
from app.developer_core.change_plan import (
    ChangePlan,
    PROPOSED,
    VALIDATED,
    APPROVED,
    READY,
)
from app.developer_core.change_plan_validator import (
    validate_change_plan,
    validate_transition,
)
from app.developer_core.change_plan_approval import (
    ChangePlanApprovalBinding,
    ChangePlanApprovalError,
)


def make_plan(change_id="gate15-final-001"):
    return ChangePlan(
        change_id=change_id,
        request="Gate 15 operational validation",
        scope="test-module",
        affected_files=("test.py",),
        affected_modules=("test_module",),
        affected_symbols=("test_function",),
        dependencies=(),
        dependents=(),
        directional_impact={"direction": "outbound"},
        risk_signals=("low",),
        evidence=("gate15-test-evidence",),
        validation_plan=("pytest",),
        rollback_boundary="git checkpoint",
    )


passed = 0
failed = 0


def check(name, condition):
    global passed, failed

    if condition:
        print(f"[PASS] {name}")
        passed += 1
    else:
        print(f"[FAIL] {name}")
        failed += 1


print("=" * 72)
print("NUSANTARA GATE 15 OPERATIONAL FINAL")
print("CHANGE PLAN + HUMAN APPROVAL BOUNDARY")
print("=" * 72)

plan = make_plan()

# 1
result = validate_change_plan(plan)
check("15.O.1 Valid ChangePlan", result.valid)

# 2
invalid = ChangePlan(
    change_id="gate15-invalid-001",
    request="invalid test",
    scope="test-module",
)
result = validate_change_plan(invalid)
check("15.O.2 Required fields rejected", not result.valid)

# 3
try:
    ChangePlan(
        change_id="gate15-invalid-002",
        request="approval bypass",
        scope="test-module",
        affected_files=("test.py",),
        affected_modules=("test_module",),
        risk_signals=("low",),
        evidence=("evidence",),
        validation_plan=("pytest",),
        rollback_boundary="git checkpoint",
        approval_required=False,
    )
    approval_disabled = True
except ValueError:
    approval_disabled = False

check("15.O.3 approval_required=True enforced", not approval_disabled)

# 4
invalid_transition = validate_transition(
    plan,
    READY,
    approval_valid=False,
)
check(
    "15.O.4 Invalid transition blocked",
    not invalid_transition.valid,
)

# 5
validated_plan = plan.transition(VALIDATED)

approval_transition = validate_transition(
    validated_plan,
    APPROVED,
    approval_valid=False,
)

check(
    "15.O.5 Approval required for APPROVED",
    not approval_transition.valid,
)

# 6
queue = ApprovalQueue()
binding = ChangePlanApprovalBinding(queue)

approval = binding.submit(
    validated_plan,
    requested_by="developer-a",
)

check(
    "15.O.6 Approval submitted as pending",
    approval.status == "pending",
)

# 7
binding_result = binding.binding(
    validated_plan,
    approval.approval_id,
)

check(
    "15.O.7 ChangePlan payload hash bound",
    binding_result.change_id == validated_plan.change_id,
)

# 8
try:
    binding.consume_to_change_request(
        validated_plan,
        approval.approval_id,
    )
    pending_blocked = False
except ChangePlanApprovalError:
    pending_blocked = True

check(
    "15.O.8 Pending approval blocked",
    pending_blocked,
)

# 9
try:
    queue.decide(
        approval.approval_id,
        reviewer="developer-a",
        decision="approved",
        reason="self approval",
    )
    self_approval_blocked = False
except ApprovalError:
    self_approval_blocked = True

check(
    "15.O.9 Requester cannot approve own request",
    self_approval_blocked,
)

# 10
approval = queue.decide(
    approval.approval_id,
    reviewer="reviewer-b",
    decision="approved",
    reason="Gate 15 operational test approval",
)

check(
    "15.O.10 Human approval recorded",
    approval.status == "approved",
)

# 11
changed_plan = ChangePlan(
    change_id=validated_plan.change_id,
    request="CHANGED AFTER APPROVAL",
    scope=validated_plan.scope,
    affected_files=validated_plan.affected_files,
    affected_modules=validated_plan.affected_modules,
    affected_symbols=validated_plan.affected_symbols,
    dependencies=validated_plan.dependencies,
    dependents=validated_plan.dependents,
    directional_impact=validated_plan.directional_impact,
    risk_signals=validated_plan.risk_signals,
    evidence=validated_plan.evidence,
    validation_plan=validated_plan.validation_plan,
    rollback_boundary=validated_plan.rollback_boundary,
)

try:
    binding.consume_to_change_request(
        changed_plan,
        approval.approval_id,
    )
    tamper_blocked = False
except ChangePlanApprovalError:
    tamper_blocked = True

check(
    "15.O.11 Payload tamper blocked",
    tamper_blocked,
)

# 12
change_request = binding.consume_to_change_request(
    validated_plan,
    approval.approval_id,
)

check(
    "15.O.12 Approved unchanged payload consumed",
    change_request.approval_id == approval.approval_id,
)

# 13
try:
    binding.consume_to_change_request(
        validated_plan,
        approval.approval_id,
    )
    replay_blocked = False
except ChangePlanApprovalError:
    replay_blocked = True

check(
    "15.O.13 Consumed approval cannot replay",
    replay_blocked,
)

# 14
check(
    "15.O.14 Audit chain verifies",
    queue.audit.verify(),
)

print("-" * 72)
print(f"VALIDATION CHECKS : {passed + failed}")
print(f"PASS              : {passed}")
print(f"FAIL              : {failed}")
print("-" * 72)

if failed == 0:
    print("GATE 15 OPERATIONAL FINAL : PASS")
    sys.exit(0)

print("GATE 15 OPERATIONAL FINAL : FAIL")
sys.exit(1)
