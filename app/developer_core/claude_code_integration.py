from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
CONTEXT = ROOT / "data" / "developer_core" / "context" / "context_package.json"
CHANGE = ROOT / "data" / "developer_core" / "change_plan.json"
OUT = ROOT / "data" / "developer_core" / "claude_code_context.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path):
    if not path.exists():
        return {}
    return json.loads(
        path.read_text(encoding="utf-8-sig")
    )

def main():
    context = read_json(CONTEXT)
    change = read_json(CHANGE)

    result = {
        "schema": "nusantara.claude_code_context.v1",
        "generated_at": now(),
        "role": "CONTROLLED_PROGRAMMER",
        "task": context.get("task"),
        "relevant_files": context.get("relevant_files", []),
        "allowed_files": change.get("allowed_files", []),
        "forbidden_paths": context.get("forbidden_paths", []),
        "change_id": change.get("change_id"),
        "approval_status": change.get("status", "APPROVAL_REQUIRED"),
        "approval_required": True,
        "write_enabled": False,
        "shell_execution": False,
        "production_write": False,
        "automatic_patch": False,
        "instruction": (
            "Claude Code may analyze and propose changes. "
            "Code changes must remain inside approved allowed_files. "
            "Human approval is mandatory before controlled write."
        ),
        "fail_closed": True
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("================================================================")
    print("NUSANTARA CLAUDE CODE INTEGRATION V1")
    print("================================================================")
    print("Role             : CONTROLLED_PROGRAMMER")
    print(f"Change ID        : {result['change_id']}")
    print(f"Approval status  : {result['approval_status']}")
    print(f"Relevant files   : {len(result['relevant_files'])}")
    print(f"Allowed files    : {len(result['allowed_files'])}")
    print("Write            : CONTROLLED")
    print("Shell            : BLOCKED")
    print("Production       : BLOCKED")
    print("Automatic patch  : BLOCKED")
    print("Approval         : REQUIRED")
    print("Fail-closed      : ENABLED")
    print(f"OUTPUT           : {OUT}")
    print("STATUS           : READY")

if __name__ == "__main__":
    main()
