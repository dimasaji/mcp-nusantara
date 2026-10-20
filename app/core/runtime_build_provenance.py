"""Closed input manifests and server-owned artifact provenance, without activation.

Artifact consumption is deliberately weaker than proof of executing a complete
Python application. No current loader supplies an execution-closure witness, so
this foundation never promotes ACTIVE_PROCESS_BUILD or Runtime Identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import PurePosixPath
import re
import threading

_ROLES = frozenset({'APPLICATION_CODE', 'STATIC_ASSET', 'DEPENDENCY', 'INTERPRETER'})
_DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')
_INSTANCE = re.compile(r'[0-9a-f]{32}\Z')
_MAX_INPUTS = 10000
_MAX_ARTIFACT_BYTES = 16 * 1024 * 1024


def _hash(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=True).encode('utf-8')
    return 'sha256:' + hashlib.sha256(encoded).hexdigest()


def _name(value) -> bool:
    if not isinstance(value, str) or not 0 < len(value) <= 512:
        return False
    path = PurePosixPath(value)
    return (not path.is_absolute() and path.as_posix() == value
            and all(part not in ('', '.', '..') for part in value.split('/'))
            and ':' not in value and '\\' not in value
            and all(ord(c) >= 32 for c in value)
            and not value.lower().endswith(('.db', '.db-wal', '.db-shm')))


@dataclass(frozen=True)
class BuildInput:
    name: str
    role: str
    digest: str


@dataclass(frozen=True)
class BuildDefinition:
    """Inventory and digests are separate; membership cannot be inferred from hashes.

    A real application definition must enumerate its transitive Python/native
    dependencies, interpreter and assets independently of the source snapshot.
    Exact inventory coverage here proves declared input coverage only. It cannot
    establish that the declaration includes every executable input of a process.
    """
    inventory: tuple[tuple[str, str], ...]
    inputs: tuple[BuildInput, ...]

    def validate(self) -> str | None:
        if type(self.inventory) is not tuple or type(self.inputs) is not tuple:
            return 'MALFORMED_BUILD_DEFINITION'
        if not 0 < len(self.inventory) <= _MAX_INPUTS or len(self.inputs) > _MAX_INPUTS:
            return 'MALFORMED_BUILD_DEFINITION'
        inventory = []
        for item in self.inventory:
            if (type(item) is not tuple or len(item) != 2 or not _name(item[0])
                    or not isinstance(item[1], str) or item[1] not in _ROLES):
                return 'MALFORMED_BUILD_DEFINITION'
            inventory.append(item)
        entries = []
        for item in self.inputs:
            if (type(item) is not BuildInput or not _name(item.name)
                    or not isinstance(item.role, str) or item.role not in _ROLES or not isinstance(item.digest, str)
                    or not _DIGEST.fullmatch(item.digest)):
                return 'MALFORMED_BUILD_DEFINITION'
            entries.append((item.name, item.role))
        if (len({name for name, _ in inventory}) != len(inventory)
                or len({name for name, _ in entries}) != len(entries)):
            return 'MALFORMED_BUILD_DEFINITION'
        if set(inventory) != set(entries) or {role for _, role in inventory} != _ROLES:
            return 'INCOMPLETE_BUILD_DEFINITION'
        return None

    def build_id(self) -> str:
        """Deterministic declared-artifact identity, never loaded-memory proof."""
        if self.validate() is not None:
            raise ValueError(self.validate())
        return _hash({'version': 1, 'inventory': sorted(self.inventory),
                      'inputs': sorted((i.name, i.role, i.digest) for i in self.inputs)})


@dataclass(frozen=True)
class ProcessBinding:
    pid: int
    process_start: str
    runtime_instance_id: str

    def valid(self) -> bool:
        if (type(self.pid) is not int or self.pid <= 0
                or not isinstance(self.process_start, str)
                or not isinstance(self.runtime_instance_id, str)
                or not _INSTANCE.fullmatch(self.runtime_instance_id)):
            return False
        try:
            start = datetime.fromisoformat(self.process_start)
            return start.tzinfo is not None and start.utcoffset() == timezone.utc.utcoffset(start)
        except ValueError:
            return False


def _result(reason, *, expected=None, observed=None, artifact_binding='NOT_VERIFIED'):
    return {'status': 'NOT_VERIFIED', 'active_process_build': 'NOT_DIRECTLY_VERIFIED',
            'runtime_identity': 'NOT_VERIFIED', 'artifact_binding': artifact_binding,
            'expected_build_id': expected, 'observed_loaded_build_id': observed,
            'coverage': 'DECLARED_ARTIFACT_INPUTS_ONLY', 'reason': reason}


class BuildProvenanceOwner:
    """Private server memory owner for bytes actually consumed by a loader.

    Instantiate only inside a trusted composition/loader, never from request JSON.
    No HTTP adapter, global owner, permit, process launch or file I/O is provided.
    A consumer records the bytes it consumed, not a client-supplied digest.
    A lock makes observation and assessment coherent within this owner. This is
    artifact evidence only: execution, imports and mutable globals are unobserved.
    """
    def __init__(self, definition: BuildDefinition, process: ProcessBinding):
        if type(definition) is not BuildDefinition or definition.validate() is not None:
            raise ValueError('INVALID_BUILD_DEFINITION')
        if type(process) is not ProcessBinding or not process.valid():
            raise ValueError('INVALID_PROCESS_BINDING')
        self.__definition = definition
        self.__process = process
        self.__records: dict[str, str] = {}
        self.__terminal = False
        self.__lock = threading.Lock()

    def observe_consumed_artifact(self, name: str, content: bytes) -> None:
        """Record content digests without retaining potentially sensitive content."""
        with self.__lock:
            if (self.__terminal or not _name(name) or type(content) is not bytes
                    or len(content) > _MAX_ARTIFACT_BYTES
                    or name not in {i.name for i in self.__definition.inputs}
                    or name in self.__records):
                self.__terminal = True
                raise ValueError('INVALID_OR_CONFLICTING_ARTIFACT_OBSERVATION')
            self.__records[name] = 'sha256:' + hashlib.sha256(content).hexdigest()

    def assess(self, expected: BuildDefinition | None, current: ProcessBinding | None) -> dict:
        """Validate server-owned observations; full execution remains fail-closed."""
        with self.__lock:
            if expected is None:
                return _result('EXPECTED_BUILD_MISSING')
            if type(expected) is not BuildDefinition:
                return _result('MALFORMED_BUILD_DEFINITION')
            invalid = expected.validate()
            if invalid is not None:
                return _result(invalid)
            expected_id = expected.build_id()
            if type(current) is not ProcessBinding or not current.valid():
                return _result('PROCESS_IDENTITY_MISSING_OR_MALFORMED', expected=expected_id)
            if self.__process.pid != current.pid or self.__process.process_start != current.process_start:
                return _result('PROCESS_IDENTITY_MISMATCH', expected=expected_id)
            if self.__process.runtime_instance_id != current.runtime_instance_id:
                return _result('RUNTIME_INSTANCE_MISMATCH', expected=expected_id)
            if self.__terminal:
                return _result('PROVENANCE_TERMINAL', expected=expected_id)
            if not self.__records:
                return _result('OBSERVED_LOADED_IDENTITY_MISSING', expected=expected_id)
            if set(self.__records) != {item.name for item in self.__definition.inputs}:
                return _result('INCOMPLETE_LOADED_PROVENANCE', expected=expected_id)
            observed = BuildDefinition(self.__definition.inventory,
                tuple(BuildInput(i.name, i.role, self.__records[i.name])
                      for i in self.__definition.inputs))
            observed_id = observed.build_id()
            if expected_id != observed_id:
                return _result('BUILD_MISMATCH', expected=expected_id, observed=observed_id)
            # Even complete artifact consumption does not prove closed execution.
            return _result('EXECUTION_CLOSURE_NOT_OBSERVED', expected=expected_id,
                           observed=observed_id, artifact_binding='VERIFIED')


def assess_untrusted_build_provenance(value=None) -> dict:
    """Client/historical/serialized receipts are never authoritative observations."""
    return _result('UNTRUSTED_PROVENANCE')
