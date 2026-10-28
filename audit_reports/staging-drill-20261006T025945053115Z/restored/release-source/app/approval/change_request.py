"""Phase 18 - human approval untuk proposal R&D.
PROPOSAL -> RISK ASSESSMENT -> HUMAN REVIEW -> (approved) -> CHANGE REQUEST. Tidak ada jalur R&D -> production."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from app.approval.queue import APPROVED, CONSUMED, ApprovalQueue, ApprovalRequest
from app.observability.context import new_id
from app.research.improvement import Proposal

_HIGH_AREAS = ("core", "policy", "security", "approval", "governance", "memory", "auth")
_ORDER = ["low", "medium", "high", "critical"]


class NotApprovedForChange(PermissionError):
    pass


def assess_risk(p: Proposal) -> str:
    """Risiko efektif = maks(risiko yang dideklarasikan, risiko dari area terdampak). Tidak bisa diturunkan."""
    touched = [s.lower() for s in (*p.affected_components, *p.affected_files)]
    computed = "high" if any(a in t for t in touched for a in _HIGH_AREAS) else "low"
    return max(p.risk, computed, key=_ORDER.index)


@dataclass
class ChangeRequest:
    change_request_id: str
    proposal_id: str
    approval_id: str
    reviewer: str
    decision_reason: str
    affected_files: list[str]
    risk: str
    rollback_plan: str
    created_at: str
    status: str = "open"


class ReviewWorkflow:
    def __init__(self, queue: ApprovalQueue):
        self.queue = queue

    def submit(self, proposal: Proposal, requested_by: str) -> ApprovalRequest:
        risk = assess_risk(proposal)
        return self.queue.submit("improvement_proposal", asdict(proposal), risk=risk, requested_by=requested_by,
                                 summary={"proposal_id": proposal.proposal_id, "problem": proposal.problem[:200],
                                          "affected_files": proposal.affected_files,
                                          "rollback_plan": proposal.rollback_plan[:300]})

    def open_change_request(self, approval_id: str, proposal: Proposal) -> ChangeRequest:
        req = self.queue.get(approval_id)
        if req is None or req.status != APPROVED:
            raise NotApprovedForChange("proposal belum disetujui")
        if not self.queue.consume(approval_id, asdict(proposal)):  # gagal jika proposal diubah setelah review
            raise NotApprovedForChange("payload proposal berubah atau approval kedaluwarsa")
        return ChangeRequest(new_id("cr"), proposal.proposal_id, approval_id, req.reviewer or "", req.reason or "",
                             list(proposal.affected_files), req.risk, proposal.rollback_plan,
                             datetime.now(timezone.utc).isoformat())
