from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import tempfile

from app.developer_core.execution_plan import ExecutionPlan


SENSITIVE_NAMES = {
    ".env",
    ".git",
    ".gitconfig",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}


class ControlledPatchError(Exception):
    """Raised when a controlled patch cannot be safely applied."""


@dataclass(frozen=True)
class PatchResult:
    execution_id: str
    change_id: str
    target_file: str
    sha256_before: str
    sha256_after: str
    bytes_before: int
    bytes_after: int

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "change_id": self.change_id,
            "target_file": self.target_file,
            "sha256_before": self.sha256_before,
            "sha256_after": self.sha256_after,
            "bytes_before": self.bytes_before,
            "bytes_after": self.bytes_after,
        }


class ControlledPatchExecutor:
    """
    Gate 16.5 controlled patch executor.

    Deliberately limited:
    - one exact approved target file at a time
    - no shell
    - no subprocess
    - no arbitrary commands
    - no absolute paths
    - no traversal
    - no sensitive files
    - expected SHA-256 must match
    - atomic replacement
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root).resolve()

    def _resolve_target(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str):
            raise ControlledPatchError(
                "target_file harus berupa string"
            )

        value = relative_path.strip()

        if not value:
            raise ControlledPatchError(
                "target_file kosong"
            )

        candidate = Path(value)

        if candidate.is_absolute():
            raise ControlledPatchError(
                "absolute path diblokir"
            )

        if any(part == ".." for part in candidate.parts):
            raise ControlledPatchError(
                "path traversal diblokir"
            )

        if any(
            part.lower() in SENSITIVE_NAMES
            for part in candidate.parts
        ):
            raise ControlledPatchError(
                "sensitive path diblokir"
            )

        resolved = (self.workspace_root / candidate).resolve()

        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise ControlledPatchError(
                "target berada di luar workspace"
            ) from exc

        return resolved

    @staticmethod
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as handle:
            for chunk in iter(
                lambda: handle.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        return digest.hexdigest()

    def apply(
        self,
        plan: ExecutionPlan,
        target_file: str,
        new_content: bytes,
        *,
        expected_sha256: str,
    ) -> PatchResult:

        if not isinstance(plan, ExecutionPlan):
            raise ControlledPatchError(
                "ExecutionPlan tidak valid"
            )

        if not plan.approved:
            raise ControlledPatchError(
                "ExecutionPlan belum approved"
            )

        if not isinstance(new_content, bytes):
            raise ControlledPatchError(
                "new_content harus berupa bytes"
            )

        if not isinstance(expected_sha256, str):
            raise ControlledPatchError(
                "expected_sha256 harus berupa string"
            )

        if not expected_sha256.strip():
            raise ControlledPatchError(
                "expected_sha256 kosong"
            )

        targets = tuple(plan.target_files)

        if len(targets) != 1:
            raise ControlledPatchError(
                "Gate 16.5 hanya mengizinkan satu target file per operasi"
            )

        if target_file != targets[0]:
            raise ControlledPatchError(
                "target_file tidak sama dengan target_files yang disetujui"
            )

        target = self._resolve_target(target_file)

        if not target.is_file():
            raise ControlledPatchError(
                "target file tidak ditemukan"
            )

        before_hash = self.sha256(target)

        if before_hash != expected_sha256:
            raise ControlledPatchError(
                "SHA-256 BEFORE tidak sesuai"
            )

        before_size = target.stat().st_size

        fd, temp_name = tempfile.mkstemp(
            prefix=".nusantara-patch-",
            suffix=".tmp",
            dir=str(target.parent),
        )

        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(new_content)
                handle.flush()
                os.fsync(handle.fileno())

            temp_path = Path(temp_name)

            after_hash = self.sha256(temp_path)

            if after_hash != hashlib.sha256(new_content).hexdigest():
                raise ControlledPatchError(
                    "SHA-256 temporary file tidak sesuai"
                )

            os.replace(temp_path, target)

            actual_after_hash = self.sha256(target)

            if actual_after_hash != after_hash:
                raise ControlledPatchError(
                    "SHA-256 AFTER tidak sesuai"
                )

            return PatchResult(
                execution_id=plan.execution_id,
                change_id=plan.change_id,
                target_file=target_file,
                sha256_before=before_hash,
                sha256_after=actual_after_hash,
                bytes_before=before_size,
                bytes_after=len(new_content),
            )

        except Exception:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
            raise
