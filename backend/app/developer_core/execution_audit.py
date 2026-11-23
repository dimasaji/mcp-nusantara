from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from app.approval.audit_trail import AuditTrail


class ExecutionAuditError(RuntimeError):
    """Raised when execution audit cannot safely proceed."""


@dataclass(frozen=True)
class ExecutionAuditResult:
    event: str
    recorded: bool
    sequence: int


class ExecutionAudit:
    """
    Gate 16.9 Execution Audit.

    Audit layer untuk controlled execution Nusantara.

    Prinsip:
    - menggunakan AuditTrail existing;
    - tidak membuat hash-chain kedua;
    - append-only;
    - fail-closed;
    - deterministic event names;
    - tidak melakukan write/patch/execute;
    - tidak menjalankan subprocess/shell;
    """

    EVENT_EXECUTION_REQUESTED = "execution.requested"
    EVENT_APPROVAL_VERIFIED = "approval.verified"
    EVENT_BOUNDARY_VALIDATED = "boundary.validated"
    EVENT_SNAPSHOT_CREATED = "snapshot.created"
    EVENT_PATCH_STARTED = "patch.started"
    EVENT_PATCH_COMPLETED = "patch.completed"
    EVENT_VALIDATION_COMPLETED = "validation.completed"
    EVENT_REGRESSION_COMPLETED = "regression.completed"
    EVENT_GRAPH_REVALIDATED = "graph.revalidated"
    EVENT_EXECUTION_COMPLETED = "execution.completed"

    EVENT_VALIDATION_FAILED = "validation.failed"
    EVENT_ROLLBACK_STARTED = "rollback.started"
    EVENT_ROLLBACK_COMPLETED = "rollback.completed"
    EVENT_EXECUTION_FAILED = "execution.failed"

    SUCCESS_EVENTS = (
        EVENT_EXECUTION_REQUESTED,
        EVENT_APPROVAL_VERIFIED,
        EVENT_BOUNDARY_VALIDATED,
        EVENT_SNAPSHOT_CREATED,
        EVENT_PATCH_STARTED,
        EVENT_PATCH_COMPLETED,
        EVENT_VALIDATION_COMPLETED,
        EVENT_REGRESSION_COMPLETED,
        EVENT_GRAPH_REVALIDATED,
        EVENT_EXECUTION_COMPLETED,
    )

    FAILURE_EVENTS = (
        EVENT_VALIDATION_FAILED,
        EVENT_ROLLBACK_STARTED,
        EVENT_ROLLBACK_COMPLETED,
        EVENT_EXECUTION_FAILED,
    )

    ALL_EVENTS = SUCCESS_EVENTS + FAILURE_EVENTS

    def __init__(
        self,
        audit: AuditTrail | None = None,
        *,
        persist_path: str | Path | None = None,
    ) -> None:
        if audit is not None and persist_path is not None:
            raise ValueError(
                "Gunakan audit atau persist_path, bukan keduanya."
            )

        if audit is None:
            if persist_path is None:
                self._audit = AuditTrail()
            else:
                self._audit = AuditTrail(
                    Path(persist_path)
                )
        else:
            self._audit = audit

        self._last_sequence = 0

    @property
    def audit(self) -> AuditTrail:
        return self._audit

    @classmethod
    def event_names(cls) -> tuple[str, ...]:
        return cls.ALL_EVENTS

    def record(
        self,
        event: str,
        **fields: Any,
    ) -> ExecutionAuditResult:
        """
        Record satu execution event.

        Fail-closed:
        jika AuditTrail gagal mencatat event, exception diteruskan
        dan caller wajib menghentikan execution.
        """

        if event not in self.ALL_EVENTS:
            raise ExecutionAuditError(
                f"Execution audit event tidak dikenal: {event}"
            )

        try:
            entry = self._audit.record(
                event,
                **self._sanitize_fields(fields),
            )
        except Exception as exc:
            raise ExecutionAuditError(
                f"Audit gagal untuk event '{event}': {exc}"
            ) from exc

        sequence = self._extract_sequence(entry)

        if sequence <= 0:
            raise ExecutionAuditError(
                f"Audit event '{event}' tidak menghasilkan sequence valid."
            )

        self._last_sequence = sequence

        return ExecutionAuditResult(
            event=event,
            recorded=True,
            sequence=sequence,
        )

    def verify(self) -> bool:
        """
        Verifikasi hash-chain AuditTrail existing.

        Tidak membuat mekanisme verifikasi kedua.
        """

        try:
            result = self._audit.verify()
        except Exception as exc:
            raise ExecutionAuditError(
                f"Audit verification gagal: {exc}"
            ) from exc

        if result is not True:
            raise ExecutionAuditError(
                "Audit chain tidak valid."
            )

        return True

    def require_verified(self) -> None:
        """Fail-closed verification boundary."""

        self.verify()

    def execution_requested(
        self,
        *,
        execution_id: str,
        change_id: str,
        requested_by: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_EXECUTION_REQUESTED,
            execution_id=execution_id,
            change_id=change_id,
            requested_by=requested_by,
        )

    def approval_verified(
        self,
        *,
        execution_id: str,
        approval_id: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_APPROVAL_VERIFIED,
            execution_id=execution_id,
            approval_id=approval_id,
        )

    def boundary_validated(
        self,
        *,
        execution_id: str,
        target_files: tuple[str, ...] | list[str],
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_BOUNDARY_VALIDATED,
            execution_id=execution_id,
            target_files=tuple(target_files),
        )

    def snapshot_created(
        self,
        *,
        execution_id: str,
        snapshot_id: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_SNAPSHOT_CREATED,
            execution_id=execution_id,
            snapshot_id=snapshot_id,
        )

    def patch_started(
        self,
        *,
        execution_id: str,
        target_file: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_PATCH_STARTED,
            execution_id=execution_id,
            target_file=target_file,
        )

    def patch_completed(
        self,
        *,
        execution_id: str,
        target_file: str,
        sha256_before: str,
        sha256_after: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_PATCH_COMPLETED,
            execution_id=execution_id,
            target_file=target_file,
            sha256_before=sha256_before,
            sha256_after=sha256_after,
        )

    def validation_completed(
        self,
        *,
        execution_id: str,
        result: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_VALIDATION_COMPLETED,
            execution_id=execution_id,
            result=result,
        )

    def regression_completed(
        self,
        *,
        execution_id: str,
        result: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_REGRESSION_COMPLETED,
            execution_id=execution_id,
            result=result,
        )

    def graph_revalidated(
        self,
        *,
        execution_id: str,
        graph_nodes: int,
        graph_links: int,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_GRAPH_REVALIDATED,
            execution_id=execution_id,
            graph_nodes=graph_nodes,
            graph_links=graph_links,
        )

    def execution_completed(
        self,
        *,
        execution_id: str,
        result: str = "success",
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_EXECUTION_COMPLETED,
            execution_id=execution_id,
            result=result,
        )

    def validation_failed(
        self,
        *,
        execution_id: str,
        reason: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_VALIDATION_FAILED,
            execution_id=execution_id,
            reason=reason,
        )

    def rollback_started(
        self,
        *,
        execution_id: str,
        snapshot_id: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_ROLLBACK_STARTED,
            execution_id=execution_id,
            snapshot_id=snapshot_id,
        )

    def rollback_completed(
        self,
        *,
        execution_id: str,
        snapshot_id: str,
        result: str = "success",
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_ROLLBACK_COMPLETED,
            execution_id=execution_id,
            snapshot_id=snapshot_id,
            result=result,
        )

    def execution_failed(
        self,
        *,
        execution_id: str,
        reason: str,
    ) -> ExecutionAuditResult:
        return self.record(
            self.EVENT_EXECUTION_FAILED,
            execution_id=execution_id,
            reason=reason,
        )

    @staticmethod
    def _extract_sequence(entry: Any) -> int:
        if isinstance(entry, Mapping):
            value = entry.get("seq")

            if isinstance(value, int):
                return value

            if isinstance(value, str) and value.isdigit():
                return int(value)

        value = getattr(entry, "seq", None)

        if isinstance(value, int):
            return value

        if isinstance(value, str) and value.isdigit():
            return int(value)

        raise ExecutionAuditError(
            "AuditTrail.record() tidak mengembalikan sequence."
        )

    @staticmethod
    def _sanitize_fields(
        fields: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Tidak menyimpan payload rahasia secara sengaja.

        Execution audit hanya menyimpan metadata execution.
        """

        blocked_names = {
            "password",
            "token",
            "secret",
            "api_key",
            "apikey",
            "private_key",
            "credential",
        }

        result: dict[str, Any] = {}

        for key, value in fields.items():
            key_lower = str(key).lower()

            if any(
                blocked in key_lower
                for blocked in blocked_names
            ):
                result[str(key)] = "[REDACTED]"
                continue

            result[str(key)] = value

        return result


__all__ = [
    "ExecutionAudit",
    "ExecutionAuditError",
    "ExecutionAuditResult",
]
