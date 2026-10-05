from pathlib import Path
import json
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "developer_core"
CHANGE = DATA / "change_plan.json"
AUDIT = DATA / "approval_audit.json"

FORBIDDEN = {
    ".git", ".env", ".venv", "venv",
    "data/production", ".developer_staging"
}

def now():
    return datetime.now(timezone.utc).isoformat()

def load_plan():
    if not CHANGE.exists():
        raise RuntimeError("CHANGE PLAN NOT FOUND")
    try:
        return json.loads(CHANGE.read_text(encoding="utf-8-sig"))
    except Exception as e:
        raise RuntimeError(f"INVALID CHANGE PLAN: {e}")

def safe_path(path):
    p = path.replace("\\", "/").strip().lstrip("./")
    for forbidden in FORBIDDEN:
        f = forbidden.replace("\\", "/")
        if p == f or p.startswith(f + "/"):
            return False
    return bool(p) and not p.startswith("/")

def validate(plan):
    required = [
        "schema",
        "change_id",
        "status",
        "allowed_files",
        "approval",
        "write_scope",
        "execution",
    ]

    for key in required:
        if key not in plan:
            raise RuntimeError(f"INVALID CHANGE PLAN: missing {key}")

    change_id = str(plan.get("change_id", "")).strip()

    if not change_id or change_id == "CHG-PENDING":
        raise RuntimeError("INVALID CHANGE ID")

    allowed = plan.get("allowed_files", [])

    if not isinstance(allowed, list) or not allowed:
        raise RuntimeError("NO ALLOWED FILES")

    for path in allowed:
        if not isinstance(path, str) or not safe_path(path):
            raise RuntimeError(f"UNSAFE ALLOWED FILE: {path}")

    execution = plan.get("execution", {})
    if execution.get("shell_execution") is not False:
        raise RuntimeError("SHELL EXECUTION MUST REMAIN BLOCKED")
    if execution.get("production_write") is not False:
        raise RuntimeError("PRODUCTION WRITE MUST REMAIN BLOCKED")
    if execution.get("automatic_patch") is not False:
        raise RuntimeError("AUTOMATIC PATCH MUST REMAIN BLOCKED")

    return True

def audit(plan, action, result, reason):
    DATA.mkdir(parents=True, exist_ok=True)

    record = {
        "schema": "nusantara.approval_audit.v1",
        "timestamp": now(),
        "change_id": plan.get("change_id"),
        "action": action,
        "result": result,
        "reason": reason,
        "approval_required": True,
        "shell_execution": False,
        "production_write": False,
        "automatic_patch": False,
        "fail_closed": True,
    }

    AUDIT.write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def approve():
    plan = load_plan()
    validate(plan)

    if plan.get("status") != "APPROVAL_REQUIRED":
        raise RuntimeError(
            f"APPROVAL BLOCKED: current status is {plan.get('status')}"
        )

    plan["status"] = "APPROVED"

    approval = plan.setdefault("approval", {})
    approval["required"] = True
    approval["approved"] = True
    approval["approved_by"] = "HUMAN"
    approval["approved_at"] = now()

    scope = plan.setdefault("write_scope", {})
    scope["enabled"] = True
    scope["reason"] = "Explicit human approval."

    CHANGE.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    audit(plan, "APPROVE", "PASS", "Explicit human approval granted.")

    print("================================================================")
    print("NUSANTARA APPROVAL CONTROLLER V1")
    print("================================================================")
    print(f"CHANGE ID       : {plan['change_id']}")
    print("ACTION          : APPROVE")
    print("STATUS          : APPROVED")
    print("WRITE SCOPE     : ENABLED")
    print("SHELL EXECUTION : BLOCKED")
    print("PRODUCTION WRITE: BLOCKED")
    print("AUTOMATIC PATCH : BLOCKED")
    print("FAIL-CLOSED     : ENABLED")
    print("RESULT          : PASS")

def reject():
    plan = load_plan()
    validate(plan)

    plan["status"] = "REJECTED"

    approval = plan.setdefault("approval", {})
    approval["required"] = True
    approval["approved"] = False
    approval["approved_by"] = "HUMAN"
    approval["approved_at"] = now()

    scope = plan.setdefault("write_scope", {})
    scope["enabled"] = False
    scope["reason"] = "Human approval rejected."

    CHANGE.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    audit(plan, "REJECT", "PASS", "Explicit human rejection.")

    print("================================================================")
    print("NUSANTARA APPROVAL CONTROLLER V1")
    print("================================================================")
    print(f"CHANGE ID       : {plan['change_id']}")
    print("ACTION          : REJECT")
    print("STATUS          : REJECTED")
    print("WRITE SCOPE     : DISABLED")
    print("SHELL EXECUTION : BLOCKED")
    print("PRODUCTION WRITE: BLOCKED")
    print("AUTOMATIC PATCH : BLOCKED")
    print("FAIL-CLOSED     : ENABLED")
    print("RESULT          : PASS")

def status():
    plan = load_plan()
    validate(plan)

    print("================================================================")
    print("NUSANTARA APPROVAL CONTROLLER V1")
    print("================================================================")
    print(f"CHANGE ID       : {plan['change_id']}")
    print(f"STATUS          : {plan['status']}")
    print(f"APPROVED        : {plan['approval'].get('approved')}")
    print(f"WRITE SCOPE     : {plan['write_scope'].get('enabled')}")
    print("SHELL EXECUTION : BLOCKED")
    print("PRODUCTION WRITE: BLOCKED")
    print("AUTOMATIC PATCH : BLOCKED")
    print("FAIL-CLOSED     : ENABLED")

def main():
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "status"

    try:
        if command == "approve":
            approve()
        elif command == "reject":
            reject()
        elif command == "status":
            status()
        else:
            raise RuntimeError(
                "Usage: approval_controller.py [status|approve|reject]"
            )

    except Exception as e:
        print("================================================================")
        print("NUSANTARA APPROVAL CONTROLLER V1")
        print("================================================================")
        print(f"BLOCKED: {e}")
        print("WRITE SCOPE     : DISABLED")
        print("SHELL EXECUTION : BLOCKED")
        print("PRODUCTION WRITE: BLOCKED")
        print("AUTOMATIC PATCH : BLOCKED")
        print("FAIL-CLOSED     : ENABLED")
        print("RESULT          : FAIL-CLOSED")
        sys.exit(1)

if __name__ == "__main__":
    main()
