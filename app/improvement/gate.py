"""Phase 19 - gerbang pengembangan V1.x: hanya change request approved + test/rollback plan + baseline.
Modul ini tidak menjalankan git; ia memvalidasi syarat dan mencatat versi (V1.0 tidak pernah dihapus)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.approval.change_request import ChangeRequest
from app.research.improvement import Proposal

BRANCH_RE = re.compile(r"^feature/improvement-\d{4}$")
_VERSION_RE = re.compile(r"^\d+\.\d+(-rc\d+)?$")
_TRANSITIONS = {"candidate": {"validated", "abandoned"}, "validated": {"released", "abandoned"},
                "released": {"stable", "rolled_back"}, "stable": set(), "rolled_back": set(), "abandoned": set()}


class GateBlocked(RuntimeError):
    def __init__(self, blockers: list[str]):
        super().__init__("; ".join(blockers))
        self.blockers = blockers


class VersionRegistry:
    def __init__(self, path: Path):
        self.path = Path(path)
        if self.path.exists():
            self.data = json.loads(self.path.read_text("utf-8"))
        else:
            self.data = {"1.0": {"status": "stable", "parent": None, "change_requests": [],
                                 "created_at": datetime.now(timezone.utc).isoformat()}}
            self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), "utf-8")

    def register(self, version: str, parent: str, change_request_id: str) -> None:
        if not _VERSION_RE.match(version):
            raise ValueError("format versi tidak valid")
        if version in self.data:
            raise ValueError("versi sudah ada (tidak boleh ditimpa)")
        if parent not in self.data:
            raise ValueError("parent tidak dikenal")
        self.data[version] = {"status": "candidate", "parent": parent, "change_requests": [change_request_id],
                              "created_at": datetime.now(timezone.utc).isoformat()}
        self._save()

    def transition(self, version: str, status: str) -> None:
        cur = self.data[version]["status"]
        if status not in _TRANSITIONS.get(cur, set()):
            raise ValueError(f"transisi {cur} -> {status} tidak diizinkan")
        self.data[version]["status"] = status
        self._save()

    def status(self, version: str) -> str | None:
        return self.data.get(version, {}).get("status")


@dataclass
class DevBranch:
    name: str
    target_version: str
    git_commands: list[str]


def branch_name(proposal_id: str) -> str:
    m = re.fullmatch(r"PROPOSAL-(\d{4})", proposal_id)
    if not m:
        raise ValueError("proposal_id tidak valid")
    return f"feature/improvement-{m.group(1)}"


def check(cr: ChangeRequest, p: Proposal, baseline_name: str | None) -> list[str]:
    b: list[str] = []
    if cr.status != "open":
        b.append("change request tidak berstatus open")
    if cr.proposal_id != p.proposal_id:
        b.append("change request tidak cocok dengan proposal")
    if not p.test_plan.strip():
        b.append("test plan kosong")
    if not p.rollback_plan.strip():
        b.append("rollback plan kosong")
    if not baseline_name:
        b.append("baseline evaluasi tidak tersedia")
    return b


def start(cr: ChangeRequest, p: Proposal, baseline_name: str | None, registry: VersionRegistry,
          target_version: str, parent: str = "1.0") -> DevBranch:
    blockers = check(cr, p, baseline_name)
    if blockers:
        raise GateBlocked(blockers)
    name = branch_name(p.proposal_id)
    registry.register(target_version, parent, cr.change_request_id)
    cr.status = "in_development"
    return DevBranch(name, target_version, [f"git checkout -b {name} v{parent}",
                                            "# lakukan perubahan, jalankan tes + evaluasi, buka review",
                                            f"git tag v{target_version}  # setelah lolos Phase 20"])
