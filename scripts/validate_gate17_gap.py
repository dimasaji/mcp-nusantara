from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.research.gap_detector import (
    GapDetector,
    GapDetectionError,
)


passed = 0
failed = 0


def check(name: str, fn) -> None:
    global passed, failed

    try:
        fn()
        print(f"[PASS] {name}")
        passed += 1
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
        failed += 1


detector = GapDetector()


def valid_gap():
    gap = detector.detect(
        component="KnowledgeEngine",
        gap_type="retrieval",
        description="Relevant evidence tidak masuk top-k",
        severity="medium",
        evidence=[
            {
                "source": "evaluation",
                "case": "RAG-001",
                "result": "miss",
            }
        ],
    )

    assert gap.gap_id.startswith("GAP-")
    assert gap.component == "KnowledgeEngine"
    assert gap.gap_type == "retrieval"
    assert gap.severity == "medium"
    assert len(gap.evidence) == 1


def deterministic_id():
    kwargs = {
        "component": "KnowledgeEngine",
        "gap_type": "retrieval",
        "description": "Relevant evidence tidak masuk top-k",
        "severity": "medium",
        "evidence": [
            {"source": "evaluation", "case": "RAG-001"},
            {"source": "runtime", "latency_ms": 120},
        ],
    }

    a = detector.detect(**kwargs)
    b = detector.detect(**kwargs)

    assert a.gap_id == b.gap_id


def evidence_order_deterministic():
    common = {
        "component": "RAG",
        "gap_type": "quality",
        "description": "Evidence mismatch",
        "severity": "medium",
    }

    a = detector.detect(
        **common,
        evidence=[
            {"source": "b"},
            {"source": "a"},
        ],
    )

    b = detector.detect(
        **common,
        evidence=[
            {"source": "a"},
            {"source": "b"},
        ],
    )

    assert a.gap_id == b.gap_id


def missing_evidence_blocked():
    try:
        detector.detect(
            component="KnowledgeEngine",
            gap_type="retrieval",
            description="Tidak ada evidence",
            severity="medium",
            evidence=[],
        )
    except GapDetectionError:
        return

    raise AssertionError("Gap tanpa evidence diterima")


def invalid_component_blocked():
    try:
        detector.detect(
            component="",
            gap_type="retrieval",
            description="Test",
            severity="medium",
            evidence=[{"source": "test"}],
        )
    except GapDetectionError:
        return

    raise AssertionError("Component kosong diterima")


def invalid_gap_type_blocked():
    try:
        detector.detect(
            component="KnowledgeEngine",
            gap_type="made_up_type",
            description="Test",
            severity="medium",
            evidence=[{"source": "test"}],
        )
    except GapDetectionError:
        return

    raise AssertionError("Gap type invalid diterima")


def invalid_severity_blocked():
    try:
        detector.detect(
            component="KnowledgeEngine",
            gap_type="retrieval",
            description="Test",
            severity="unknown_severity",
            evidence=[{"source": "test"}],
        )
    except GapDetectionError:
        return

    raise AssertionError("Severity invalid diterima")


def empty_evidence_item_blocked():
    try:
        detector.detect(
            component="KnowledgeEngine",
            gap_type="retrieval",
            description="Test",
            severity="medium",
            evidence=[{}],
        )
    except GapDetectionError:
        return

    raise AssertionError("Evidence kosong diterima")


def payload_is_serializable():
    gap = detector.detect(
        component="DeveloperCore",
        gap_type="architecture",
        description="Dependency relation perlu ditinjau",
        severity="low",
        evidence=[
            {
                "source": "graph",
                "nodes": 2824,
                "links": 5920,
            }
        ],
    )

    import json

    payload = gap.to_payload()

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert "GAP-" in encoded


def no_production_execution_api():
    source = (
        ROOT / "app" / "research" / "gap_detector.py"
    ).read_text(encoding="utf-8")

    forbidden_patterns = [
        "import subprocess",
        "from subprocess import",
        "subprocess.",
        "os.system(",
        "os.popen(",
        "os.spawn",
        "os.exec",
        "subprocess.run(",
        "subprocess.Popen(",
        "subprocess.call(",
        "subprocess.check_call(",
        "subprocess.check_output(",
    ]

    active_lines = []

    for line in source.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("#"):
            continue

        active_lines.append(stripped.lower())

    active_source = "\n".join(active_lines)

    for pattern in forbidden_patterns:
        if pattern.lower() in active_source:
            raise AssertionError(
                f"Forbidden execution primitive ditemukan: {pattern}"
            )


print("=" * 72)
print("NUSANTARA GATE 17.1")
print("GAP DETECTION CONTRACT")
print("=" * 72)

check("17.1.1 Valid gap detected", valid_gap)
check("17.1.2 Deterministic GAP ID", deterministic_id)
check("17.1.3 Evidence order deterministic", evidence_order_deterministic)
check("17.1.4 Gap tanpa evidence blocked", missing_evidence_blocked)
check("17.1.5 Empty component blocked", invalid_component_blocked)
check("17.1.6 Invalid gap type blocked", invalid_gap_type_blocked)
check("17.1.7 Invalid severity blocked", invalid_severity_blocked)
check("17.1.8 Empty evidence blocked", empty_evidence_item_blocked)
check("17.1.9 Payload serializable", payload_is_serializable)
check("17.1.10 Production execution blocked", no_production_execution_api)

print("-" * 72)
print(f"VALIDATION CHECKS : {passed + failed}")
print(f"PASS              : {passed}")
print(f"FAIL              : {failed}")
print("-" * 72)

if failed == 0:
    print("GATE 17.1 FINAL   : PASS")
    print("PRODUCTION WRITE  : NOT ENABLED")
    print("EXECUTION         : NOT ENABLED")
else:
    print("GATE 17.1 FINAL   : FAIL")
    raise SystemExit(1)

print("=" * 72)
