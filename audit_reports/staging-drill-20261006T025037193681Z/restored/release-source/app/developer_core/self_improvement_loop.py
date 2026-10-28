from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
REGRESSION = ROOT / "data" / "developer_core" / "regression" / "regression_result.json"
AUDIT = ROOT / "data" / "developer_core" / "execution_audit.json"
OUT = ROOT / "data" / "developer_core" / "self_improvement" / "self_improvement_report.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    if not path.exists():
        return {}
    try:
        return json.loads(
            path.read_text(encoding="utf-8-sig")
        )
    except Exception:
        return {}

def main():
    regression = read(REGRESSION)
    audit = read(AUDIT)

    observations = []

    if regression.get("result") == "PASS":
        observations.append({
            "area": "regression",
            "status": "HEALTHY",
            "action": "No automatic change required."
        })
    else:
        observations.append({
            "area": "regression",
            "status": "REVIEW_REQUIRED",
            "action": "Create proposal; do not auto-patch."
        })

    if audit:
        observations.append({
            "area": "execution_audit",
            "status": "OBSERVED",
            "action": "Use audit findings for future proposals."
        })
    else:
        observations.append({
            "area": "execution_audit",
            "status": "NO_DATA",
            "action": "Await controlled execution."
        })

    result = {
        "schema": "nusantara.self_improvement.v1",
        "generated_at": now(),
        "mode": "OBSERVE_PROPOSE_APPROVE",
        "observations": observations,
        "automatic_patch": False,
        "automatic_write": False,
        "shell_execution": False,
        "production_write": False,
        "approval_required": True,
        "human_review": True,
        "fail_closed": True,
        "next_action": (
            "Create a change proposal only after evidence and regression review."
        )
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("================================================================")
    print("NUSANTARA SELF-IMPROVEMENT LOOP V1")
    print("================================================================")
    print("Mode             : OBSERVE -> PROPOSE -> APPROVE")
    print("Automatic patch  : BLOCKED")
    print("Automatic write  : BLOCKED")
    print("Shell            : BLOCKED")
    print("Production       : BLOCKED")
    print("Human review     : REQUIRED")
    print("Fail-closed      : ENABLED")
    print(f"OUTPUT           : {OUT}")
    print("STATUS           : READY")

if __name__ == "__main__":
    main()
