from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json, shutil
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / "docs/reports/nus-evidence-completion-20261010"
RUN = REPORT / "runs/blocker-closure-20261010-01"
PYTEST_XML = RUN / "python-results.xml"
VITEST_JSON = REPORT / "runs/003-vitest-final-05/vitest-results.json"
BUNDLE = RUN / "results-bundle.json"
RUN_MANIFEST = REPORT / "current-test-run.json"
PREVIOUS = RUN / "previous-current-test-run.json"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

if any(not p.is_file() for p in (PYTEST_XML, VITEST_JSON, RUN_MANIFEST)):
    raise SystemExit("required results or prior manifest are missing")
if PREVIOUS.exists():
    raise SystemExit("refusing to overwrite the preserved prior manifest")
old_bytes = RUN_MANIFEST.read_bytes()
old = json.loads(old_bytes.decode("utf-8-sig"))
expected_old_manifest_hash = "6b601996c5320c91b2e5287a1c682264c19fb6a44877284207efa52663e7de77"
if hashlib.sha256(old_bytes).hexdigest() != expected_old_manifest_hash:
    raise SystemExit("current test manifest changed since inspection")

spec = json.loads((ROOT / "control-plane/evidence-requirements.json").read_text(encoding="utf-8-sig"))
root = ET.parse(PYTEST_XML).getroot()
suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
totals = {key: sum(int(s.attrib.get(key, "0")) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
pytest_names = {case.attrib.get("name", "") for case in root.iter("testcase")}
if totals != {"tests": 19, "failures": 0, "errors": 0, "skipped": 0}:
    raise SystemExit(f"unexpected fresh Python test totals: {totals}")
vitest = json.loads(VITEST_JSON.read_text(encoding="utf-8-sig"))
assertions = [case for suite in vitest["testResults"] for case in suite["assertionResults"]]
vitest_names = {case.get("fullName", "") for case in assertions}
if (vitest.get("numPassedTests") != 17 or vitest.get("numFailedTests", 0) != 0
        or any(case.get("status") != "passed" for case in assertions)):
    raise SystemExit("prior UI test evidence no longer validates")

# The current source comparison established that only these two Python files
# drifted since the prior run; all frontend/typecheck sources stayed byte-identical.
changed = []
for source, old_hash in old["source_sha256"].items():
    path = ROOT / source
    if not path.is_file() or digest(path) != old_hash:
        changed.append(source)
if set(changed) != {"tests/run_evidence_tests_isolated.py", "tests/test_evidence_registry.py"}:
    raise SystemExit(f"unexpected source drift since prior manifest: {changed}")
if old.get("counts", {}).get("typecheck_exit_code") != 0:
    raise SystemExit("prior typecheck evidence is not a pass")

artifacts = [
    {"path": PYTEST_XML.relative_to(ROOT).as_posix(), "sha256": digest(PYTEST_XML)},
    {"path": VITEST_JSON.relative_to(ROOT).as_posix(), "sha256": digest(VITEST_JSON)},
]
bundle_data = json.dumps({"schema_version": 1, "artifacts": artifacts}, sort_keys=True, indent=2).encode("utf-8")
if BUNDLE.exists():
    if BUNDLE.read_bytes() != bundle_data:
        raise SystemExit("existing fresh result bundle does not match the validated artifacts")
else:
    BUNDLE.write_bytes(bundle_data)

sources = sorted({source for criterion in spec["criteria"] for source in criterion["sources"]})
source_hashes = {source: digest(ROOT / source) for source in sources}

def test_passes(identifier: str) -> bool:
    if identifier in pytest_names:
        return True
    selected = [case for case in assertions if identifier in case.get("fullName", "")]
    return bool(selected) and all(case.get("status") == "passed" for case in selected)

criteria_results = {}
for criterion in spec["criteria"]:
    names = criterion["tests"]
    if not all(test_passes(name) for name in names):
        if criterion["id"] != "AC15":
            raise SystemExit(f"required test missing or failed for {criterion['id']}: {names}")
        criteria_results[criterion["id"]] = {
            "status": "BLOCKED",
            "test_ids": names,
            "reason": "TEST_REFERENCE_STALE_OR_MISSING; required test name is absent from the refreshed run. Similar test_missing_test_run_blocks_pass checks blocker reasons but does not establish the full AC15 artifact-binding assertion.",
        }
    else:
        criteria_results[criterion["id"]] = {"status": "PASS", "test_ids": names}

shutil.copyfile(RUN_MANIFEST, PREVIOUS)
manifest = {
    "schema_version": 1,
    "run_id": "NUS-EVIDENCE-COMPLETION-003-20261010-BLOCKER-CLOSURE-01",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "command": [
        f".venv\\Scripts\\python.exe -B tests\\run_evidence_tests_isolated.py {RUN.relative_to(ROOT).as_posix()}",
        "REUSED VERIFIED: .\\node_modules\\.bin\\vitest.cmd run tests/human.test.tsx --config vitest.config.ts --configLoader native --reporter=json --outputFile=docs/reports/nus-evidence-completion-20261010/runs/003-vitest-final-05/vitest-results.json",
        "REUSED VERIFIED: .\\node_modules\\.bin\\tsc.cmd --noEmit --pretty false",
    ],
    "exit_code": 0,
    "scope": "current isolated Python evidence registry/API/runner guard tests plus unchanged hash-verified UI and typecheck evidence",
    "isolation": {
        "network_blocked": True,
        "filesystem_writes_scoped": True,
        "active_data_blocked": True,
        "subprocess_blocked": True,
        "cache_isolated": True,
        "exceptions": ["Runner permits only its verified local loopback socketpair window; no external network calls in these tests"],
        "python_output": RUN.relative_to(ROOT).as_posix(),
        "reused_ui_output": VITEST_JSON.relative_to(ROOT).as_posix(),
        "reused_ui_cache_sha256_before_after": old["isolation"].get("baseline_cache_sha256_before_after"),
    },
    "results_path": BUNDLE.relative_to(ROOT).as_posix(),
    "results_sha256": hashlib.sha256(bundle_data).hexdigest(),
    "counts": {
        "pytest_passed": totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"],
        "vitest_passed": int(vitest["numPassedTests"]),
        "failed": 0,
        "errors": 0,
        "skipped": totals["skipped"] + int(vitest.get("numPendingTests", 0)),
        "typecheck_exit_code": 0,
    },
    "source_sha256": source_hashes,
    "criteria": criteria_results,
}
RUN_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"manifest": str(RUN_MANIFEST.relative_to(ROOT)), "previous_manifest_copy": str(PREVIOUS.relative_to(ROOT)), "bundle": str(BUNDLE.relative_to(ROOT)), "counts": manifest["counts"], "criteria": len(criteria_results)}, indent=2))

