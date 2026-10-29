from pathlib import Path
import json
import shutil
import sys
import os
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass
from contextvars import ContextVar
from app.core.work_approval_contract import workflow_contract

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "developer_core"
STAGING = ROOT / ".developer_staging"
CHANGE_FILE = DATA / "change_plan.json"
AUDIT_FILE = DATA / "execution_audit.json"
AUTHORIZATION_FILE = DATA / "execution_authorization.json"


@dataclass(frozen=True)
class ExecutionPaths:
    root: Path
    data: Path
    staging: Path
    change_file: Path
    audit_file: Path
    authorization_file: Path

    @classmethod
    def for_root(cls, root, data=None):
        root = Path(root).resolve()
        data = Path(data).resolve() if data else root / 'data'
        folder = data / 'developer_core'
        return cls(root, data, root / '.developer_staging', folder / 'change_plan.json',
                   folder / 'execution_audit.json', folder / 'execution_authorization.json')

_execution_context = ContextVar('v1_execution_context', default=None)

def _paths():
    context = _execution_context.get()
    if context:
        return context[0]
    return ExecutionPaths(ROOT, Path(os.getenv('NUSANTARA_DATA_DIR', str(ROOT / 'data'))),
                          STAGING, CHANGE_FILE, AUDIT_FILE, AUTHORIZATION_FILE)

def _authorization():
    context = _execution_context.get()
    return context[1] if context else None


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
        relative = path.resolve().relative_to(_paths().root.resolve())
        return relative
    except ValueError:
        return None

def load_plan():
    if not _paths().change_file.exists():
        raise RuntimeError("CHANGE PLAN NOT FOUND")

    try:
        return json.loads(_paths().change_file.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"INVALID CHANGE PLAN: {exc}")

def validate_plan(plan):
    change_id = plan.get('change_id', '')
    if not isinstance(change_id, str) or not change_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in change_id):
        raise RuntimeError('PLAN_CHANGE_ID_INVALID')
    prepared = plan.get('schema') == 'nusantara.normal-plan.v1' and plan.get('status') == 'PREPARED'
    if prepared:
        missing = [key for key in ('objective', 'expected_change', 'risk', 'tests_required', 'rollback') if not plan.get(key)]
        if missing:
            raise RuntimeError('PLAN_INCOMPLETE: ' + ', '.join(missing))
    if not prepared and plan.get("status") != "APPROVED":
        raise RuntimeError(
            "WRITE BLOCKED: change plan is not APPROVED"
        )

    approval = plan.get("approval", {})

    if not prepared and approval.get("approved") is not True:
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
        if not isinstance(item, str) or Path(item).is_absolute() or '..' in Path(item).parts or is_forbidden(item):
            raise RuntimeError(
                f"WRITE BLOCKED: forbidden path in scope: {item}"
            )

def build_staging(change_id):
    return _paths().staging / change_id

def validate_staging(plan, staging):
    allowed = {
        norm(x): x
        for x in plan.get("allowed_files", [])
    }

    if not staging.exists():
        raise RuntimeError(
            f"_paths().staging NOT FOUND: {staging}"
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

    if {norm(item) for item in staged_files} != set(allowed):
        raise RuntimeError('PLAN_STAGING_INCOMPLETE')

    return staged_files

def _execute_reviewed(plan, staging, files):
    # Enforce at the mutation boundary, including direct Python callers.
    from app.core.evidence_registry import require_execution_approval
    validate_plan(plan)
    if plan != load_plan():
        raise RuntimeError("WRITE BLOCKED: plan differs from reviewed disk source")
    staging = Path(staging).resolve()
    if staging != build_staging(plan.get("change_id", "")).resolve() or not staging.is_relative_to(_paths().staging.resolve()):
        raise RuntimeError("WRITE BLOCKED: staging boundary mismatch")
    validated = validate_staging(plan, staging)
    if set(files) != set(validated):
        raise RuntimeError("WRITE BLOCKED: staged file list mismatch")
    required = [_paths().change_file.resolve().relative_to(_paths().root.resolve()).as_posix()]
    for relative in validated:
        source = staging / relative
        if source.is_symlink() or not source.resolve().is_relative_to(staging):
            raise RuntimeError("WRITE BLOCKED: staged source escapes boundary")
        required.append(source.resolve().relative_to(_paths().root.resolve()).as_posix())
        destination = _paths().root / relative
        safe = safe_relative(destination)
        if safe is None or is_forbidden(safe):
            raise RuntimeError("WRITE BLOCKED: destination outside allowed boundary")
        if destination.exists():
            required.append(destination.resolve().relative_to(_paths().root.resolve()).as_posix())
    # References live outside the hashed plan to avoid a self-referential
    # package digest. This file is untrusted; the server audit is authoritative.
    try:
        approval = _authorization()
        if approval is None:
            approval = json.loads(_paths().authorization_file.read_text(encoding="utf-8-sig"))
        if not isinstance(approval, dict):
            raise ValueError("invalid authorization reference")
    except (OSError, ValueError):
        raise RuntimeError("WRITE BLOCKED: evidence decision reference unavailable") from None
    require_execution_approval(_paths().root, _paths().data / 'control_plane/evidence_decisions.jsonl',
        package_id=approval.get('package_id', ''), decision_id=approval.get('decision_id', ''), required_sources=required,
        plan_binding=plan_identity(plan, staging, validated))
    if any(row.get('decision_id') == approval.get('decision_id') and row.get('result') in {'AUTHORIZED_ATTEMPT', 'PASS'}
           for row in execution_history(_paths())):
        raise RuntimeError('WRITE BLOCKED: decision already consumed by an execution attempt')
    if any(row.get('change_id') == plan['change_id'] and row.get('result') == 'PASS'
           for row in execution_history(_paths())):
        raise RuntimeError('EXECUTION_PLAN_ALREADY_COMPLETED')
    _execution_context.set((_paths(), approval))
    audit(plan.get('change_id'), 'AUTHORIZED_ATTEMPT', [str(item) for item in validated])
    changed = []

    for relative in files:
        source = staging / relative
        destination = _paths().root / relative

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
        "package_id": (_authorization() or {}).get('package_id'),
        "decision_id": (_authorization() or {}).get('decision_id'),
        "result": result,
        "files_changed": files or [],
        "reason": reason,
        "production_write": False,
        "shell_execution": False,
        "automatic_patch": False,
        "fail_closed": True
    }

    _paths().audit_file.parent.mkdir(parents=True, exist_ok=True)
    # Preserve event history as well as the legacy latest-result projection.
    with _paths().audit_file.with_suffix(".jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    _paths().audit_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def _execution_reason(error):
    from app.core.evidence_registry import EvidenceRegistryError
    import re
    if isinstance(error, EvidenceRegistryError) and re.fullmatch(r'[A-Z0-9_]+', str(error)):
        return str(error)
    for text, code in [('already consumed', 'EXECUTION_DECISION_ALREADY_CONSUMED'),
                       ('EXECUTION_PLAN_ALREADY_COMPLETED', 'EXECUTION_PLAN_ALREADY_COMPLETED'),
                       ('differs from reviewed', 'EXECUTION_PLAN_CHANGED'),
                       ('boundary', 'EXECUTION_BOUNDARY_REJECTED'),
                       ('reference unavailable', 'EXECUTION_REFERENCE_UNAVAILABLE')]:
        if text in str(error):
            return code
    return type(error).__name__


def execute(plan, staging, files, *, paths=None, authorization=None):
    from app.core.evidence_registry import _cross_process_lock
    context = _execution_context.set((paths or _paths(), authorization))
    try:
        with _cross_process_lock(_paths().data / 'developer_core' / 'execution.lock'):
            try:
                changed = _execute_reviewed(plan, staging, files)
            except Exception as exc:
                audit(plan.get('change_id', 'UNKNOWN'), 'BLOCKED', reason=_execution_reason(exc))
                raise
            audit(plan.get('change_id'), 'PASS', changed)
            return changed
    finally:
        _execution_context.reset(context)


def plan_identity(plan, staging, files):
    material = {'plan': plan, 'staged': {str(item).replace('\\', '/'): hashlib.sha256((staging / item).read_bytes()).hexdigest() for item in files}}
    version = hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    return {'plan_id': plan['change_id'], 'version': version, 'action': 'CONTROLLED_FILE_WRITE'}


def execution_context(paths=None):
    token = _execution_context.set((paths or _paths(), None))
    try:
        plan = load_plan()
        validate_plan(plan)
        staging = build_staging(plan.get('change_id', ''))
        files = validate_staging(plan, staging)
        completed = next((row for row in reversed(execution_history(_paths()))
                          if row.get('change_id') == plan['change_id'] and row.get('result') == 'PASS'), None)
        return {'change_id': plan['change_id'], 'expected_change': plan.get('expected_change', ''),
                'workflow': workflow_contract(),
                'plan_origin': {'kind': 'DEVELOPER_OPERATION' if isinstance(plan.get('origin'), dict)
                                and plan['origin'].get('kind') == 'DEVELOPER_OPERATION' else 'UNKNOWN',
                                'actor_identity': 'NOT_RECORDED'},
                'completed': completed is not None, 'completed_at': completed.get('timestamp') if completed else None,
                'plan_binding': plan_identity(plan, staging, files),
                'objective': plan.get('objective', plan.get('expected_change', '')),
                'risk': plan.get('risk', 'Belum dijelaskan'), 'tests_required': plan.get('tests_required', []),
                'rollback': plan.get('rollback', 'Belum dijelaskan'),
                'checked_at': datetime.now(timezone.utc).isoformat(), 'source': 'Developer Core / change_plan.json',
                'target_files': [str(item).replace('\\', '/') for item in files],
                'operation': 'CONTROLLED_FILE_WRITE', 'production_write': False, 'shell_execution': False}
    finally:
        _execution_context.reset(token)


def execute_current(paths, authorization):
    token = _execution_context.set((paths, authorization))
    try:
        try:
            plan = load_plan()
            validate_plan(plan)
            staging = build_staging(plan.get('change_id', ''))
            files = validate_staging(plan, staging)
        except (RuntimeError, ValueError, OSError) as exc:
            audit('UNKNOWN', 'BLOCKED', reason=_execution_reason(exc))
            raise
        return execute(plan, staging, files, paths=paths, authorization=authorization)
    finally:
        _execution_context.reset(token)


def prepare_normal_plan(paths, *, objective, expected_change, documents, risk, tests_required, rollback):
    """Prepare bounded file writes from developer context; never grant human approval.

    Explicit developer operation only. Read-only analysis and GET routes do not call it.
    Existing plans are archived byte-for-byte before replacing the active projection.
    """
    from app.core.evidence_registry import _cross_process_lock
    identity = hashlib.sha256(json.dumps({'objective': objective, 'documents': documents}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    plan = {'schema': 'nusantara.normal-plan.v1', 'change_id': 'NORMAL-' + identity,
            'origin': {'kind': 'DEVELOPER_OPERATION', 'actor_identity': 'NOT_RECORDED'},
            'status': 'PREPARED', 'objective': objective, 'expected_change': expected_change,
            'risk': risk, 'tests_required': tests_required, 'rollback': rollback,
            'allowed_files': sorted(documents), 'write_scope': {'enabled': True},
            'approval': {'required': True, 'approved': False},
            'execution': {'shell_execution': False, 'production_write': False, 'automatic_patch': False}}
    validate_plan(plan)
    with _cross_process_lock(paths.data / 'developer_core/execution.lock'):
        staging = paths.staging / plan['change_id']
        for name, content in documents.items():
            target = staging / name
            if not target.resolve().is_relative_to(staging.resolve()) or target.is_symlink():
                raise RuntimeError('PLAN_STAGING_BOUNDARY_REJECTED')
            if target.exists() and target.read_text(encoding='utf-8') != content:
                raise RuntimeError('PLAN_STAGING_ALREADY_EXISTS')
        for name, content in documents.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                with target.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(content)
        paths.change_file.parent.mkdir(parents=True, exist_ok=True)
        if paths.change_file.exists():
            old = paths.change_file.read_bytes()
            archive = paths.change_file.parent / 'plans' / (hashlib.sha256(old).hexdigest() + '.json')
            archive.parent.mkdir(exist_ok=True)
            if not archive.exists():
                with archive.open('xb') as stream:
                    stream.write(old)
        temporary = paths.change_file.with_suffix('.prepared.tmp')
        temporary.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        os.replace(temporary, paths.change_file)
    return execution_context(paths)


def execution_history(paths):
    log = paths.audit_file.with_suffix('.jsonl')
    if not log.exists():
        return []
    if log.stat().st_size > 16_000_000:
        raise RuntimeError('EXECUTION_HISTORY_SIZE_LIMIT')
    rows = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines() if line.strip()]
    if any(not isinstance(row, dict) or row.get('schema') != 'nusantara-controlled-write-audit-v1' for row in rows):
        raise RuntimeError('EXECUTION_HISTORY_INVALID')
    return rows


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
            if _paths().change_file.exists():
                plan = json.loads(
                    _paths().change_file.read_text(encoding="utf-8-sig")
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
