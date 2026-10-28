import hashlib
import json

import pytest

from app.core import evidence_registry as registry


def test_registry_covers_all_acceptance_criteria():
    manifest = json.loads((registry.DEFAULT_ROOT / "control-plane/evidence-requirements.json").read_text())
    assert {item["id"] for item in manifest["criteria"]} == {f"AC{i}" for i in range(1, 16)}
    assert all(item["sources"] and item["tests"] for item in manifest["criteria"])


def test_each_criterion_links_sources_and_tests():
    package = registry.collect_review_package()
    evidence_paths = {item["path"] for item in package["evidence"]}
    assert len(package["criteria"]) == 15
    assert all(item["evidence"] and item["tests"] for item in package["criteria"])
    assert all(set(item["evidence"]).issubset(evidence_paths) for item in package["criteria"])


def test_collector_records_real_artifact_references():
    package = registry.collect_review_package()
    paths = {item["path"] for item in package["evidence"]}
    assert "app/core/evidence_registry.py" in paths
    assert "control-plane/evidence-requirements.json" in paths
    assert all(item["path"] and item["classification"] in registry.SOURCE_CLASSES for item in package["evidence"])


def test_validator_distinguishes_all_statuses(tmp_path, monkeypatch):
    (tmp_path / "present.txt").write_text("offline evidence")
    (tmp_path / "directory").mkdir()
    valid = registry._source_status(tmp_path, "present.txt")
    missing = registry._source_status(tmp_path, "missing.txt")
    invalid = registry._source_status(tmp_path, "directory")
    escaped = registry._source_status(tmp_path, "../outside.txt")
    historical = registry._source_status(tmp_path, "present.txt", "HISTORICAL")
    original_read_bytes = type(tmp_path / "present.txt").read_bytes
    def denied_read(path):
        if path.name == "present.txt":
            raise PermissionError("fixture permission boundary")
        return original_read_bytes(path)
    monkeypatch.setattr(type(tmp_path / "present.txt"), "read_bytes", denied_read)
    blocked = registry._source_status(tmp_path, "present.txt")
    assert valid["validation_status"] == "VALID" and valid["sha256"] == hashlib.sha256(b"offline evidence").hexdigest()
    assert missing["validation_status"] == "MISSING" and missing["classification"] == "MISSING"
    assert invalid["validation_status"] == "INVALID"
    assert escaped["validation_status"] == "INVALID"
    assert blocked["validation_status"] == "BLOCKED" and blocked["classification"] == "INACCESSIBLE"
    assert historical["classification"] == "HISTORICAL"


def test_audit_chain_detects_tampering_and_appends(tmp_path):
    path = tmp_path / "decisions.jsonl"
    first = registry.append_decision_audit(path, package_id="package-1", decision="HOLD", notes="", reviewer_principal="admin-token-holder", test_evidence=[], blockers=[])
    second = registry.append_decision_audit(path, package_id="package-1", decision="FAIL", notes="reviewed", reviewer_principal="admin-token-holder", test_evidence=["t1"], blockers=[])
    assert second["previous_hash"] == first["record_hash"]
    assert [row["decision_id"] for row in registry.read_decision_audit(path)] == [first["decision_id"], second["decision_id"]]
    original = path.read_bytes()
    path.write_bytes(original.replace(b"reviewed", b"tampered"))
    with pytest.raises(registry.EvidenceRegistryError, match="DECISION_AUDIT_CHAIN_INVALID"):
        registry.read_decision_audit(path)
    path.write_bytes(b"".join(original.splitlines(keepends=True)[:-1]))
    with pytest.raises(registry.EvidenceRegistryError, match="DECISION_AUDIT_CHECKPOINT_MISMATCH"):
        registry.read_decision_audit(path)
    path.unlink()
    with pytest.raises(registry.EvidenceRegistryError, match="DECISION_AUDIT_LOG_MISSING"):
        registry.read_decision_audit(path)


def test_missing_test_run_blocks_pass(tmp_path):
    source_manifest = (
        registry.DEFAULT_ROOT / "control-plane" / "evidence-requirements.json"
    )
    manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
    manifest["test_run_manifest"] = "missing-test-run.json"

    control_plane = tmp_path / "control-plane"
    control_plane.mkdir()
    (control_plane / "evidence-requirements.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    package = registry.collect_review_package(tmp_path)

    assert len(package["criteria"]) == 15
    assert package["runtime_status"] == "NOT_VERIFIED"
    assert package["pass_allowed"] is False
    assert all(item["reason"] for item in package["blockers"])

    current_run = next(
        item for item in package["evidence"]
        if item["path"].endswith("missing-test-run.json")
    )
    assert current_run["validation_status"] == "NOT_VERIFIED"
    assert current_run["classification"] == "MISSING"

def test_package_id_changes_when_evidence_changes(tmp_path):
    root = tmp_path
    (root / "control-plane").mkdir()
    artifact = root / "source.txt"
    artifact.write_text("first")
    manifest = {"schema_version": 1, "test_run_manifest": "run.json", "criteria": [
        {"id": f"AC{i}", "summary": f"criterion {i}", "sources": ["source.txt"], "tests": ["test_id"]}
        for i in range(1, 16)
    ]}
    (root / "control-plane/evidence-requirements.json").write_text(json.dumps(manifest))
    first = registry.collect_review_package(root)
    artifact.write_text("second")
    second = registry.collect_review_package(root)
    assert first["package_id"] != second["package_id"]


def test_test_run_manifest_is_bound_to_result_hashes(tmp_path):
    output = b"10 passed"
    (tmp_path / "results.txt").write_bytes(output)
    bundle = {"artifacts": [{"path": "results.txt", "sha256": hashlib.sha256(output).hexdigest()}]}
    bundle_raw = json.dumps(bundle).encode()
    (tmp_path / "results-bundle.json").write_bytes(bundle_raw)
    manifest = {"schema_version": 1, "run_id": "run-fixture", "timestamp": "2026-10-10T00:00:00Z",
        "command": ["isolated-test-runner"], "exit_code": 0, "scope": "offline unit test fixture",
        "isolation": {key: True for key in ("network_blocked", "filesystem_writes_scoped", "active_data_blocked", "subprocess_blocked", "cache_isolated")},
        "results_path": "results-bundle.json", "results_sha256": hashlib.sha256(bundle_raw).hexdigest(),
        "counts": {"passed": 1, "failed": 0}, "source_sha256": {}, "criteria": {}}
    (tmp_path / "test-run.json").write_text(json.dumps(manifest))
    evidence, result = registry._test_run(tmp_path, "test-run.json", {})
    assert evidence["validation_status"] == "VALID" and result["exit_code"] == 0
    (tmp_path / "results.txt").write_bytes(b"modified")
    evidence, result = registry._test_run(tmp_path, "test-run.json", {})
    assert evidence["validation_status"] == "INVALID"
    assert evidence["reason"] == "TEST_RESULT_ARTIFACT_HASH_MISMATCH" and result is None




@pytest.mark.parametrize("source_mode,counts,reason", [
    ('missing', {'passed': 1, 'failed': 0}, 'TEST_SOURCE_COVERAGE_INCOMPLETE'),
    ('stale', {'passed': 1, 'failed': 0}, 'TEST_SOURCE_CHANGED_AFTER_RUN'),
    ('current', {'passed': 1, 'failed': 1}, 'TEST_RESULT_COUNTS_FAILED'),
    ('current', {'passed': 1, 'errors': 1}, 'TEST_RESULT_COUNTS_FAILED'),
])
def test_run_cannot_omit_source_binding_or_hide_failed_results(tmp_path, source_mode, counts, reason):
    source = tmp_path / 'source.py'
    source.write_text('value = 1')
    current = registry._source_status(tmp_path, 'source.py')
    (tmp_path / 'output.txt').write_text('test output')
    bundle = {'artifacts': [{'path': 'output.txt', 'sha256': hashlib.sha256((tmp_path / 'output.txt').read_bytes()).hexdigest()}]}
    raw = json.dumps(bundle).encode()
    (tmp_path / 'bundle.json').write_bytes(raw)
    run = {'schema_version': 1, 'run_id': 'fixture', 'timestamp': '2026-10-15T00:00:00Z',
        'command': ['fixture-runner'], 'exit_code': 0, 'scope': 'offline fixture',
        'isolation': {key: True for key in ('network_blocked', 'filesystem_writes_scoped', 'active_data_blocked', 'subprocess_blocked', 'cache_isolated')},
        'results_path': 'bundle.json', 'results_sha256': hashlib.sha256(raw).hexdigest(),
        'counts': counts, 'source_sha256': {} if source_mode == 'missing' else {'source.py': '0' * 64 if source_mode == 'stale' else current['sha256']}, 'criteria': {}}
    (tmp_path / 'run.json').write_text(json.dumps(run))
    evidence, result = registry._test_run(tmp_path, 'run.json', {'source.py': current})
    assert result is None
    assert evidence['validation_status'] == 'INVALID' and evidence['reason'] == reason
