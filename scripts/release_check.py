#!/usr/bin/env python3
"""Phase 20: jalankan check rilis yang bisa dijalankan & tulis RELEASE_READINESS_REPORT.md.
Check yang butuh fastapi/V1-baseline/load-test dilaporkan NOT_RUN (bukan PASS)."""
from __future__ import annotations

import importlib.util
import io
import py_compile
import subprocess
import sys
import unittest
import tempfile
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.security.readiness import FAIL, NOT_RUN, PASS, Check, render, verdict  # noqa: E402
from app.security.scanner import scan_tree  # noqa: E402

C, P = "tests.v2.test_v2_core.", "tests.v2.test_phases_7_21."


def run_ids(ids: list[str] | None) -> tuple[bool, str]:
    loader = unittest.TestLoader()
    names = ids if ids is not None else ["tests.v2.test_v2_core", "tests.v2.test_phases_7_21", "tests.v2.test_devcore", "tests.v2.test_devcore_integration", "tests.v2.test_devcore_routes"]
    suite = unittest.TestSuite(loader.loadTestsFromName(i) for i in names)
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    return res.wasSuccessful(), f"{res.testsRun} tes, {len(res.failures)} gagal, {len(res.errors)} error"


def test_check(name: str, ids: list[str] | None, critical: bool = False) -> Check:
    ok, detail = run_ids(ids)
    return Check(name, PASS if ok else FAIL, detail, critical)


def compile_all() -> Check:
    bad = []
    with tempfile.TemporaryDirectory() as directory:
        for index, p in enumerate((ROOT / "app").rglob("*.py")):
            try:
                py_compile.compile(str(p), doraise=True, cfile=str(Path(directory) / f"module-{index}.pyc"))
            except py_compile.PyCompileError:
                bad.append(str(p.relative_to(ROOT)))
    return Check("compile seluruh app/", FAIL if bad else PASS, ", ".join(bad) or "semua modul terkompilasi", True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation-report", type=Path)
    parser.add_argument("--load-report", type=Path)
    parser.add_argument("--chat-load-report", type=Path)
    args = parser.parse_args()
    have_fastapi = importlib.util.find_spec("fastapi") is not None and importlib.util.find_spec("pydantic") is not None
    checks = [
        test_check("1 unit test (semua tests/v2)", None, True),
        compile_all(),
        test_check("2 integration test (orchestrator end-to-end)", [C + "Orchestrator", P + "TestExperience"], True),
    ]
    if have_fastapi:
        r = subprocess.run([sys.executable, "run_tests.py"], cwd=ROOT, capture_output=True, text=True, timeout=300)
        checks.append(Check("3 API test + regresi V1 (run_tests.py)", PASS if r.returncode == 0 else FAIL,
                            r.stdout[-200:].strip() or r.stderr[-200:].strip(), True))
    else:
        checks.append(Check("3 API test + regresi V1 (run_tests.py)", NOT_RUN, "fastapi/pydantic tidak terpasang"))
    checks += [
        test_check("4 memory test", [C + "Memory"], True),
        test_check("5 RAG test", [P + "TestRAG"]),
        test_check("6 MCP test", [P + "TestMCPBridge"]),
        test_check("7 tool security test", [C + "Governance", P + "TestSandbox"], True),
        test_check("8 policy test", [C + "Orchestrator.test_policy_paths", C + "Orchestrator.test_v1_policy_adapter_matches_v1_rules"], True),
        test_check("9a otorisasi lapisan approval (reviewer != peminta, payload-bound)", [C + "AuditAndApproval"], True),
        test_check("10 prompt injection test", [P + "TestSecurity.test_prompt_injection_in_evidence_stays_data"], True),
        test_check("11 data leakage test", [P + "TestSecurity.test_data_leakage_logs_audit_events"], True),
    ]
    if have_fastapi and importlib.util.find_spec("pytest"):
        auth = subprocess.run([sys.executable, "-m", "pytest", "tests/test_audit_regressions.py",
                               "tests/v2/test_devcore_routes.py", "-q"], cwd=ROOT,
                              capture_output=True, text=True, timeout=180)
        checks.append(Check("9b API auth/security regression", PASS if auth.returncode == 0 else FAIL,
                            auth.stdout[-200:].strip(), True))
    else:
        checks.append(Check("9b API auth/security regression", NOT_RUN, "pytest/FastAPI required"))
    finds = scan_tree(ROOT)
    checks.append(Check("12 secret exposure scan", FAIL if finds else PASS,
                        f"{len(finds)} temuan: " + ", ".join(f"{f.path}:{f.line}({f.rule})" for f in finds[:5]) if finds else "0 temuan", True))
    checks += [
        test_check("16 developer core (read-only tools, security gate, grounding)", ["tests.v2.test_devcore", "tests.v2.test_devcore_integration", "tests.v2.test_devcore_routes"], True),
        test_check("15 failure recovery test", [C + "Hardening", C + "Orchestrator.test_model_failure_degrades_not_crashes",
                                                C + "Orchestrator.test_retrieval_failure_still_answers"], True),
    ]
    evaluation = Check("13 live V1 quality benchmark", NOT_RUN, "reviewed factual oracle and live benchmark required", True)
    if args.evaluation_report:
        report = json.loads(args.evaluation_report.read_text("utf-8"))
        if report.get("meta", {}).get("mode") != "live_v1":
            evaluation = Check(evaluation.name, FAIL, "mock/non-V1 report rejected", True)
        elif report.get("request_failures", 0) or report.get("status") == "FAIL":
            evaluation = Check(evaluation.name, FAIL, "live request failures/regression recorded", True)
        elif report.get("metrics", {}).get("correctness") is None:
            evaluation = Check(evaluation.name, NOT_RUN, "live captured; factual correctness oracle not yet measured", True)
        else:
            evaluation = Check(evaluation.name, NOT_RUN, "human review of oracle/quality thresholds still required", True)
    checks.append(evaluation)
    load = Check("14a health HTTP load", NOT_RUN, "run scripts/load_test.py")
    if args.load_report:
        report = json.loads(args.load_report.read_text("utf-8"))
        load = Check(load.name, PASS if report.get("scope") == "health" and report.get("requests", 0) > 0
                     and report.get("failures") == 0 else FAIL, str(args.load_report))
    chat_load = Check("14b production-representative chat load", NOT_RUN,
                      "health load alone does not measure model throughput", True)
    if args.chat_load_report:
        report = json.loads(args.chat_load_report.read_text("utf-8"))
        if report.get("scope") != "chat" or not report.get("requests", 0):
            chat_load = Check(chat_load.name, FAIL, "invalid chat load evidence", True)
        elif report.get("failures", 0):
            chat_load = Check(chat_load.name, FAIL, f"{report['failures']}/{report['requests']} requests failed", True)
        else:
            chat_load = Check(chat_load.name, NOT_RUN, "sample measured; representative workload and SLA review required", True)
    checks.extend([load, chat_load])
    out = render("2.0.0-alpha", checks, str(args.evaluation_report or "live benchmark not supplied"))
    (ROOT / "RELEASE_READINESS_REPORT.md").write_text(out, "utf-8")
    print(out)
    return 1 if verdict(checks) == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
