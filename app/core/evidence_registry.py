"""Offline evidence packages and server-side, tamper-evident human decisions.

Artifact validation is deliberately separate from source classification. VALID
means a regular, bounded, readable artifact was hashed under the recorded rule;
it does not certify the truth of its contents or a live system state.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
from uuid import uuid4
from app.core.work_approval_contract import APPROVAL_VALIDITY_SECONDS


VALIDATION_STATUSES = frozenset({"VALID", "INVALID", "MISSING", "BLOCKED", "NOT_VERIFIED"})
SOURCE_CLASSES = frozenset({"CURRENT_OFFLINE", "HISTORICAL", "FIXTURE", "TEMPORARY", "MISSING", "INACCESSIBLE"})
MAX_ARTIFACT_BYTES = 4_000_000
MAX_AUDIT_BYTES = 16_000_000
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
_audit_thread_lock = threading.RLock()


class EvidenceRegistryError(ValueError):
    """Evidence or audit data could not be safely interpreted."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> object:
    try:
        if path.stat().st_size > MAX_ARTIFACT_BYTES:
            raise EvidenceRegistryError("ARTIFACT_SIZE_LIMIT")
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise
    except PermissionError:
        raise
    except EvidenceRegistryError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise EvidenceRegistryError("ARTIFACT_INVALID") from exc


def _safe_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise EvidenceRegistryError("INVALID_EVIDENCE_PATH")
    candidate = (root / relative).resolve(strict=False)
    if not candidate.is_relative_to(root):
        raise EvidenceRegistryError("EVIDENCE_PATH_OUTSIDE_ROOT")
    return candidate


def _source_status(root: Path, relative: str, classification: str = "CURRENT_OFFLINE") -> dict:
    if classification not in SOURCE_CLASSES:
        raise EvidenceRegistryError("EVIDENCE_CLASSIFICATION_INVALID")
    record = {"path": relative, "classification": classification, "validation_status": "NOT_VERIFIED", "sha256": None, "bytes": None, "collected_at": None, "reason": None}
    try:
        path = _safe_path(root, relative)
        info = path.stat()
        if not path.is_file():
            record.update(validation_status="INVALID", reason="NOT_A_REGULAR_FILE")
            return record
        if info.st_size > MAX_ARTIFACT_BYTES:
            record.update(validation_status="BLOCKED", reason="ARTIFACT_SIZE_LIMIT")
            return record
        data = path.read_bytes()
        record.update(validation_status="VALID", sha256=_sha256(data), bytes=len(data),
                       collected_at=datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat())
    except FileNotFoundError:
        record.update(classification="MISSING", validation_status="MISSING", reason="REQUIRED_ARTIFACT_NOT_FOUND")
    except PermissionError:
        record.update(classification="INACCESSIBLE", validation_status="BLOCKED", reason="ARTIFACT_ACCESS_DENIED")
    except EvidenceRegistryError as exc:
        record.update(validation_status="INVALID", reason=str(exc))
    except OSError:
        record.update(classification="INACCESSIBLE", validation_status="BLOCKED", reason="ARTIFACT_READ_FAILED")
    return record


def _test_run(root: Path, relative: str, known_sources: dict[str, dict]) -> tuple[dict, dict | None]:
    evidence = {"path": relative, "classification": "HISTORICAL", "validation_status": "NOT_VERIFIED", "sha256": None, "bytes": None, "reason": "NO_CURRENT_TEST_RUN"}
    try:
        path = _safe_path(root, relative)
        raw = path.read_bytes()
        if len(raw) > MAX_ARTIFACT_BYTES:
            evidence.update(validation_status="BLOCKED", reason="TEST_REPORT_SIZE_LIMIT")
            return evidence, None
        result = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(result, dict):
            evidence.update(validation_status="INVALID", reason="TEST_REPORT_SHAPE_INVALID")
            return evidence, None
        evidence.update(validation_status="VALID", sha256=_sha256(raw), bytes=len(raw), reason=None)
        required = {"schema_version", "run_id", "timestamp", "command", "exit_code", "scope", "isolation", "results_path", "results_sha256", "counts", "source_sha256", "criteria"}
        if not required.issubset(result) or result.get("schema_version") != 1:
            evidence.update(validation_status="INVALID", reason="TEST_REPORT_FIELDS_INVALID")
            return evidence, None
        if not isinstance(result.get("command"), list) or not result["command"] or not isinstance(result.get("isolation"), dict):
            evidence.update(validation_status="INVALID", reason="TEST_REPORT_PROVENANCE_INVALID")
            return evidence, None
        required_isolation = {"network_blocked", "filesystem_writes_scoped", "active_data_blocked", "subprocess_blocked", "cache_isolated"}
        if not required_isolation.issubset(result["isolation"]) or any(result["isolation"][key] is not True for key in required_isolation):
            evidence.update(validation_status="BLOCKED", reason="TEST_ISOLATION_NOT_PROVEN")
            return evidence, None
        if (not isinstance(result.get("exit_code"), int) or isinstance(result.get("exit_code"), bool)
                or not isinstance(result.get("counts"), dict)
                or any(not isinstance(value, int) or value < 0 for value in result["counts"].values())):
            evidence.update(validation_status="INVALID", reason="TEST_RESULT_COUNTS_INVALID")
            return evidence, None
        if not isinstance(result.get("results_sha256"), str) or len(result["results_sha256"]) != 64:
            evidence.update(validation_status="INVALID", reason="TEST_RESULTS_HASH_INVALID")
            return evidence, None
        try:
            results_path = _safe_path(root, result["results_path"])
            results_raw = results_path.read_bytes()
            if len(results_raw) > MAX_ARTIFACT_BYTES or _sha256(results_raw) != result["results_sha256"]:
                evidence.update(validation_status="INVALID", reason="TEST_RESULTS_HASH_MISMATCH")
                return evidence, None
            result_bundle = json.loads(results_raw.decode("utf-8-sig"))
            artifacts = result_bundle.get("artifacts") if isinstance(result_bundle, dict) else None
            if not isinstance(artifacts, list) or not artifacts:
                evidence.update(validation_status="INVALID", reason="TEST_RESULTS_BUNDLE_INVALID")
                return evidence, None
            verified_artifacts = []
            for artifact in artifacts:
                if (not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str)
                        or not isinstance(artifact.get("sha256"), str) or len(artifact["sha256"]) != 64):
                    evidence.update(validation_status="INVALID", reason="TEST_RESULT_ARTIFACT_REFERENCE_INVALID")
                    return evidence, None
                artifact_path = _safe_path(root, artifact["path"])
                artifact_raw = artifact_path.read_bytes()
                if len(artifact_raw) > MAX_ARTIFACT_BYTES or _sha256(artifact_raw) != artifact["sha256"]:
                    evidence.update(validation_status="INVALID", reason="TEST_RESULT_ARTIFACT_HASH_MISMATCH")
                    return evidence, None
                verified_artifacts.append({"path": artifact["path"], "sha256": artifact["sha256"], "bytes": len(artifact_raw)})
        except FileNotFoundError:
            evidence.update(classification="MISSING", validation_status="MISSING", reason="TEST_RESULTS_MISSING")
            return evidence, None
        except PermissionError:
            evidence.update(classification="INACCESSIBLE", validation_status="BLOCKED", reason="TEST_RESULTS_ACCESS_DENIED")
            return evidence, None
        if not isinstance(result.get("criteria"), dict) or not isinstance(result.get("source_sha256"), dict):
            evidence.update(validation_status="INVALID", reason="TEST_REPORT_LINKAGE_INVALID")
            return evidence, None
        if set(known_sources) - set(result["source_sha256"]):
            evidence.update(validation_status="INVALID", reason="TEST_SOURCE_COVERAGE_INCOMPLETE")
            return evidence, None
        if any(result["counts"].get(key, 0) for key in ("failed", "failures", "errors")):
            evidence.update(validation_status="INVALID", reason="TEST_RESULT_COUNTS_FAILED")
            return evidence, None
        for source_path, expected_hash in result["source_sha256"].items():
            current = known_sources.get(source_path)
            if not current or current.get("sha256") != expected_hash or current.get("validation_status") != "VALID":
                evidence.update(validation_status="INVALID", reason="TEST_SOURCE_CHANGED_AFTER_RUN")
                return evidence, None
        evidence["classification"] = "CURRENT_OFFLINE" if result.get("exit_code") == 0 else "HISTORICAL"
        evidence["results_path"] = result["results_path"]
        evidence["results_sha256"] = result["results_sha256"]
        evidence["result_artifacts"] = verified_artifacts
        return evidence, result
    except FileNotFoundError:
        evidence.update(classification="MISSING", validation_status="NOT_VERIFIED", reason="NO_CURRENT_TEST_RUN")
    except PermissionError:
        evidence.update(classification="INACCESSIBLE", validation_status="BLOCKED", reason="TEST_REPORT_ACCESS_DENIED")
    except (UnicodeError, ValueError, TypeError):
        evidence.update(validation_status="INVALID", reason="TEST_REPORT_INVALID")
    except OSError:
        evidence.update(classification="INACCESSIBLE", validation_status="BLOCKED", reason="TEST_REPORT_READ_FAILED")
    return evidence, None


def collect_review_package(root: Path = DEFAULT_ROOT, *, generated_at: str | None = None) -> dict:
    """Collect only manifest-declared offline files; never opens active DB/index data."""
    root = Path(root).resolve()
    manifest_path = root / "control-plane" / "evidence-requirements.json"
    try:
        manifest = _read_json(manifest_path)
    except FileNotFoundError as exc:
        raise EvidenceRegistryError("EVIDENCE_REQUIREMENTS_MISSING") from exc
    except PermissionError as exc:
        raise EvidenceRegistryError("EVIDENCE_REQUIREMENTS_BLOCKED") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or not isinstance(manifest.get("criteria"), list):
        raise EvidenceRegistryError("EVIDENCE_REQUIREMENTS_INVALID")

    criteria_spec = manifest["criteria"]
    ids = [item.get("id") for item in criteria_spec if isinstance(item, dict)]
    if len(criteria_spec) != 15 or len(ids) != 15 or set(ids) != {f"AC{i}" for i in range(1, 16)}:
        raise EvidenceRegistryError("ACCEPTANCE_MAPPING_INCOMPLETE")

    for item in criteria_spec:
        if (not isinstance(item.get("summary"), str) or not item["summary"].strip()
                or not isinstance(item.get("sources"), list) or not item["sources"]
                or any(not isinstance(path, str) or not path for path in item["sources"])
                or not isinstance(item.get("tests"), list) or not item["tests"]
                or any(not isinstance(test, str) or not test for test in item["tests"])):
            raise EvidenceRegistryError("ACCEPTANCE_MAPPING_INVALID")

    source_paths = sorted({path for item in criteria_spec for path in item.get("sources", [])})
    classifications = manifest.get("classifications", {})
    if not isinstance(classifications, dict):
        raise EvidenceRegistryError("EVIDENCE_CLASSIFICATION_MAP_INVALID")
    sources = {path: _source_status(root, path, classifications.get(path, "CURRENT_OFFLINE")) for path in source_paths}
    for path, record in sources.items():
        record["id"] = "src_" + _sha256(path.encode("utf-8"))[:16]
    test_path = manifest.get("test_run_manifest")
    if not isinstance(test_path, str):
        raise EvidenceRegistryError("TEST_RUN_MANIFEST_PATH_INVALID")
    test_evidence, test_run = _test_run(root, test_path, sources)
    evidence = list(sources.values()) + [{"id": "current-test-run", **test_evidence}]

    criteria = []
    for item in sorted(criteria_spec, key=lambda row: row["id"]):
        missing_sources = [path for path in item.get("sources", []) if sources[path]["validation_status"] != "VALID"]
        test_ids = item.get("tests", [])
        if not isinstance(test_ids, list) or not test_ids:
            raise EvidenceRegistryError("CRITERION_TEST_LINK_MISSING")
        criterion_result = (test_run or {}).get("criteria", {}).get(item["id"], {}) if test_run else {}
        if not isinstance(criterion_result, dict):
            criterion_result = {}
        if missing_sources:
            status = next((sources[path]["validation_status"] for path in missing_sources if sources[path]["validation_status"] in {"INVALID", "MISSING", "BLOCKED"}), "NOT_VERIFIED")
            reason = "REQUIRED_SOURCE_UNAVAILABLE"
        elif test_run is None or test_evidence["validation_status"] != "VALID":
            status, reason = "NOT_VERIFIED", test_evidence["reason"] or "TEST_NOT_VERIFIED"
        elif test_run.get("exit_code") != 0:
            status, reason = "INVALID", "TEST_RUN_FAILED"
        elif criterion_result.get("status") == "BLOCKED":
            status, reason = "BLOCKED", criterion_result.get("reason", "TEST_BLOCKED")
        elif criterion_result.get("status") == "FAIL":
            status, reason = "INVALID", criterion_result.get("reason", "TEST_FAILED")
        elif (criterion_result.get("status") == "PASS"
              and isinstance(criterion_result.get("test_ids"), list)
              and all(isinstance(test_id, str) for test_id in criterion_result["test_ids"])
              and set(criterion_result["test_ids"]) >= set(test_ids)):
            status, reason = "VALID", None
        else:
            status, reason = "NOT_VERIFIED", "REQUIRED_TEST_RESULT_MISSING"
        criteria.append({"id": item["id"], "summary": item["summary"], "status": status,
                         "evidence": item["sources"], "tests": test_ids, "reason": reason})

    blockers = [{"id": item["id"], "reason": item["reason"] or item["status"]}
                for item in criteria if item["status"] != "VALID"]
    fingerprint_data = {"schema_version": 1, "evidence": evidence, "criteria": criteria, "blockers": blockers}
    package_id = "evp_sha256_" + _sha256(_canonical(fingerprint_data))
    return {**fingerprint_data, "package_id": package_id, "generated_at": generated_at or _utc_now(),
            "read_scope": "MANIFEST_DECLARED_OFFLINE_ARTIFACTS_ONLY",
            "runtime_status": "NOT_VERIFIED", "pass_allowed": not blockers,
            "blockers": blockers}


@contextmanager
def _cross_process_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"\0")
            lock_file.flush()
        lock_file.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _record_hash(record: dict) -> str:
    material = {key: value for key, value in record.items() if key != "record_hash"}
    return _sha256(_canonical(material))


def _checkpoint_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".head.json")


def _checkpoint_hash(checkpoint: dict) -> str:
    return _sha256(_canonical({key: value for key, value in checkpoint.items() if key != "checkpoint_hash"}))


def _write_checkpoint(path: Path, records: list[dict]) -> None:
    checkpoint = {"schema_version": 1, "record_count": len(records),
                  "head_hash": records[-1]["record_hash"] if records else "0" * 64}
    checkpoint["checkpoint_hash"] = _checkpoint_hash(checkpoint)
    checkpoint_path = _checkpoint_path(path)
    temporary = checkpoint_path.with_name(checkpoint_path.name + ".tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(_canonical(checkpoint) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, checkpoint_path)
    except OSError as exc:
        raise EvidenceRegistryError("DECISION_AUDIT_CHECKPOINT_WRITE_FAILED") from exc


def read_decision_audit(path: Path) -> list[dict]:
    """Verify the complete append-only hash chain; fail closed on any edit."""
    path = Path(path)
    checkpoint_path = _checkpoint_path(path)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        if checkpoint_path.exists():
            raise EvidenceRegistryError("DECISION_AUDIT_LOG_MISSING") from None
        return []
    except PermissionError as exc:
        raise EvidenceRegistryError("DECISION_AUDIT_BLOCKED") from exc
    except OSError as exc:
        raise EvidenceRegistryError("DECISION_AUDIT_READ_FAILED") from exc
    if not raw:
        if checkpoint_path.exists():
            raise EvidenceRegistryError("DECISION_AUDIT_CHAIN_INVALID")
        return []
    if not raw.endswith(b"\n"):
        raise EvidenceRegistryError("DECISION_AUDIT_PARTIAL_RECORD")
    records = []
    previous = "0" * 64
    for line in raw.splitlines():
        try:
            record = json.loads(line.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise EvidenceRegistryError("DECISION_AUDIT_INVALID_JSON") from exc
        if not isinstance(record, dict) or record.get("previous_hash") != previous or record.get("record_hash") != _record_hash(record):
            raise EvidenceRegistryError("DECISION_AUDIT_CHAIN_INVALID")
        previous = record["record_hash"]
        records.append(record)
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise EvidenceRegistryError("DECISION_AUDIT_CHECKPOINT_MISSING") from None
    except (OSError, UnicodeError, ValueError) as exc:
        raise EvidenceRegistryError("DECISION_AUDIT_CHECKPOINT_INVALID") from exc
    if (not isinstance(checkpoint, dict) or checkpoint.get("schema_version") != 1
            or checkpoint.get("record_count") != len(records)
            or checkpoint.get("head_hash") != previous
            or checkpoint.get("checkpoint_hash") != _checkpoint_hash(checkpoint)):
        raise EvidenceRegistryError("DECISION_AUDIT_CHECKPOINT_MISMATCH")
    return records


def append_decision_audit(path: Path, *, package_id: str, decision: str, notes: str,
                          reviewer_principal: str, test_evidence: list[str], blockers: list[dict],
                          timestamp: str | None = None, plan_binding: dict | None = None) -> dict:
    if decision not in {"PASS", "FAIL", "HOLD"}:
        raise EvidenceRegistryError("DECISION_INVALID")
    if not isinstance(notes, str) or len(notes) > 2000:
        raise EvidenceRegistryError("DECISION_NOTES_INVALID")
    path = Path(path)
    with _audit_thread_lock, _cross_process_lock(path.with_suffix(path.suffix + ".lock")):
        records = read_decision_audit(path)
        record = {
            "schema_version": 1,
            "decision_id": "dec_" + uuid4().hex,
            "package_id": package_id,
            "decision": decision,
            "reviewer_principal": reviewer_principal,
            "authentication": "NUSANTARA_ADMIN_TOKEN",
            "timestamp": timestamp or _utc_now(),
            "notes": notes,
            "test_evidence": test_evidence,
            "blockers": blockers,
            "previous_hash": records[-1]["record_hash"] if records else "0" * 64,
        }
        if plan_binding is not None:
            record['plan_binding'] = plan_binding
        record["record_hash"] = _record_hash(record)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("ab") as stream:
                stream.write(_canonical(record) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise EvidenceRegistryError("DECISION_AUDIT_WRITE_FAILED") from exc
        _write_checkpoint(path, [*records, record])
        return record


def require_execution_approval(root: Path, audit_path: Path, *, package_id: str,
                               decision_id: str, required_sources: list[str],
                               now: datetime | None = None, plan_binding: dict | None = None) -> dict:
    """Authorize only the current fully tested package and latest unexpired PASS."""
    package = collect_review_package(root)
    if not package['pass_allowed'] or package['package_id'] != package_id:
        raise EvidenceRegistryError('EXECUTION_EVIDENCE_INVALID_OR_CHANGED')
    covered = {row['path'] for row in package['evidence']
               if row['validation_status'] == 'VALID'}
    if not required_sources or not set(required_sources).issubset(covered):
        raise EvidenceRegistryError('EXECUTION_SOURCE_NOT_IN_REVIEW_PACKAGE')
    records = read_decision_audit(audit_path)
    matching = [row for row in records if row['package_id'] == package_id]
    if not matching or matching[-1]['decision_id'] != decision_id or matching[-1]['decision'] != 'PASS':
        raise EvidenceRegistryError('EXECUTION_REQUIRES_CURRENT_PASS')
    decision = matching[-1]
    if plan_binding is not None and decision.get('plan_binding') != plan_binding:
        raise EvidenceRegistryError('EXECUTION_PLAN_APPROVAL_MISMATCH')
    try:
        created = datetime.fromisoformat(decision['timestamp'].replace('Z', '+00:00'))
        age = ((now or datetime.now(timezone.utc)) - created).total_seconds()
    except (ValueError, TypeError, KeyError):
        raise EvidenceRegistryError('EXECUTION_DECISION_TIMESTAMP_INVALID') from None
    if not 0 <= age <= APPROVAL_VALIDITY_SECONDS:
        raise EvidenceRegistryError('EXECUTION_APPROVAL_EXPIRED')
    return decision
