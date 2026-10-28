from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
CHANGE = ROOT / "data" / "developer_core" / "change_plan.json"

FORBIDDEN = [
    ".git",
    ".env",
    "data/production"
]

def normalize(p):
    return str(p).replace("\\", "/").strip("/").lower()

def validate_file(path):
    p = normalize(path)

    for forbidden in FORBIDDEN:
        f = normalize(forbidden)
        if p == f or p.startswith(f + "/"):
            return False, "FORBIDDEN_PATH"

    return True, "OK"

def validate(plan):
    if plan.get("status") != "APPROVAL_REQUIRED":
        return False, "INVALID_INITIAL_STATE"

    approval = plan.get("approval", {})

    if approval.get("approved") is not False:
        return False, "APPROVAL_STATE_INVALID"

    write_scope = plan.get("write_scope", {})

    if write_scope.get("enabled") is not False:
        return False, "WRITE_SCOPE_MUST_BE_DISABLED"

    if plan.get("execution", {}).get("shell_execution") is not False:
        return False, "SHELL_EXECUTION_MUST_BE_BLOCKED"

    if plan.get("execution", {}).get("production_write") is not False:
        return False, "PRODUCTION_WRITE_MUST_BE_BLOCKED"

    for path in plan.get("allowed_files", []):
        ok, reason = validate_file(path)
        if not ok:
            return False, f"{reason}: {path}"

    return True, "PASS"

if __name__ == "__main__":
    if not CHANGE.exists():
        print("CHANGE PLAN NOT FOUND")
        raise SystemExit(1)

    plan = json.loads(CHANGE.read_text(encoding="utf-8-sig"))
    ok, reason = validate(plan)

    print("=" * 64)
    print("NUSANTARA CONTROLLED WRITE POLICY VALIDATOR")
    print("=" * 64)
    print("Result :", reason)

    if ok:
        print("STATUS : PASS")
        print("Write  : NOT ACTIVE")
        print("Approval: REQUIRED")
        raise SystemExit(0)

    print("STATUS : FAIL-CLOSED")
    raise SystemExit(1)

