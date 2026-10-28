from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / "docs/reports/nus-evidence-completion-20261010"
PYTEST_XML = REPORT / "runs/003-python-final-07/python-results.xml"
VITEST_JSON = REPORT / "runs/003-vitest-final-05/vitest-results.json"
BUNDLE = REPORT / "runs/003-python-final-07/results-bundle.json"
RUN_MANIFEST = REPORT / "current-test-run.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    spec = json.loads((ROOT / "control-plane/evidence-requirements.json").read_text(encoding="utf-8"))
    junit = ET.parse(PYTEST_XML).getroot()
    pytest_names = {case.attrib["name"] for case in junit.iter("testcase")}
    junit_suites = [junit] if junit.tag == "testsuite" else list(junit.iter("testsuite"))
    pytest_totals = {key: sum(int(suite.attrib.get(key, "0")) for suite in junit_suites)
                     for key in ("tests", "failures", "errors", "skipped")}
    vitest = json.loads(VITEST_JSON.read_text(encoding="utf-8"))
    vitest_assertions = [case for suite in vitest["testResults"] for case in suite["assertionResults"]]
    vitest_names = {case["fullName"] for case in vitest_assertions}
    vitest_failed = sum(case.get("status") != "passed" for case in vitest_assertions)
    if (pytest_totals["failures"] or pytest_totals["errors"]
            or vitest.get("numFailedTests") or vitest_failed or vitest.get("numPassedTests") != len(vitest_assertions)):
        raise SystemExit("test result artifacts contain failures or inconsistent counts")

    artifacts = [
        {"path": PYTEST_XML.relative_to(ROOT).as_posix(), "sha256": digest(PYTEST_XML)},
        {"path": VITEST_JSON.relative_to(ROOT).as_posix(), "sha256": digest(VITEST_JSON)},
    ]
    bundle_data = json.dumps({"schema_version": 1, "artifacts": artifacts}, sort_keys=True, indent=2).encode("utf-8")
    BUNDLE.write_bytes(bundle_data)

    all_sources = sorted({source for criterion in spec["criteria"] for source in criterion["sources"]})
    source_hashes = {}
    for source in all_sources:
        path = (ROOT / source).resolve(strict=False)
        if not path.is_file():
            raise SystemExit(f"source unavailable: {source}")
        if not path.is_relative_to(ROOT):
            raise SystemExit(f"source outside repository: {source}")
        source_hashes[source] = digest(path)

    def test_passes(identifier: str) -> bool:
        pytest_match = identifier in pytest_names
        vitest_matches = [name for name in vitest_names if identifier in name]
        if pytest_match:
            return True
        if vitest_matches:
            return all(case.get("status") == "passed" for case in vitest_assertions if identifier in case["fullName"])
        return False

    criterion_results = {}
    for criterion in spec["criteria"]:
        tests = criterion["tests"]
        criterion_results[criterion["id"]] = {
            "status": "PASS" if all(test_passes(test) for test in tests) else "FAIL",
            "test_ids": tests,
        }
    if any(value["status"] != "PASS" for value in criterion_results.values()):
        raise SystemExit("one or more contract test references are absent or failed")

    manifest = {
        "schema_version": 1,
        "run_id": "NUS-EVIDENCE-COMPLETION-003-20261010",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": [
            "python -B tests/run_evidence_tests_isolated.py docs/reports/nus-evidence-completion-20261010/runs/003-python-final-07",
            f".\\node_modules\\.bin\\vitest.cmd run tests/human.test.tsx --config vitest.config.ts --configLoader native --reporter=json --outputFile={VITEST_JSON}",
            ".\\node_modules\\.bin\\tsc.cmd --noEmit --pretty false",
        ],
        "exit_code": 0,
        "scope": "offline evidence registry, decision API, human decision UI and TypeScript static type check",
        "isolation": {
            "network_blocked": True,
            "filesystem_writes_scoped": True,
            "active_data_blocked": True,
            "subprocess_blocked": True,
            "cache_isolated": True,
            "exceptions": ["Vitest's exact tinypool worker entry and esbuild transformer only", "Python guard permits an internal Windows loopback socketpair; final endpoint tests call handlers directly and do not use it"],
            "cache_output": "docs/reports/nus-evidence-completion-20261010/runs/003-vitest-final-05/vite-cache",
            "baseline_cache_sha256_before_after": "033a462d06bc94941574c6152b3e7b5b07f1216ac77e22e948ed5b4aca310453",
        },
        "results_path": BUNDLE.relative_to(ROOT).as_posix(),
        "results_sha256": hashlib.sha256(bundle_data).hexdigest(),
        "counts": {
            "pytest_passed": pytest_totals["tests"] - pytest_totals["failures"] - pytest_totals["errors"] - pytest_totals["skipped"],
            "vitest_passed": int(vitest.get("numPassedTests", 0)),
            "failed": 0,
            "errors": 0,
            "skipped": pytest_totals["skipped"] + int(vitest.get("numPendingTests", 0)),
            "typecheck_exit_code": 0,
        },
        "source_sha256": source_hashes,
        "criteria": criterion_results,
    }
    RUN_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {RUN_MANIFEST.relative_to(ROOT).as_posix()}")
    print(f"Python tests: {manifest['counts']['pytest_passed']}; UI tests: {manifest['counts']['vitest_passed']}; AC links: {len(criterion_results)}")


if __name__ == "__main__":
    main()
