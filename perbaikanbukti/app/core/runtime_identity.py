"""Content identity captured once when the application process imports its code."""
from __future__ import annotations

import hashlib
import os
import sys
import threading
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.observability.context import current_ids
from app.core.runtime_build_provenance import (
    BuildDefinition, BuildInput, BuildProvenanceOwner, ProcessBinding,
    assess_untrusted_build_provenance,
)

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


# This is an import-time disk snapshot, not proof of loaded bytes or execution
# closure. Keep it separate from server-owned artifact provenance and full build.
BUILD_ID = source_build_id()


@dataclass(frozen=True)
class RuntimeInstanceIdentity:
    process_id: int
    runtime_instance_id: str
    captured_at: str
    working_directory: str | None


def _new_runtime_instance() -> RuntimeInstanceIdentity:
    try:
        directory = os.getcwd()
    except OSError:
        directory = None
    return RuntimeInstanceIdentity(os.getpid(), uuid4().hex,
                                   datetime.now(timezone.utc).isoformat(), directory)


_instance_lock = threading.Lock()
_runtime_instance = _new_runtime_instance()


def _after_fork() -> None:
    # A fork must not inherit either its parent's identity or a locked mutex.
    global _instance_lock, _runtime_instance
    _instance_lock = threading.Lock()
    _runtime_instance = _new_runtime_instance()


if hasattr(os, 'register_at_fork'):
    os.register_at_fork(after_in_child=_after_fork)


def current_runtime_instance() -> RuntimeInstanceIdentity:
    global _runtime_instance
    with _instance_lock:
        if _runtime_instance.process_id != os.getpid():
            _runtime_instance = _new_runtime_instance()
        return _runtime_instance


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
    invocation_id: str = ''
    runtime_instance_id: str | None = None
    instance_captured_at: str | None = None
    working_directory: str | None = None
    request_id_source: str = 'STANDALONE'
    actual_model: str | None = None
    identity_status: str = 'NOT_VERIFIED'
    confirmation_source: str = 'NONE'
    fallback_status: str = 'NOT_ATTEMPTED'

    def with_response(self, reported_model, *, completed: bool = True):
        actual = (reported_model if isinstance(reported_model, str) and
                  0 < len(reported_model) <= 256 and reported_model.strip() and
                  all(ord(char) >= 32 for char in reported_model) else None)
        instance = current_runtime_instance()
        bound = (self.process_id == instance.process_id and
                 self.runtime_instance_id == instance.runtime_instance_id and
                 bool(self.invocation_id))
        status = ('NOT_VERIFIED' if actual is None or not completed or not bound else
                  'RUNTIME_CONFIRMED' if actual == self.payload_model else 'MISMATCH')
        return replace(self, actual_model=actual, identity_status=status,
                       confirmation_source='PROVIDER_RESPONSE' if actual is not None else 'NONE')

    def safe_dump(self) -> dict:
        return asdict(self)


def capture_model_identity(*, provider_id: str, selected_model: str,
                           configuration=None, requested_model=None,
                           override_source: str = 'DEFAULT') -> ModelExecutionIdentity:
    """Bind existing request context and loaded build to one provider invocation."""
    configured = configuration.llm.model if configuration is not None else None
    source = next((p.source for p in configuration.provenance if p.field == 'llm.model'),
                  'DEFAULT') if configuration is not None else 'DEFAULT'
    fingerprint = (hashlib.sha256(configuration.canonical_json().encode('utf-8')).hexdigest()
                   if configuration is not None else None)
    instance = current_runtime_instance()
    invocation_id = uuid4().hex
    contextual_id = current_ids()['request_id']
    contextual = isinstance(contextual_id, str) and contextual_id not in ('', '-')
    return ModelExecutionIdentity(
        request_id=contextual_id if contextual else invocation_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        build_id=BUILD_ID, process_id=instance.process_id, executable=sys.executable,
        invocation_id=invocation_id, runtime_instance_id=instance.runtime_instance_id,
        instance_captured_at=instance.captured_at, working_directory=instance.working_directory,
        request_id_source='REQUEST_CONTEXT' if contextual else 'STANDALONE',
        provider_id=provider_id, configured_model=configured,
        effective_model=configured if configured is not None else selected_model,
        configuration_source=source, configuration_fingerprint=fingerprint,
        selected_model=selected_model, requested_model=requested_model,
        override_source=override_source, payload_model=selected_model,
    )
