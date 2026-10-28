from pathlib import Path
import json
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / "graphify-out" / "graph.json"
VALIDATION = ROOT / "data" / "validation" / "nusantara_validation_report.json"
OUT = ROOT / "data" / "developer_core"
OUT.mkdir(parents=True, exist_ok=True)


def run_command(args):
    p = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": " ".join(args),
        "returncode": p.returncode,
        "stdout": p.stdout[-12000:],
        "stderr": p.stderr[-12000:],
        "ok": p.returncode == 0,
    }


def inspect_project():
    return {
        "root": str(ROOT),
        "graph_exists": GRAPH.exists(),
        "validation_exists": VALIDATION.exists(),
        "git": run_command(["git", "status", "--short"]),
        "head": run_command(["git", "rev-parse", "--short", "HEAD"]),
        "branch": run_command(["git", "branch", "--show-current"]),
    }


def inspect_graph():
    if not GRAPH.exists():
        return {
            "status": "unavailable",
            "reason": "graph.json not found",
        }

    try:
        data = json.loads(GRAPH.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
        edges = data.get("edges", data.get("links", []))

        return {
            "status": "ok",
            "nodes": len(nodes),
            "edges": len(edges),
        }
    except Exception as exc:
        return {
            "status": "error",
            "reason": str(exc),
        }


def inspect_validation():
    if not VALIDATION.exists():
        return {
            "status": "unavailable",
            "reason": "validation report not found",
        }

    try:
        return {
            "status": "ok",
            "report": json.loads(
                VALIDATION.read_text(encoding="utf-8")
            ),
        }
    except Exception as exc:
        return {
            "status": "error",
            "reason": str(exc),
        }


def create_operationalization():
    return {
        "name": "Nusantara Developer Core Operationalization",
        "version": "1.0.0",
        "mode": "controlled",
        "production_write": False,
        "shell_execution": False,
        "automatic_patch": False,
        "approval_required": True,
        "stages": [
            "inspect",
            "graph",
            "impact",
            "evidence",
            "gap",
            "root_cause",
            "proposal",
            "experiment",
            "evaluation",
            "release_check",
        ],
        "contracts": {
            "evidence_before_conclusion": True,
            "deterministic_queries": True,
            "fail_closed": True,
            "preserve_existing_tools": True,
            "preserve_gate_14": True,
            "preserve_gate_15": True,
            "preserve_gate_16": True,
            "preserve_gate_17": True,
        },
    }


def main():
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": inspect_project(),
        "graph": inspect_graph(),
        "validation": inspect_validation(),
        "operationalization": create_operationalization(),
    }

    output = OUT / "developer_core_operationalization.json"
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=" * 68)
    print("NUSANTARA DEVELOPER CORE OPERATIONALIZATION")
    print("=" * 68)
    print("Version              : 1.0.0")
    print("Mode                 : CONTROLLED")
    print("Production write     : DISABLED")
    print("Shell execution      : DISABLED")
    print("Automatic patch      : DISABLED")
    print("Approval required    : YES")
    print()
    print("Graph status         :", result["graph"]["status"])

    if result["graph"].get("status") == "ok":
        print("Graph nodes          :", result["graph"]["nodes"])
        print("Graph edges          :", result["graph"]["edges"])

    print()
    print("Operational stages:")
    for stage in result["operationalization"]["stages"]:
        print("  [READY] " + stage)

    print()
    print("OUTPUT:")
    print(output)
    print()
    print("DEVELOPER CORE OPERATIONALIZATION: READY")


if __name__ == "__main__":
    main()
