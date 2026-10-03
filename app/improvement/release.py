"""Phase 21 - manajemen rilis: backup, checklist, release notes, rollback. Tidak melakukan deploy."""
from __future__ import annotations

import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.approval.change_request import ChangeRequest
from app.improvement.gate import VersionRegistry


def create_backup(src_dir: Path, out_dir: Path, label: str) -> Path:
    src = Path(src_dir)
    if not src.is_dir():
        raise FileNotFoundError(f"direktori sumber tidak ada: {src}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"backup-{label}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.tar.gz"
    with tarfile.open(dest, "w:gz") as tf:
        tf.add(src, arcname=src.name)
    return dest


@dataclass
class ChecklistItem:
    name: str
    ok: bool
    detail: str = ""


def release_checklist(*, version: str, registry: VersionRegistry, backup: Path | None, readiness: str,
                      project_root: Path, health_ok: bool | None) -> list[ChecklistItem]:
    root = Path(project_root)
    return [
        ChecklistItem("version terdaftar & validated", registry.status(version) == "validated",
                      str(registry.status(version))),
        ChecklistItem("readiness report PASS", readiness == "PASS", readiness),
        ChecklistItem("backup ada", bool(backup and Path(backup).exists())),
        ChecklistItem("rollback plan ada", (root / "ROLLBACK_PLAN.md").exists()),
        ChecklistItem("changelog ada", (root / "CHANGELOG.md").exists()),
        ChecklistItem("health check lulus", health_ok is True, "belum dijalankan" if health_ok is None else ""),
        ChecklistItem("V1.0 masih tersedia", registry.status("1.0") is not None),
    ]


def ready_to_release(items: list[ChecklistItem]) -> bool:
    return all(i.ok for i in items)


def generate_release_notes(version: str, crs: list[ChangeRequest]) -> str:
    lines = [f"# Release Notes {version}", "", "Perubahan (setiap butir punya persetujuan manusia):"]
    lines += [f"- {c.proposal_id} (CR {c.change_request_id}, risiko {c.risk}, reviewer {c.reviewer}): "
              f"{c.decision_reason}" for c in crs] or ["- (tidak ada)"]
    return "\n".join(lines) + "\n"


def rollback(registry: VersionRegistry, from_version: str, to_version: str = "1.0") -> list[str]:
    if registry.status(to_version) not in ("stable", "released"):
        raise ValueError("versi tujuan rollback harus stable/released")
    registry.transition(from_version, "rolled_back")
    return [f"hentikan layanan {from_version}", f"pulihkan backup data terakhir (jika ada migrasi)",
            f"jalankan {to_version}", "verifikasi /health lalu monitor"]
