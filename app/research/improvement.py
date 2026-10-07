"""Phase 17 - improvement proposal. approval_required selalu True; tidak menyentuh production."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from app.research.gap_detection import GapCandidate

_RISKS = ("low", "medium", "high", "critical")


class ProposalInvalid(ValueError):
    pass


@dataclass
class Proposal:
    proposal_id: str
    problem: str
    evidence: list[str]
    root_cause: str
    proposed_change: str
    affected_components: list[str]
    affected_files: list[str]
    risk: str
    expected_benefit: str
    experiment_result: dict[str, Any] | None
    test_plan: str
    rollback_plan: str
    approval_required: bool = True


class ProposalEngine:
    def __init__(self, path: Path | None = None) -> None:
        self._n = 0
        self.proposals: dict[str, Proposal] = {}
        self.path = path
        if path and path.exists():
            for raw in json.loads(path.read_text("utf-8")):
                proposal = Proposal(**raw)
                self.proposals[proposal.proposal_id] = proposal
                self._n = max(self._n, int(proposal.proposal_id.split("-")[-1]))

    def create(self, *, problem: str, evidence: list[str], root_cause: str, proposed_change: str,
               affected_components: list[str], affected_files: list[str] | None = None, risk: str = "medium",
               expected_benefit: str = "", experiment_result: dict[str, Any] | None = None,
               test_plan: str = "", rollback_plan: str = "") -> Proposal:
        for name, val in (("problem", problem), ("root_cause", root_cause), ("proposed_change", proposed_change),
                          ("test_plan", test_plan), ("rollback_plan", rollback_plan)):
            if not val.strip():
                raise ProposalInvalid(f"{name} wajib diisi")
        if not evidence or not affected_components:
            raise ProposalInvalid("evidence dan affected_components wajib")
        if risk not in _RISKS:
            raise ProposalInvalid("risk tidak valid")
        if experiment_result and experiment_result.get("verdict") == "REGRESSION":
            raise ProposalInvalid("hasil eksperimen REGRESSION tidak boleh diajukan")
        self._n += 1
        p = Proposal(f"PROPOSAL-{self._n:04d}", problem, list(evidence), root_cause, proposed_change,
                     list(affected_components), list(affected_files or []), risk, expected_benefit,
                     experiment_result, test_plan, rollback_plan, True)
        self.proposals[p.proposal_id] = p
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps([asdict(x) for x in self.proposals.values()], ensure_ascii=False), "utf-8")
            temporary.replace(self.path)
        return p

    def from_gap(self, gap: GapCandidate, *, proposed_change: str, root_cause: str,
                 affected_components: list[str], test_plan: str, rollback_plan: str, **kw: Any) -> Proposal:
        return self.create(problem=gap.description, evidence=gap.evidence, root_cause=root_cause,
                           proposed_change=proposed_change, affected_components=affected_components,
                           test_plan=test_plan, rollback_plan=rollback_plan, **kw)
