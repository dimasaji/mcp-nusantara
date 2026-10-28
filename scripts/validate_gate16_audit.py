from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.approval.audit_trail import AuditTrail
from app.developer_core.execution_audit import (
    ExecutionAudit,
    ExecutionAuditError,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def audit_entries(audit: AuditTrail):
    entries = getattr(audit, "_entries", None)

    if entries is None:
        entries = getattr(audit, "entries", None)

    if callable(entries):
        entries = entries()

    if entries is None:
        raise RuntimeError(
            "Tidak dapat membaca entries AuditTrail existing."
        )

    return list(entries)


def event_names(entries):
    result = []

    for entry in entries:
        if isinstance(entry, dict):
            event = entry.get("event")
        else:
            event = getattr(entry, "event", None)

        if event:
            result.append(event)

    return result


def main():
    print("=" * 72)
    print("NUSANTARA GATE 16.9")
    print("EXECUTION AUDIT")
    print("=" * 72)

    checks = 0

    # --------------------------------------------------------------
    # 16.9.1 EXISTING AUDIT SYSTEM
    # --------------------------------------------------------------

    check(
        issubclass(ExecutionAudit, object),
        "ExecutionAudit tidak valid",
    )

    checks += 1
    print(
        "[PASS] 16.9.1 Execution audit module available"
    )

    # --------------------------------------------------------------
    # 16.9.2 NO DUPLICATE AUDIT SYSTEM
    # --------------------------------------------------------------

    source = (
        PROJECT_ROOT
        / "app"
        / "approval"
        / "audit_trail.py"
    )

    check(
        source.is_file(),
        "app/approval/audit_trail.py tidak ditemukan",
    )

    audit = AuditTrail()

    executor_audit = ExecutionAudit(
        audit=audit
    )

    check(
        executor_audit.audit is audit,
        "ExecutionAudit tidak menggunakan AuditTrail existing",
    )

    checks += 1
    print(
        "[PASS] 16.9.2 Existing AuditTrail reused"
    )

    # --------------------------------------------------------------
    # 16.9.3 EXECUTION EVENTS
    # --------------------------------------------------------------

    execution_id = "exec-gate16.9-001"

    executor_audit.execution_requested(
        execution_id=execution_id,
        change_id="change-gate16.9",
        requested_by="validator",
    )

    executor_audit.approval_verified(
        execution_id=execution_id,
        approval_id="approval-gate16.9",
    )

    executor_audit.boundary_validated(
        execution_id=execution_id,
        target_files=(
            "tests/gate16_target.py",
        ),
    )

    executor_audit.snapshot_created(
        execution_id=execution_id,
        snapshot_id="snapshot-gate16.9",
    )

    executor_audit.patch_started(
        execution_id=execution_id,
        target_file="tests/gate16_target.py",
    )

    executor_audit.patch_completed(
        execution_id=execution_id,
        target_file="tests/gate16_target.py",
        sha256_before="before-hash",
        sha256_after="after-hash",
    )

    executor_audit.validation_completed(
        execution_id=execution_id,
        result="pass",
    )

    executor_audit.regression_completed(
        execution_id=execution_id,
        result="pass",
    )

    executor_audit.graph_revalidated(
        execution_id=execution_id,
        graph_nodes=2824,
        graph_links=5920,
    )

    executor_audit.execution_completed(
        execution_id=execution_id,
        result="success",
    )

    entries = audit_entries(audit)

    names = event_names(entries)

    expected = list(
        ExecutionAudit.SUCCESS_EVENTS
    )

    check(
        names == expected,
        "Urutan execution event tidak sesuai contract",
    )

    checks += 1
    print(
        "[PASS] 16.9.3 Execution events recorded in order"
    )

    # --------------------------------------------------------------
    # 16.9.4 HASH CHAIN
    # --------------------------------------------------------------

    check(
        executor_audit.verify() is True,
        "Audit hash chain tidak valid",
    )

    checks += 1
    print(
        "[PASS] 16.9.4 Audit hash chain verifies"
    )

    # --------------------------------------------------------------
    # 16.9.5 TAMPER DETECTION
    # --------------------------------------------------------------

    tamper_audit = AuditTrail()

    tamper_executor = ExecutionAudit(
        audit=tamper_audit
    )

    tamper_executor.execution_requested(
        execution_id="exec-tamper",
        change_id="change-tamper",
        requested_by="validator",
    )

    tamper_entries = audit_entries(
        tamper_audit
    )

    check(
        len(tamper_entries) == 1,
        "Audit tamper fixture tidak memiliki entry",
    )

    first = tamper_entries[0]

    if isinstance(first, dict):
        original = first.get("data")
        first["data"] = {
            "tampered": True
        }
    else:
        original = getattr(first, "data", None)
        try:
            first.data = {
                "tampered": True
            }
        except Exception:
            raise RuntimeError(
                "Audit entry tidak dapat dimodifikasi untuk test tamper."
            )

    try:
        tamper_detected = False

        try:
            tamper_executor.verify()
        except ExecutionAuditError:
            tamper_detected = True

        check(
            tamper_detected,
            "Tamper audit tidak terdeteksi",
        )

    finally:
        if isinstance(first, dict):
            first["data"] = original
        else:
            try:
                first.data = original
            except Exception:
                pass

    checks += 1
    print(
        "[PASS] 16.9.5 Audit tampering detected"
    )

    # --------------------------------------------------------------
    # 16.9.6 FAILURE / ROLLBACK EVENTS
    # --------------------------------------------------------------

    failure_audit = AuditTrail()

    failure_executor = ExecutionAudit(
        audit=failure_audit
    )

    failure_executor.execution_requested(
        execution_id="exec-failure",
        change_id="change-failure",
        requested_by="validator",
    )

    failure_executor.validation_failed(
        execution_id="exec-failure",
        reason="synthetic validation failure",
    )

    failure_executor.rollback_started(
        execution_id="exec-failure",
        snapshot_id="snapshot-failure",
    )

    failure_executor.rollback_completed(
        execution_id="exec-failure",
        snapshot_id="snapshot-failure",
        result="success",
    )

    failure_executor.execution_failed(
        execution_id="exec-failure",
        reason="execution rolled back",
    )

    failure_names = event_names(
        audit_entries(failure_audit)
    )

    expected_failure = [
        "execution.requested",
        "validation.failed",
        "rollback.started",
        "rollback.completed",
        "execution.failed",
    ]

    check(
        failure_names == expected_failure,
        "Failure/rollback event sequence tidak sesuai",
    )

    check(
        failure_executor.verify() is True,
        "Failure audit chain tidak valid",
    )

    checks += 1
    print(
        "[PASS] 16.9.6 Failure / rollback events recorded"
    )

    # --------------------------------------------------------------
    # 16.9.7 FAIL-CLOSED AUDIT
    # --------------------------------------------------------------

    class BrokenAudit:
        def record(self, event, **fields):
            raise RuntimeError(
                "synthetic audit failure"
            )

        def verify(self):
            return False

    broken_executor = ExecutionAudit(
        audit=BrokenAudit()
    )

    failed_closed = False

    try:
        broken_executor.execution_requested(
            execution_id="exec-fail-closed",
            change_id="change-fail-closed",
            requested_by="validator",
        )
    except ExecutionAuditError:
        failed_closed = True

    check(
        failed_closed,
        "Audit failure tidak fail-closed",
    )

    checks += 1
    print(
        "[PASS] 16.9.7 Audit failure is fail-closed"
    )

    # --------------------------------------------------------------
    # 16.9.8 UNKNOWN EVENT BLOCKED
    # --------------------------------------------------------------

    unknown_blocked = False

    try:
        executor_audit.record(
            "execution.unknown",
            execution_id="invalid",
        )
    except ExecutionAuditError:
        unknown_blocked = True

    check(
        unknown_blocked,
        "Unknown audit event tidak diblokir",
    )

    checks += 1
    print(
        "[PASS] 16.9.8 Unknown audit event blocked"
    )

    # --------------------------------------------------------------
    # 16.9.9 SENSITIVE FIELD REDACTION
    # --------------------------------------------------------------

    redaction_audit = AuditTrail()

    redaction_executor = ExecutionAudit(
        audit=redaction_audit
    )

    redaction_executor.record(
        ExecutionAudit.EVENT_EXECUTION_REQUESTED,
        execution_id="exec-redaction",
        api_key="SECRET-DO-NOT-STORE",  # nosecret: fixture for Gate 16.9.9 redaction test
        token="TOKEN-DO-NOT-STORE",  # nosecret: fixture for Gate 16.9.9 redaction test
        normal_field="safe",
    )

    redaction_entry = audit_entries(
        redaction_audit
    )[0]

    if isinstance(redaction_entry, dict):
        data = redaction_entry.get("data", {})
    else:
        data = getattr(redaction_entry, "data", {})

    check(
        data.get("api_key") == "[REDACTED]",
        "api_key tidak di-redact",
    )

    check(
        data.get("token") == "[REDACTED]",
        "token tidak di-redact",
    )

    check(
        data.get("normal_field") == "safe",
        "Field normal berubah secara tidak semestinya",
    )

    checks += 1
    print(
        "[PASS] 16.9.9 Sensitive audit fields redacted"
    )

    # --------------------------------------------------------------
    # 16.9.10 PERSISTENCE
    # --------------------------------------------------------------

    with tempfile.TemporaryDirectory(
        prefix="nusantara_gate16_9_"
    ) as temp_dir:

        audit_file = (
            Path(temp_dir)
            / "execution_audit.json"
        )

        persisted = ExecutionAudit(
            persist_path=audit_file
        )

        persisted.execution_requested(
            execution_id="exec-persist",
            change_id="change-persist",
            requested_by="validator",
        )

        check(
            audit_file.is_file(),
            "Audit persistence file tidak dibuat",
        )

        check(
            persisted.verify() is True,
            "Persisted audit chain tidak valid",
        )

    checks += 1
    print(
        "[PASS] 16.9.10 Audit persistence and verification"
    )

    # --------------------------------------------------------------
    # FINAL
    # --------------------------------------------------------------

    print("-" * 72)
    print(
        f"VALIDATION CHECKS : {checks}"
    )
    print(
        f"PASS              : {checks}"
    )
    print(
        "FAIL              : 0"
    )
    print("-" * 72)
    print(
        "GATE 16.9 FINAL   : PASS"
    )
    print(
        "EXECUTION AUDIT   : FAIL-CLOSED"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
