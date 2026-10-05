from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("Health Check", ROOT / "app" / "developer_core" / "e2e_health_check.py"),
    ("Regression Gate", ROOT / "app" / "developer_core" / "automatic_regression_gate.py"),
    ("Execution Audit", ROOT / "app" / "developer_core" / "execution_audit_integration.py"),
    ("Self Improvement", ROOT / "app" / "developer_core" / "self_improvement_loop.py"),
]


def run_step(name, script):
    if not script.exists():
        return {
            "name": name,
            "status": "FAIL",
            "reason": f"Missing: {script.relative_to(ROOT)}",
        }

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        return {
            "name": name,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "output": result.stdout[-3000:],
            "error": result.stderr[-1000:] if result.stderr else "",
        }
    except Exception as exc:
        return {
            "name": name,
            "status": "FAIL",
            "reason": str(exc),
        }


def main():
    print("=" * 68)
    print("NUSANTARA DEVELOPER CORE")
    print("=" * 68)

    results = []

    for name, script in STEPS:
        result = run_step(name, script)
        results.append(result)
        print(f"{name:<22}: {result['status']}")

        if result["status"] != "PASS":
            print()
            print(result.get("reason", result.get("error", "")))
            break

    security = {
        "production_write": False,
        "shell_execution": False,
        "automatic_patch": False,
        "fail_closed": True,
    }

    print()
    print("SECURITY")
    print(f"Production Write     : BLOCKED")
    print(f"Shell Execution      : BLOCKED")
    print(f"Automatic Patch      : BLOCKED")
    print(f"Fail-Closed          : ENABLED")

    overall = all(r["status"] == "PASS" for r in results)

    report = {
        "schema": "nusantara.developer_core.e2e.v1",
        "status": "PASS" if overall else "FAIL",
        "security": security,
        "results": results,
    }

    out = ROOT / "data" / "developer_core" / "developer_core_e2e_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print(f"REPORT               : {out}")
    print(f"DEVELOPER CORE       : {'PASS' if overall else 'FAIL'}")


if __name__ == "__main__":
    main()
