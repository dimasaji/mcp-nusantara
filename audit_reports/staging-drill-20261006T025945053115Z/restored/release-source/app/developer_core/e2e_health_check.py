"""
Nusantara Developer Core - E2E Health Check
Safe diagnostic module. No production write, shell execution, or automatic patch.
"""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[2]


def check_json_file(path: Path) -> dict:
    result = {
        "path": str(path.relative_to(ROOT)),
        "exists": path.exists(),
        "valid_json": False,
    }

    if not path.exists():
        return result

    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
        result["valid_json"] = True
    except Exception:
        result["valid_json"] = False

    return result


def run_health_check() -> dict:
    checks = {
        "context_router": check_json_file(
            ROOT / "data" / "developer_core" / "context" / "context_package.json"
        ),
        "change_plan": check_json_file(
            ROOT / "data" / "developer_core" / "change_plan.json"
        ),
        "claude_code_context": check_json_file(
            ROOT / "data" / "developer_core" / "claude_code_context.json"
        ),
        "regression": check_json_file(
            ROOT / "data" / "developer_core" / "regression" / "regression_result.json"
        ),
        "self_improvement": check_json_file(
            ROOT / "data" / "developer_core" / "self_improvement"
            / "self_improvement_report.json"
        ),
    }

    return {
        "status": "PASS" if all(
            item["exists"] and item["valid_json"]
            for item in checks.values()
        ) else "WARN",
        "production_write": False,
        "shell_execution": False,
        "automatic_patch": False,
        "checks": checks,
    }


if __name__ == "__main__":
    print(json.dumps(run_health_check(), indent=2))
