"""
Human Handoff Engine - Escalation ke manusia.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.handoff.schemas import HandoffLevel, HandoffRequest, HandoffStatus


class HandoffEngine:
    """
    Engine untuk manajemen human handoff.
    """

    def __init__(self):
        self._requests: Dict[str, HandoffRequest] = {}

    def create_request(
        self,
        reason: str,
        context: Dict[str, Any] = None,
        requester_role: str = "assistant",
        level: HandoffLevel = HandoffLevel.NORMAL,
        summary: Optional[str] = None,
        suggested_action: Optional[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> HandoffRequest:
        """
        Buat handoff request baru.
        """
        request_id = uuid.uuid4().hex[:12]

        # Handle string level input
        if isinstance(level, str):
            level = HandoffLevel(level)

        context = context or {}

        request = HandoffRequest(
            handoff_id=request_id,
            reason=reason,
            context=context or {},
            requester_role=requester_role,
            level=level.value,
            status=HandoffStatus.PENDING,
            created_at=datetime.now(timezone.utc).isoformat(),
            summary=summarize_context(context) if summary is None else summary,
            suggested_action=suggested_action,
            metadata=metadata or {},
        )

        self._requests[request_id] = request
        return request

    def get_request(self, handoff_id: str) -> Optional[HandoffRequest]:
        """Dapatkan request oleh ID."""
        return self._requests.get(handoff_id)

    def update_status(
        self,
        handoff_id: str,
        status: HandoffStatus,
        note: Optional[str] = None,
    ) -> Optional[HandoffRequest]:
        """Update status request."""
        request = self._requests.get(handoff_id)
        if request is None:
            return None

        request.status = status.value
        request.updated_at = datetime.utcnow().isoformat()
        if note:
            request.note = note

        return request

    def escalate(
        self,
        handoff_id: str,
        level: HandoffLevel = HandoffLevel.HIGH,
    ) -> Optional[HandoffRequest]:
        """Escalasi request ke level lebih tinggi."""
        request = self._requests.get(handoff_id)
        if request is None:
            return None

        old_level = request.level
        request.level = level.value
        request.escalation_count = request.escalation_count + 1
        request.escalated_at = datetime.utcnow().isoformat()
        request.status = HandoffStatus.PENDING

        return request

    def list_pending(self) -> List[HandoffRequest]:
        """List semua request yang pending."""
        return [
            req for req in self._requests.values()
            if req.status == HandoffStatus.PENDING.value
        ]

    def list_by_status(self, status: HandoffStatus) -> List[HandoffRequest]:
        """List request berdasarkan status."""
        return [
            req for req in self._requests.values()
            if req.status == status.value
        ]

    def resolve(self, handoff_id: str, resolution: str) -> Optional[HandoffRequest]:
        """Resolve request dengan resolusi."""
        request = self._requests.get(handoff_id)
        if request is None:
            return None

        request.status = HandoffStatus.RESOLVED.value
        request.resolution = resolution
        request.resolved_at = datetime.utcnow().isoformat()

        return request

    def cancel(self, handoff_id: str) -> Optional[HandoffRequest]:
        """Batalkan request."""
        request = self._requests.get(handoff_id)
        if request is None:
            return None

        request.status = HandoffStatus.CANCELLED.value
        request.updated_at = datetime.utcnow().isoformat()

        return request

    def get_stats(self) -> Dict[str, Any]:
        """Dapatkan statistik handoff."""
        all_requests = list(self._requests.values())
        pending = sum(1 for r in all_requests if r.status == HandoffStatus.PENDING.value)
        resolved = sum(1 for r in all_requests if r.status == HandoffStatus.RESOLVED.value)
        cancelled = sum(1 for r in all_requests if r.status == HandoffStatus.CANCELLED.value)

        by_level = {}
        for r in all_requests:
            level = r.level
            by_level[level] = by_level.get(level, 0) + 1

        return {
            "total_requests": len(all_requests),
            "pending": pending,
            "resolved": resolved,
            "cancelled": cancelled,
            "by_level": by_level,
        }


def summarize_context(context: Dict[str, Any]) -> str:
    """Buat ringkasan dari context."""
    parts = []
    if "problem" in context:
        parts.append(f"Masalah: {context['problem']}")
    if "urgency" in context:
        parts.append(f"Ked urgency: {context['urgency']}")
    if "user_message" in context:
        msg = str(context["user_message"])
        if len(msg) > 200:
            msg = msg[:200] + "..."
        parts.append(f"Pesan: {msg}")
    return ". ".join(parts) if parts else "Tidak ada konteks spesifik"


_default_engine = HandoffEngine()


def create_handoff_engine() -> HandoffEngine:
    return HandoffEngine()


def get_default_handoff_engine() -> HandoffEngine:
    return _default_engine


def create_handoff_request(
    reason: str,
    context: Dict[str, Any] = None,
    requester_role: str = "assistant",
    level: HandoffLevel = HandoffLevel.NORMAL,
) -> HandoffRequest:
    """Buat handoff request (shortcut)."""
    engine = get_default_handoff_engine()
    return engine.create_request(
        reason=reason,
        context=context,
        requester_role=requester_role,
        level=level,
    )
