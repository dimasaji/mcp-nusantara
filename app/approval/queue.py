"""Human approval queue. Persetujuan terikat pada hash payload & sekali pakai."""
from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from app.approval.audit_trail import AuditTrail
from app.observability.context import new_id

PENDING, APPROVED, REJECTED, CHANGES, CONSUMED, EXPIRED = (
    "pending", "approved", "rejected", "request_changes", "consumed", "expired")
_DECISIONS = {"approved": APPROVED, "rejected": REJECTED, "request_changes": CHANGES}


def payload_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


class ApprovalError(Exception):
    pass


@dataclass
class ApprovalRequest:
    approval_id: str
    kind: str
    payload_hash: str
    summary: dict[str, Any]
    risk: str
    requested_by: str
    created_at: datetime
    expires_at: datetime
    status: str = PENDING
    reviewer: str | None = None
    reason: str | None = None
    decided_at: datetime | None = None
    history: list[str] = field(default_factory=list)


class ApprovalQueue:
    def __init__(self, audit: AuditTrail | None = None, ttl_minutes: int = 60):
        self.audit = audit or AuditTrail()
        self.ttl = timedelta(minutes=ttl_minutes)
        self._items: dict[str, ApprovalRequest] = {}
        self._lock = threading.Lock()

    def submit(self, kind: str, payload: Any, *, risk: str, requested_by: str,
               summary: dict[str, Any] | None = None) -> ApprovalRequest:
        now = datetime.now(timezone.utc)
        req = ApprovalRequest(new_id("apr"), kind, payload_hash(payload), summary or {}, risk,
                              requested_by, now, now + self.ttl)
        with self._lock:
            self._items[req.approval_id] = req
        self.audit.record("approval.submitted", approval_id=req.approval_id, kind=kind,
                          risk=risk, requested_by=requested_by, summary=req.summary)
        return req

    def get(self, approval_id: str) -> ApprovalRequest | None:
        with self._lock:
            return self._items.get(approval_id)

    def pending(self) -> list[ApprovalRequest]:
        with self._lock:
            return [r for r in self._items.values() if r.status == PENDING]

    def decide(self, approval_id: str, *, reviewer: str, decision: str, reason: str) -> ApprovalRequest:
        if decision not in _DECISIONS:
            raise ApprovalError(f"decision harus salah satu dari {sorted(_DECISIONS)}")
        if not reason.strip():
            raise ApprovalError("alasan wajib diisi")
        with self._lock:
            req = self._items.get(approval_id)
            if req is None:
                raise ApprovalError("approval tidak ditemukan")
            if req.status != PENDING:
                raise ApprovalError(f"approval sudah berstatus {req.status}")
            if reviewer == req.requested_by:
                raise ApprovalError("reviewer tidak boleh sama dengan peminta")
            if datetime.now(timezone.utc) > req.expires_at:
                req.status = EXPIRED
                raise ApprovalError("approval kedaluwarsa")
            req.status, req.reviewer, req.reason = _DECISIONS[decision], reviewer, reason
            req.decided_at = datetime.now(timezone.utc)
        self.audit.record("approval.decided", approval_id=approval_id, reviewer=reviewer,
                          decision=decision, reason=reason, risk=req.risk)
        return req

    def consume(self, approval_id: str, payload: Any) -> bool:
        """True hanya jika approved, belum kedaluwarsa, payload identik; sekali pakai."""
        with self._lock:
            req = self._items.get(approval_id)
            ok = (req is not None and req.status == APPROVED
                  and datetime.now(timezone.utc) <= req.expires_at
                  and req.payload_hash == payload_hash(payload))
            if ok:
                req.status = CONSUMED
        self.audit.record("approval.consume", approval_id=approval_id, granted=bool(ok))
        return bool(ok)
