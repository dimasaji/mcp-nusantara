from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

CHANGE = ROOT / "data" / "developer_core" / "change_plan.json"
OUT = ROOT / "data" / "developer_core" / "approval_result.json"

FORBIDDEN = {
    ".git",
    ".env",
    ".venv",
    "venv",
    ".developer_staging",
    "data/production",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    if not path.exists():
        raise RuntimeError(f"BLOCKED: file tidak ditemukan: {path}")

    return json.loads(
        path.read_text(encoding="utf-8-sig")
    )


def write_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


def normalize(path):
    return str(path).replace("\\", "/").strip().lstrip("./")


def is_forbidden(path):
    value = normalize(path).lower()

    for blocked in FORBIDDEN:
        blocked = blocked.lower()

        if (
            value == blocked
            or value.startswith(blocked + "/")
        ):
            return True

    return False


def validate_plan(plan):
    required = [
        "change_id",
        "objective",
        "status",
        "candidate_files",
        "allowed_files",
        "execution",
        "write_scope",
        "fail_closed",
    ]

    missing = [
        key for key in required
        if key not in plan
    ]

    if missing:
        raise RuntimeError(
            "BLOCKED: field change plan hilang: "
            + ", ".join(missing)
        )

    if plan.get("fail_closed") is not True:
        raise RuntimeError(
            "BLOCKED: fail_closed harus True."
        )

    if plan.get("status") != "APPROVAL_REQUIRED":
        raise RuntimeError(
            "BLOCKED: status bukan APPROVAL_REQUIRED."
        )

    candidate = plan.get("candidate_files", [])
    allowed = plan.get("allowed_files", [])

    if not isinstance(candidate, list) or not candidate:
        raise RuntimeError(
            "BLOCKED: candidate_files kosong."
        )

    if not isinstance(allowed, list) or not allowed:
        raise RuntimeError(
            "BLOCKED: allowed_files kosong."
        )

    candidate = [
        normalize(x)
        for x in candidate
        if isinstance(x, str) and x.strip()
    ]

    allowed = [
        normalize(x)
        for x in allowed
        if isinstance(x, str) and x.strip()
    ]

    if set(allowed) != set(candidate):
        raise RuntimeError(
            "BLOCKED: allowed_files harus sama dengan candidate_files."
        )

    forbidden = [
        x for x in allowed
        if is_forbidden(x)
    ]

    if forbidden:
        raise RuntimeError(
            "BLOCKED: forbidden path terdeteksi: "
            + ", ".join(forbidden)
        )

    execution = plan.get("execution", {})

    if execution.get("shell_execution") is not False:
        raise RuntimeError(
            "BLOCKED: shell_execution harus False."
        )

    if execution.get("production_write") is not False:
        raise RuntimeError(
            "BLOCKED: production_write harus False."
        )

    if execution.get("automatic_patch") is not False:
        raise RuntimeError(
            "BLOCKED: automatic_patch harus False."
        )

    write_scope = plan.get("write_scope", {})

    if write_scope.get("enabled") is not False:
        raise RuntimeError(
            "BLOCKED: write_scope harus False sebelum approval."
        )

    return candidate


def approve():
    plan = read_json(CHANGE)

    candidate = validate_plan(plan)

    plan["status"] = "APPROVED"

    plan["approval"] = {
        "required": True,
        "approved": True,
        "approved_by": "HUMAN",
        "approved_at": now()
    }

    plan["write_scope"] = {
        "enabled": True,
        "allowed_files": candidate
    }

    write_json(CHANGE, plan)

    result = {
        "schema": "nusantara.approval_result.v1",
        "timestamp": now(),
        "action": "APPROVE",
        "change_id": plan["change_id"],
        "status": "APPROVED",
        "approved": True,
        "approved_by": "HUMAN",
        "write_enabled": True,
        "allowed_files": candidate,
        "shell_execution": False,
        "production_write": False,
        "automatic_patch": False,
        "fail_closed": True
    }

    write_json(OUT, result)

    print("=" * 64)
    print("NUSANTARA APPROVAL CONTROLLER V2")
    print("=" * 64)
    print("Action           : APPROVE")
    print(f"Change ID        : {plan['change_id']}")
    print("Status           : APPROVED")
    print("Approved by      : HUMAN")
    print("Write scope      : ENABLED")
    print(f"Allowed files    : {len(candidate)}")
    print("Shell            : BLOCKED")
    print("Production       : BLOCKED")
    print("Automatic patch  : BLOCKED")
    print("Fail-closed      : ENABLED")
    print(f"OUTPUT           : {OUT}")
    print("STATUS           : APPROVED")


def reject():
    plan = read_json(CHANGE)

    plan["status"] = "REJECTED"

    plan["approval"] = {
        "required": True,
        "approved": False,
        "approved_by": "HUMAN",
        "approved_at": now()
    }

    plan["write_scope"] = {
        "enabled": False
    }

    write_json(CHANGE, plan)

    result = {
        "schema": "nusantara.approval_result.v1",
        "timestamp": now(),
        "action": "REJECT",
        "change_id": plan["change_id"],
        "status": "REJECTED",
        "approved": False,
        "write_enabled": False,
        "shell_execution": False,
        "production_write": False,
        "automatic_patch": False,
        "fail_closed": True
    }

    write_json(OUT, result)

    print("=" * 64)
    print("NUSANTARA APPROVAL CONTROLLER V2")
    print("=" * 64)
    print("Action           : REJECT")
    print(f"Change ID        : {plan['change_id']}")
    print("Status           : REJECTED")
    print("Write scope      : DISABLED")
    print("Shell            : BLOCKED")
    print("Production       : BLOCKED")
    print("Automatic patch  : BLOCKED")
    print("Fail-closed      : ENABLED")
    print(f"OUTPUT           : {OUT}")


def status():
    plan = read_json(CHANGE)

    print("=" * 64)
    print("NUSANTARA APPROVAL CONTROLLER V2")
    print("=" * 64)
    print(f"Change ID        : {plan.get('change_id')}")
    print(f"Status           : {plan.get('status')}")

    approval = plan.get("approval", {})
    write_scope = plan.get("write_scope", {})
    execution = plan.get("execution", {})

    print(
        f"Approved         : "
        f"{approval.get('approved', False)}"
    )

    print(
        f"Approved by      : "
        f"{approval.get('approved_by')}"
    )

    print(
        f"Write scope      : "
        f"{write_scope.get('enabled', False)}"
    )

    print(
        f"Allowed files    : "
        f"{len(plan.get('allowed_files', []))}"
    )

    print(
        f"Shell            : "
        f"{'BLOCKED' if execution.get('shell_execution') is False else 'ENABLED'}"
    )

    print(
        f"Production       : "
        f"{'BLOCKED' if execution.get('production_write') is False else 'ENABLED'}"
    )

    print(
        f"Automatic patch  : "
        f"{'BLOCKED' if execution.get('automatic_patch') is False else 'ENABLED'}"
    )

    print(
        f"Fail-closed      : "
        f"{plan.get('fail_closed')}"
    )


def main():
    import sys

    command = (
        sys.argv[1].lower()
        if len(sys.argv) > 1
        else "status"
    )

    if command == "status":
        status()

    elif command == "approve":
        approve()

    elif command == "reject":
        reject()

    else:
        print(
            "Usage: "
            "python .\\app\\developer_core\\approval_controller.py "
            "[status|approve|reject]"
        )


if __name__ == "__main__":
    main()
