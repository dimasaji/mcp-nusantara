"""Phase 21 - manajemen rilis: backup, checklist, release notes, rollback. Tidak melakukan deploy."""
from __future__ import annotations

import tarfile
import hashlib
import re
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
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", label):
        raise ValueError("invalid backup label")
    if src.resolve() == out.resolve() or src.resolve() in out.resolve().parents:
        raise ValueError("backup destination must be outside source")
    if src.is_symlink() or any(p.is_symlink() for p in src.rglob("*")):
        raise ValueError("backup source must not contain symbolic links")
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"backup-{label}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.tar.gz"
    with tarfile.open(dest, "w:gz") as tf:
        tf.add(src, arcname=src.name)
    dest.with_suffix(dest.suffix + ".sha256").write_text(_sha256(dest), "ascii")
    return dest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def restore_backup(archive: Path, destination: Path, *, max_bytes: int = 1_000_000_000) -> Path:
    """Restore verified data to an empty destination; never overwrite active data."""
    archive, destination = Path(archive), Path(destination)
    expected = archive.with_suffix(archive.suffix + ".sha256").read_text("ascii").strip()
    if expected != _sha256(archive):
        raise ValueError("backup checksum mismatch")
    if destination.is_symlink() or (destination.exists() and any(destination.iterdir())):
        raise ValueError("restore destination must be empty and not a symlink")
    root = destination.resolve()
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        if sum(m.size for m in members) > max_bytes:
            raise ValueError("backup exceeds restore size limit")
        for member in members:
            target = (root / member.name).resolve()
            if (member.name.startswith(("/", "\\")) or "\\" in member.name or ":" in member.name
                    or root not in target.parents or not (member.isfile() or member.isdir())):
                raise ValueError("unsafe backup member")
        destination.mkdir(parents=True, exist_ok=True)
        source.extractall(destination, members=members, filter="data")
    return destination


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
