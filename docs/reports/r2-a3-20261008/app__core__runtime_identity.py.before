"""Content identity captured once when the application process imports its code."""
from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def source_build_id(root: Path = ROOT) -> str:
    """Hash executable source/assets, never environment files or runtime data."""
    root = root.resolve()
    files = [p for p in (root / "app").rglob("*")
             if p.is_file() and p.suffix in {".py", ".json", ".html", ".css", ".js"}]
    files += [root / "pyproject.toml", root / "nusantara-models/indobert_worker.py"]
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            path.resolve().relative_to(root)
        except ValueError:
            continue
        name = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()


# Requests always identify the source loaded at process startup, even if files
# are edited later. A new build requires a new process.
BUILD_ID = source_build_id()


@dataclass(frozen=True)
class ModelExecutionIdentity:
    """Per-invocation evidence; a provider report is not a model-weight attestation.

    Kept internal to provider responses; public API projection stays unchanged.
    Capture before the first await so mutable provider labels cannot rewrite it.
    """
    request_id: str
    timestamp: str
    build_id: str
    process_id: int
    executable: str
    provider_id: str
    configured_model: str | None
    effective_model: str
    configuration_source: str
    configuration_fingerprint: str | None
    selected_model: str
    requested_model: str | None
    override_source: str
    payload_model: str
    actual_model: str | None = None
    identity_status: str = 'NOT_VERIFIED'
    confirmation_source: str = 'NONE'
    fallback_status: str = 'NOT_ATTEMPTED'

    def with_response(self, reported_model, *, completed: bool = True):
        actual = (reported_model if isinstance(reported_model, str) and
                  0 < len(reported_model) <= 256 and reported_model.strip() and
                  all(ord(char) >= 32 for char in reported_model) else None)
        status = ('NOT_VERIFIED' if actual is None or not completed else
                  'RUNTIME_CONFIRMED' if actual == self.payload_model else 'MISMATCH')
        return replace(self, actual_model=actual, identity_status=status,
                       confirmation_source='PROVIDER_RESPONSE' if actual is not None else 'NONE')

    def safe_dump(self) -> dict:
        return asdict(self)


def capture_model_identity(*, provider_id: str, selected_model: str,
                           configuration=None, requested_model=None,
                           override_source: str = 'DEFAULT') -> ModelExecutionIdentity:
    """Reuse the existing loaded build identity; no model/config loader or I/O."""
    configured = configuration.llm.model if configuration is not None else None
    source = next((p.source for p in configuration.provenance if p.field == 'llm.model'),
                  'DEFAULT') if configuration is not None else 'DEFAULT'
    fingerprint = (hashlib.sha256(configuration.canonical_json().encode('utf-8')).hexdigest()
                   if configuration is not None else None)
    return ModelExecutionIdentity(
        request_id=uuid4().hex, timestamp=datetime.now(timezone.utc).isoformat(),
        build_id=BUILD_ID, process_id=os.getpid(), executable=sys.executable,
        provider_id=provider_id, configured_model=configured,
        effective_model=configured if configured is not None else selected_model,
        configuration_source=source, configuration_fingerprint=fingerprint,
        selected_model=selected_model, requested_model=requested_model,
        override_source=override_source, payload_model=selected_model,
    )
