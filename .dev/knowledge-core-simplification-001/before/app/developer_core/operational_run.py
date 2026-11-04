from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "developer_core"
DATA.mkdir(parents=True, exist_ok=True)

REPORT = DATA / "operational_run_report.json"
CHANGE = DATA / "change_plan.json"
POLICY = DATA / "write_policy.json"

def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def graph_status():
    p = ROOT / "graphify-out" / "graph.json"
    if not p.exists():
        return {
            "status": "BLOCKED",
            "nodes": 0,
            "edges": 0,
            "reason": "graph.json not found"
        }

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
        edges = data.get("edges", data.get("links", []))
        return {
            "status": "ok",
            "nodes": len(nodes) if isinstance(nodes, list) else 0,
            "edges": len(edges) if isinstance(edges, list) else 0
        }
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "nodes": 0,
            "edges": 0,
            "reason": str(exc)
        }

def build_report():
    now = datetime.now(timezone.utc).isoformat()

    validation = load_json(
        ROOT / "data" / "validation" / "nusantara_validation_report.json",
        {}
    )

    gates = {}
    for key, value in validation.items():
        if str(key).lower().startswith("gate"):
            gates[str(key)] = value

    graph = graph_status()

    report = {
        "schema": "nusantara-developer-core-operational-run-v1",
        "generated_at": now,
        "status": "READY",
        "mode": "CONTROLLED_WRITE",

        "safety": {
            "read": True,
            "write": "APPROVAL_REQUIRED",
            "shell_execution": False,
            "production_write": False,
            "automatic_patch": False,
            "unrestricted_write": False,
            "fail_closed": True
        },

        "graph": graph,

        "gates": gates,

        "developer_core": {
            "inspect": "READY",
            "graph": "READY" if graph["status"] == "ok" else "BLOCKED",
            "impact": "READY",
            "evidence": "READY",
            "gap": "READY",
            "root_cause": "READY",
            "proposal": "READY",
            "experiment": "READY",
            "evaluation": "READY",
            "release_check": "READY"
        },

        "write_contract": {
            "requires_change_plan": True,
            "requires_human_approval": True,
            "allowed_files_only": True,
            "forbidden_production_paths": True,
            "forbidden_git_paths": True,
            "regression_required": True
        },

        "claude_code": {
            "role": "CONTROLLED_PROGRAMMER",
            "context_source": "data/developer_core/operational_run_report.json",
            "next_step": "CREATE_CHANGE_PLAN",
            "repository_wide_discovery": "AVOID_UNLESS_REQUIRED"
        }
    }

    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return report

def build_change_plan():
    now = datetime.now(timezone.utc).isoformat()

    plan = {
        "schema": "nusantara-developer-core-change-plan-v1",
        "generated_at": now,
        "change_id": "CHG-PENDING",
        "status": "APPROVAL_REQUIRED",

        "objective": None,

        "allowed_files": [],

        "forbidden_paths": [
            ".git",
            ".git/*",
            ".env",
            ".env.*",
            "data/production",
            "data/production/*"
        ],

        "tests_required": [
            "Gate 7",
            "Gate 8",
            "Gate 9",
            "Gate 10",
            "Gate 11",
            "Gate 12",
            "Gate 13",
            "Gate 14",
            "Gate 15",
            "Gate 16",
            "Gate 17"
        ],

        "risk": "UNKNOWN",

        "approval": {
            "required": True,
            "approved": False,
            "approved_at": None
        },

        "write_scope": {
            "enabled": False,
            "reason": "Human approval has not been granted."
        },

        "execution": {
            "shell_execution": False,
            "production_write": False,
            "automatic_patch": False
        }
    }

    CHANGE.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return plan

def build_policy():
    policy = {
        "schema": "nusantara-developer-core-write-policy-v1",

        "mode": "CONTROLLED_WRITE",

        "rules": {
            "read_allowed": True,
            "analysis_allowed": True,
            "proposal_allowed": True,
            "change_plan_allowed": True,

            "write_requires_approval": True,
            "write_requires_allowed_files": True,

            "shell_execution": False,
            "production_write": False,
            "automatic_patch": False,
            "unrestricted_write": False
        },

        "fail_closed": True,

        "approval_states": [
            "APPROVAL_REQUIRED",
            "APPROVED",
            "REJECTED",
            "BLOCKED"
        ],

        "default_state": "APPROVAL_REQUIRED"
    }

    POLICY.write_text(
        json.dumps(policy, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return policy

if __name__ == "__main__":
    report = build_report()
    plan = build_change_plan()
    policy = build_policy()

    print("=" * 64)
    print("NUSANTARA DEVELOPER CORE V1 - CONTROLLED CODING")
    print("=" * 64)
    print("Operational Run Report : READY")
    print("Change Plan             : APPROVAL_REQUIRED")
    print("Write Policy            : CONTROLLED")
    print("Human Approval          : REQUIRED")
    print("Shell Execution         : BLOCKED")
    print("Production Write        : BLOCKED")
    print("Automatic Patch         : BLOCKED")
    print("Unrestricted Write      : BLOCKED")
    print("Fail Closed             : ENABLED")
    print()
    print("REPORT :", REPORT)
    print("CHANGE :", CHANGE)
    print("POLICY :", POLICY)
    print()
    print("Claude Code role        : CONTROLLED_PROGRAMMER")
    print("STATUS                  : READY")
