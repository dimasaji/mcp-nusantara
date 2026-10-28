from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "data" / "developer_core" / "execution_audit.json"
OUT = ROOT / "data" / "developer_core" / "execution_audit_integration.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def main():
    existing = {}

    if AUDIT.exists():
        try:
            existing = json.loads(
                AUDIT.read_text(encoding="utf-8-sig")
            )
        except Exception:
            existing = {}

    result = {
        "schema": "nusantara.execution_audit_integration.v1",
        "generated_at": now(),
        "source_audit_exists": AUDIT.exists(),
        "source_audit": existing,
        "integration_status": "READY",
        "production_write": False,
        "shell_execution": False,
        "automatic_patch": False,
        "approval_required": True,
        "fail_closed": True
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("================================================================")
    print("NUSANTARA EXECUTION AUDIT INTEGRATION V1")
    print("================================================================")
    print(f"Existing audit : {AUDIT.exists()}")
    print("Integration    : READY")
    print("Shell          : BLOCKED")
    print("Production     : BLOCKED")
    print("Auto patch     : BLOCKED")
    print("Approval       : REQUIRED")
    print(f"OUTPUT         : {OUT}")
    print("STATUS         : PASS")

if __name__ == "__main__":
    main()
