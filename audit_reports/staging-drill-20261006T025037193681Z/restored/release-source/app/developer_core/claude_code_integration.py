from pathlib import Path
import json
import hashlib
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


def make_change_id(task):
    digest = hashlib.sha256(
        task.encode("utf-8")
    ).hexdigest()[:12].upper()

    return f"CHG-TASK-{digest}"


def main():
    context = read_json(CONTEXT)

    task = str(
        context.get("task", "")
    ).strip()

    if not task:
        raise RuntimeError(
            "BLOCKED: task tidak ditemukan."
        )

    relevant_files = [
        x for x in context.get(
            "relevant_files", []
        )
        if isinstance(x, str) and x.strip()
    ]

    candidate_files = [
        x for x in context.get(
            "candidate_files",
            relevant_files,
        )
        if isinstance(x, str) and x.strip()
    ]

    forbidden_paths = context.get(
        "forbidden_paths", []
    )

    change_id = make_change_id(task)

    # ------------------------------------------------------------
    # CHANGE PLAN
    # ------------------------------------------------------------
    # candidate_files = scope yang diusulkan
    # allowed_files  = scope yang dapat divalidasi approval controller
    # write_scope     = FALSE sampai manusia melakukan approval
    # ------------------------------------------------------------

    change_plan = {
        "schema": "nusantara.change_plan.v1",
        "generated_at": now(),
        "change_id": change_id,
        "objective": task,
        "change_type": "TASK_PROPOSAL",
        "risk": "LOW",
        "status": "APPROVAL_REQUIRED",

        "approval": {
            "required": True,
            "approved": False,
            "approved_by": None,
            "approved_at": None
        },

        "context_files": relevant_files,
        "candidate_files": candidate_files,

        "allowed_files": candidate_files,

        "tests_required": [
            "Gate 7",
            "Gate 15",
            "Gate 16",
            "Gate 17"
        ],

        "execution": {
            "shell_execution": False,
            "production_write": False,
            "automatic_patch": False
        },

        "write_scope": {
            "enabled": False
        },

        "fail_closed": True
    }

    CHANGE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    CHANGE.write_text(
        json.dumps(
            change_plan,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    # ------------------------------------------------------------
    # CLAUDE CODE CONTEXT
    # ------------------------------------------------------------

    result = {
        "schema": "nusantara.claude_code_context.v2",
        "generated_at": now(),
        "role": "CONTROLLED_PROGRAMMER",
        "task": task,

        "relevant_files": relevant_files,
        "candidate_files": candidate_files,

        # Ini proposal scope, BUKAN izin write.
        "allowed_files": candidate_files,

        "forbidden_paths": forbidden_paths,

        "change_id": change_id,

        "approval_status": "APPROVAL_REQUIRED",
        "approval_required": True,

        "write_mode": "CONTROLLED",
        "write_enabled": False,

        "execution": {
            "shell_execution": False,
            "production_write": False,
            "automatic_patch": False
        },

        "instruction": (
            "Claude Code may analyze and propose changes. "
            "Use relevant_files as read context. "
            "candidate_files represent the proposed change scope. "
            "No write is permitted before explicit human approval. "
            "Controlled write must validate approval, write scope, "
            "allowed files and forbidden paths. "
            "Shell execution, production write and automatic patch "
            "remain blocked."
        ),

        "fail_closed": True
    }

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUT.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("=" * 64)
    print("NUSANTARA CLAUDE CODE INTEGRATION V2")
    print("=" * 64)
    print("Role             : CONTROLLED_PROGRAMMER")
    print(f"Change ID        : {change_id}")
    print("Approval status  : APPROVAL_REQUIRED")
    print(f"Relevant files   : {len(relevant_files)}")
    print(f"Candidate files  : {len(candidate_files)}")
    print("Write enabled    : False")
    print("Shell            : BLOCKED")
    print("Production       : BLOCKED")
    print("Automatic patch  : BLOCKED")
    print("Approval         : REQUIRED")
    print("Fail-closed      : ENABLED")
    print(f"OUTPUT           : {OUT}")
    print("STATUS           : READY")


if __name__ == "__main__":
    main()
