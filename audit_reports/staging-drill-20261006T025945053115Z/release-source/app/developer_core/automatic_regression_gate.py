from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "data" / "validation" / "nusantara_validation_report.json"
OUT = ROOT / "data" / "developer_core" / "regression" / "regression_result.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def main():
    checks = {
        "validation_report_exists": REPORT.exists()
    }

    report = {}

    if REPORT.exists():
        try:
            report = json.loads(
                REPORT.read_text(encoding="utf-8-sig")
            )
        except Exception as e:
            checks["validation_report_valid"] = False
            report = {"error": str(e)}
        else:
            checks["validation_report_valid"] = True

    text = json.dumps(report).upper()

    checks["master_pass"] = (
        "NUSANTARA MASTER : PASS" in text
        or report.get("master_status") == "PASS"
        or report.get("status") == "PASS"
    )

    checks["no_fail"] = (
        "FAIL" not in text
        or "FAIL-CLOSED" in text
    )

    result = all(checks.values())

    output = {
        "schema": "nusantara.regression_result.v1",
        "generated_at": now(),
        "result": "PASS" if result else "BLOCKED",
        "checks": checks,
        "gate_scope": "Gate 7-17",
        "automatic_patch": False,
        "shell_execution": False,
        "production_write": False,
        "approval_required": True,
        "fail_closed": True
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("================================================================")
    print("NUSANTARA AUTOMATIC REGRESSION GATE V1")
    print("================================================================")
    print(f"Validation report : {REPORT.exists()}")
    print(f"Master regression : {'PASS' if result else 'BLOCKED'}")
    print("Scope             : Gate 7-17")
    print("Automatic patch   : BLOCKED")
    print("Production write  : BLOCKED")
    print("Shell execution   : BLOCKED")
    print("Approval          : REQUIRED")
    print("Fail-closed       : ENABLED")
    print(f"OUTPUT            : {OUT}")
    print(f"RESULT            : {'PASS' if result else 'BLOCKED'}")

if __name__ == "__main__":
    main()
