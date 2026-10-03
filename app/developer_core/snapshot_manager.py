"""Nusantara V1 - Gate 16.4 Snapshot / Rollback.

Controlled snapshot manager.

Contract:
    Approved ExecutionPlan
        -> approval verification
        -> target verification
        -> SHA-256 BEFORE
        -> immutable snapshot
        -> rollback only approved target files

This module NEVER:
- executes shell commands
- executes PowerShell/cmd
- patches source
- writes outside snapshot storage
- snapshots the whole repository
- restores files outside approved target_files
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.developer_core.execution_plan import ExecutionPlan


SENSITIVE_NAMES = frozenset({
    ".env",
    ".git",
    ".gitconfig",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
})


class SnapshotError(RuntimeError):
    """Snapshot/rollback operation rejected."""


@dataclass(frozen=True)
class SnapshotFile:
    relative_path: str
    snapshot_path: str
    sha256_before: str
    size_before: int

    def to_dict(self) -> dict:
        return {
            "relative_path": self.relative_path,
            "snapshot_path": self.snapshot_path,
            "sha256_before": self.sha256_before,
            "size_before": self.size_before,
        }


@dataclass(frozen=True)
class SnapshotManifest:
    snapshot_id: str
    execution_id: str
    change_id: str
    workspace_root: str
    snapshot_root: str
    target_files: tuple[str, ...]
    files: tuple[SnapshotFile, ...]
    rollback_boundary: str

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "execution_id": self.execution_id,
            "change_id": self.change_id,
            "workspace_root": self.workspace_root,
            "snapshot_root": self.snapshot_root,
            "target_files": list(self.target_files),
            "files": [f.to_dict() for f in self.files],
            "rollback_boundary": self.rollback_boundary,
        }


class SnapshotManager:
    """Creates and restores snapshots for exact approved targets."""

    def __init__(
        self,
        workspace_root: str | Path,
        snapshot_root: str | Path | None = None,
    ):
        self.workspace_root = Path(workspace_root).resolve()

        if snapshot_root is None:
            snapshot_root = (
                self.workspace_root
                / "data"
                / "execution_snapshots"
            )

        self.snapshot_root = Path(snapshot_root).resolve()

        self._ensure_inside_workspace_or_snapshot(
            self.snapshot_root
        )

    # ------------------------------------------------------------------
    # PATH SAFETY
    # ------------------------------------------------------------------

    def _resolve_target(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str):
            raise SnapshotError("target path harus string")

        if not relative_path.strip():
            raise SnapshotError("target path kosong")

        normalized = relative_path.replace("\\", "/")

        if normalized.startswith("/"):
            raise SnapshotError(
                f"absolute path diblokir: {relative_path}"
            )

        if len(normalized) >= 2 and normalized[1] == ":":
            raise SnapshotError(
                f"Windows absolute path diblokir: {relative_path}"
            )

        parts = Path(normalized).parts

        if ".." in parts:
            raise SnapshotError(
                f"path traversal diblokir: {relative_path}"
            )

        for part in parts:
            if part.lower() in {
                name.lower() for name in SENSITIVE_NAMES
            }:
                raise SnapshotError(
                    f"sensitive path diblokir: {relative_path}"
                )

        target = (self.workspace_root / Path(*parts)).resolve()

        try:
            target.relative_to(self.workspace_root)
        except ValueError as exc:
            raise SnapshotError(
                f"target keluar workspace: {relative_path}"
            ) from exc

        return target

    def _ensure_inside_workspace_or_snapshot(
        self,
        path: Path,
    ) -> None:
        try:
            path.relative_to(self.workspace_root)
        except ValueError as exc:
            raise SnapshotError(
                f"path berada di luar workspace: {path}"
            ) from exc

    # ------------------------------------------------------------------
    # HASH
    # ------------------------------------------------------------------

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as handle:
            for chunk in iter(
                lambda: handle.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        return digest.hexdigest()

    # ------------------------------------------------------------------
    # SNAPSHOT
    # ------------------------------------------------------------------

    def create_snapshot(
        self,
        plan: ExecutionPlan,
    ) -> SnapshotManifest:

        if not isinstance(plan, ExecutionPlan):
            raise SnapshotError(
                "ExecutionPlan tidak valid"
            )

        if plan.approved is not True:
            raise SnapshotError(
                "snapshot membutuhkan approved=True"
            )

        if not plan.target_files:
            raise SnapshotError(
                "target_files kosong"
            )

        if not plan.rollback_boundary.strip():
            raise SnapshotError(
                "rollback_boundary wajib diisi"
            )

        # Validate ALL targets before creating anything.
        resolved_targets: list[tuple[str, Path]] = []

        for relative_path in plan.target_files:
            target = self._resolve_target(relative_path)

            if not target.exists():
                raise SnapshotError(
                    f"target tidak ditemukan: {relative_path}"
                )

            if not target.is_file():
                raise SnapshotError(
                    f"target bukan file: {relative_path}"
                )

            resolved_targets.append(
                (relative_path, target)
            )

        snapshot_id = (
            "snap_"
            + uuid.uuid4().hex
        )

        snapshot_dir = (
            self.snapshot_root
            / snapshot_id
        )

        snapshot_dir.mkdir(
            parents=True,
            exist_ok=False,
        )

        snapshot_files: list[SnapshotFile] = []

        try:
            for relative_path, target in resolved_targets:

                destination = (
                    snapshot_dir
                    / Path(relative_path)
                ).resolve()

                try:
                    destination.relative_to(
                        snapshot_dir
                    )
                except ValueError as exc:
                    raise SnapshotError(
                        "snapshot target keluar snapshot boundary"
                    ) from exc

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                sha = self._sha256(target)
                size = target.stat().st_size

                # copy2 preserves file metadata.
                shutil.copy2(
                    target,
                    destination,
                )

                # Verify snapshot integrity immediately.
                copied_sha = self._sha256(
                    destination
                )

                if copied_sha != sha:
                    raise SnapshotError(
                        f"snapshot hash mismatch: {relative_path}"
                    )

                snapshot_files.append(
                    SnapshotFile(
                        relative_path=relative_path,
                        snapshot_path=str(
                            destination.relative_to(
                                self.snapshot_root
                            )
                        ),
                        sha256_before=sha,
                        size_before=size,
                    )
                )

            manifest = SnapshotManifest(
                snapshot_id=snapshot_id,
                execution_id=plan.execution_id,
                change_id=plan.change_id,
                workspace_root=str(
                    self.workspace_root
                ),
                snapshot_root=str(
                    snapshot_dir
                ),
                target_files=tuple(
                    plan.target_files
                ),
                files=tuple(
                    snapshot_files
                ),
                rollback_boundary=(
                    plan.rollback_boundary
                ),
            )

            manifest_path = (
                snapshot_dir
                / "manifest.json"
            )

            manifest_path.write_text(
                json.dumps(
                    manifest.to_dict(),
                    indent=2,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            return manifest

        except Exception:
            shutil.rmtree(
                snapshot_dir,
                ignore_errors=True,
            )
            raise

    # ------------------------------------------------------------------
    # ROLLBACK
    # ------------------------------------------------------------------

    def rollback(
        self,
        manifest: SnapshotManifest,
    ) -> tuple[str, ...]:

        if not isinstance(
            manifest,
            SnapshotManifest,
        ):
            raise SnapshotError(
                "SnapshotManifest tidak valid"
            )

        snapshot_dir = (
            self.snapshot_root
            / manifest.snapshot_id
        ).resolve()

        try:
            snapshot_dir.relative_to(
                self.snapshot_root
            )
        except ValueError as exc:
            raise SnapshotError(
                "snapshot keluar snapshot boundary"
            ) from exc

        if not snapshot_dir.is_dir():
            raise SnapshotError(
                "snapshot tidak ditemukan"
            )

        restored: list[str] = []

        # Verify all snapshot files before modifying
        # any workspace file.
        prepared: list[
            tuple[SnapshotFile, Path, Path]
        ] = []

        for item in manifest.files:

            target = self._resolve_target(
                item.relative_path
            )

            source = (
                self.snapshot_root
                / item.snapshot_path
            ).resolve()

            try:
                source.relative_to(
                    snapshot_dir
                )
            except ValueError as exc:
                raise SnapshotError(
                    "snapshot source keluar snapshot boundary"
                ) from exc

            if not source.is_file():
                raise SnapshotError(
                    f"snapshot file hilang: {item.relative_path}"
                )

            source_sha = self._sha256(source)

            if source_sha != item.sha256_before:
                raise SnapshotError(
                    f"snapshot integrity mismatch: "
                    f"{item.relative_path}"
                )

            prepared.append(
                (item, source, target)
            )

        # Restore only approved target files.
        for item, source, target in prepared:

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temporary = target.with_name(
                target.name
                + ".nusantara-rollback.tmp"
            )

            try:
                shutil.copy2(
                    source,
                    temporary,
                )

                restored_sha = self._sha256(
                    temporary
                )

                if restored_sha != item.sha256_before:
                    raise SnapshotError(
                        f"rollback hash mismatch: "
                        f"{item.relative_path}"
                    )

                os.replace(
                    temporary,
                    target,
                )

                restored.append(
                    item.relative_path
                )

            finally:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

        return tuple(restored)


__all__ = [
    "SnapshotError",
    "SnapshotFile",
    "SnapshotManifest",
    "SnapshotManager",
]
