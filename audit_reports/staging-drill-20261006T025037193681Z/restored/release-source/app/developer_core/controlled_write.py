from pathlib import Path
import json
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "developer_core"
STAGING = ROOT / ".developer_staging"
CHANGE_FILE = DATA / "change_plan.json"
AUDIT_FILE = DATA / "execution_audit.json"

FORBIDDEN = [
    ".git",
    ".env",
    ".venv",
    "venv",
    "data/production",
    ".developer_staging"
]

def norm(value):
    return str(value).replace("\\", "/").strip("/").lower()

def is_forbidden(relative_path):
    p = norm(relative_path)

    for item in FORBIDDEN:
        f = norm(item)
        if p == f or p.startswith(f + "/"):
            return True

    return False

def safe_relative(path):
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
        return relative
    except ValueError:
        return None

def load_plan():
    if not CHANGE_FILE.exists():
        raise RuntimeError("CHANGE PLAN NOT FOUND")

    try:
        return json.loads(CHANGE_FILE.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"INVALID CHANGE PLAN: {exc}")

def validate_plan(plan):
    if plan.get("status") != "APPROVED":
        raise RuntimeError(
            "WRITE BLOCKED: change plan is not APPROVED"
        )

    approval = plan.get("approval", {})

    if approval.get("approved") is not True:
        raise RuntimeError(
            "WRITE BLOCKED: explicit approval is required"
        )

    scope = plan.get("write_scope", {})

    if scope.get("enabled") is not True:
        raise RuntimeError(
            "WRITE BLOCKED: write scope is not enabled"
        )

    execution = plan.get("execution", {})

    if execution.get("shell_execution") is not False:
        raise RuntimeError(
            "WRITE BLOCKED: shell execution must remain disabled"
        )

    if execution.get("production_write") is not False:
        raise RuntimeError(
            "WRITE BLOCKED: production write must remain disabled"
        )

    allowed = plan.get("allowed_files", [])

    if not isinstance(allowed, list) or not allowed:
        raise RuntimeError(
            "WRITE BLOCKED: allowed_files is empty"
        )

    for item in allowed:
        if is_forbidden(item):
            raise RuntimeError(
                f"WRITE BLOCKED: forbidden path in scope: {item}"
            )

def build_staging(change_id):
    return STAGING / change_id

def validate_staging(plan, staging):
    allowed = {
        norm(x): x
        for x in plan.get("allowed_files", [])
    }

    if not staging.exists():
        raise RuntimeError(
            f"STAGING NOT FOUND: {staging}"
        )

    staged_files = []

    for source in staging.rglob("*"):
        if not source.is_file():
            continue

        relative = source.relative_to(staging)
        relative_norm = norm(relative)

        if relative_norm not in allowed:
            raise RuntimeError(
                f"WRITE BLOCKED: staged file outside approved scope: "
                f"{relative}"
            )

        if is_forbidden(relative):
            raise RuntimeError(
                f"WRITE BLOCKED: forbidden staged path: {relative}"
            )

        staged_files.append(relative)

    if not staged_files:
        raise RuntimeError(
            "WRITE BLOCKED: staging contains no files"
        )

    return staged_files

def execute(plan, staging, files):
    changed = []

    for relative in files:
        source = staging / relative
        destination = ROOT / relative

        safe = safe_relative(destination)

        if safe is None:
            raise RuntimeError(
                f"WRITE BLOCKED: destination outside repository: {relative}"
            )

        if is_forbidden(safe):
            raise RuntimeError(
                f"WRITE BLOCKED: forbidden destination: {relative}"
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

        changed.append(str(relative).replace("\\", "/"))

    return changed

def audit(change_id, result, files=None, reason=None):
    payload = {
        "schema": "nusantara-controlled-write-audit-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "change_id": change_id,
        "result": result,
        "files_changed": files or [],
        "reason": reason,
        "production_write": False,
        "shell_execution": False,
        "automatic_patch": False,
        "fail_closed": True
    }

    AUDIT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def main():
    print("=" * 68)
    print("NUSANTARA CONTROLLED WRITE EXECUTOR V1")
    print("=" * 68)

    try:
        plan = load_plan()
        change_id = plan.get("change_id")

        if not change_id or change_id == "CHG-PENDING":
            raise RuntimeError(
                "WRITE BLOCKED: invalid change_id"
            )

        validate_plan(plan)

        staging = build_staging(change_id)

        files = validate_staging(plan, staging)

        print(f"Change ID        : {change_id}")
        print(f"Approval         : APPROVED")
        print(f"Staging          : {staging}")
        print(f"Files requested  : {len(files)}")

        changed = execute(plan, staging, files)

        audit(
            change_id,
            "PASS",
            changed
        )

        print()
        print("FILES WRITTEN:")
        for item in changed:
            print(f"  [WRITE] {item}")

        print()
        print("Production write : BLOCKED")
        print("Shell execution  : BLOCKED")
        print("Unrestricted     : BLOCKED")
        print("Audit            : WRITTEN")
        print()
        print("CONTROLLED WRITE : PASS")

        return 0

    except Exception as exc:
        change_id = "UNKNOWN"

        try:
            if CHANGE_FILE.exists():
                plan = json.loads(
                    CHANGE_FILE.read_text(encoding="utf-8-sig")
                )
                change_id = plan.get(
                    "change_id",
                    "UNKNOWN"
                )
        except Exception:
            pass

        audit(
            change_id,
            "BLOCKED",
            reason=str(exc)
        )

        print()
        print(f"BLOCKED: {exc}")
        print("FAIL-CLOSED : ENABLED")

        return 1

if __name__ == "__main__":
    raise SystemExit(main())

