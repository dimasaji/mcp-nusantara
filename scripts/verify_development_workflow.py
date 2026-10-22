"""Verify the workflow fixes using the existing protected offline runner."""

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

offline = importlib.import_module("scripts.test_v1_sop_boundary")


if __name__ == "__main__":
    offline.TESTS = [*offline.TESTS,
        "tests/test_pytest_collection.py",
        "tests/test_audit_regressions.py::test_authorized_ingest_keeps_path_literal",
        "tests/test_audit_regressions.py::test_search_empty_and_populated_results",
        "tests/test_audit_regressions.py::test_slow_knowledge_work_keeps_event_loop_responsive",
        "tests/test_audit_regressions.py::test_knowledge_http_denies_before_backend",
        "tests/test_configuration_integration.py::test_provider_payload_uses_snapshot_and_request_precedence",
        "tests/test_configuration_integration.py::test_legacy_provider_and_explicit_nondefault_arguments",
    ]
    raise SystemExit(offline.main())
