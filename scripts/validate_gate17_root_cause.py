from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.research.root_cause import (
    RootCauseAnalyzer,
    RootCauseAnalysisError,
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


analyzer = RootCauseAnalyzer()


def make_evidence():
    return [
        {
            "evidence_id": "EVD-001",
            "source": "evaluation",
            "evidence_type": "retrieval",
            "data": {
                "expected": "KTP-el",
                "retrieved": False,
            },
        },
        {
            "evidence_id": "EVD-002",
            "source": "runtime",
            "evidence_type": "trace",
            "data": {
                "retrieval_top_k": 5,
                "relevant_hits": 0,
            },
        },
    ]


def make_candidates():
    return [
        {
            "cause": "retrieval ranking kurang tepat",
            "evidence_ids": [
                "EVD-001",
                "EVD-002",
            ],
            "confidence": 0.82,
            "rationale": (
                "Evidence menunjukkan query relevan "
                "tidak masuk hasil retrieval."
            ),
        },
        {
            "cause": "chunking kurang sesuai",
            "evidence_ids": [
                "EVD-001",
            ],
            "confidence": 0.46,
            "rationale": (
                "Chunking merupakan alternatif yang "
                "masih perlu diuji."
            ),
        },
    ]


def valid_analysis():
    result = analyzer.analyze(
        gap_id="GAP-0001",
        component="KnowledgeEngine",
        evidence=make_evidence(),
        candidates=make_candidates(),
    )

    assert result.analysis_id.startswith("RCA-")
    assert result.gap_id == "GAP-0001"
    assert result.component == "KnowledgeEngine"
    assert result.evidence_count == 2
    assert len(result.candidates) == 2
    assert (
        result.selected_cause
        == "retrieval ranking kurang tepat"
    )


def deterministic_analysis_id():
    kwargs = {
        "gap_id": "GAP-0001",
        "component": "KnowledgeEngine",
        "evidence": make_evidence(),
        "candidates": make_candidates(),
    }

    a = analyzer.analyze(**kwargs)
    b = analyzer.analyze(**kwargs)

    assert a.analysis_id == b.analysis_id
    assert a.to_payload() == b.to_payload()


def evidence_order_deterministic():
    evidence_a = make_evidence()

    evidence_b = list(reversed(evidence_a))

    candidates = make_candidates()

    a = analyzer.analyze(
        gap_id="GAP-ORDER",
        component="KnowledgeEngine",
        evidence=evidence_a,
        candidates=candidates,
    )

    b = analyzer.analyze(
        gap_id="GAP-ORDER",
        component="KnowledgeEngine",
        evidence=evidence_b,
        candidates=candidates,
    )

    assert a.analysis_id == b.analysis_id


def missing_evidence_blocked():
    try:
        analyzer.analyze(
            gap_id="GAP-0002",
            component="KnowledgeEngine",
            evidence=[],
            candidates=make_candidates(),
        )
    except RootCauseAnalysisError:
        return

    raise AssertionError(
        "Root cause tanpa evidence diterima"
    )


def missing_candidates_blocked():
    try:
        analyzer.analyze(
            gap_id="GAP-0003",
            component="KnowledgeEngine",
            evidence=make_evidence(),
            candidates=[],
        )
    except RootCauseAnalysisError:
        return

    raise AssertionError(
        "Root cause tanpa candidate diterima"
    )


def cause_without_evidence_blocked():
    try:
        analyzer.analyze(
            gap_id="GAP-0004",
            component="KnowledgeEngine",
            evidence=make_evidence(),
            candidates=[
                {
                    "cause": "unsupported cause",
                    "evidence_ids": [],
                    "confidence": 0.80,
                    "rationale": "Tidak ada evidence.",
                }
            ],
        )
    except RootCauseAnalysisError:
        return

    raise AssertionError(
        "Cause tanpa evidence diterima"
    )


def unknown_evidence_blocked():
    try:
        analyzer.analyze(
            gap_id="GAP-0005",
            component="KnowledgeEngine",
            evidence=make_evidence(),
            candidates=[
                {
                    "cause": "unknown cause",
                    "evidence_ids": ["EVD-NOT-FOUND"],
                    "confidence": 0.80,
                    "rationale": "Evidence tidak tersedia.",
                }
            ],
        )
    except RootCauseAnalysisError:
        return

    raise AssertionError(
        "Unknown evidence diterima"
    )


def confidence_range_blocked():
    for confidence in (-0.1, 1.1):
        try:
            analyzer.analyze(
                gap_id="GAP-0006",
                component="KnowledgeEngine",
                evidence=make_evidence(),
                candidates=[
                    {
                        "cause": "invalid confidence",
                        "evidence_ids": ["EVD-001"],
                        "confidence": confidence,
                        "rationale": "Invalid.",
                    }
                ],
            )
        except RootCauseAnalysisError:
            continue

        raise AssertionError(
            f"Confidence {confidence} diterima"
        )


def low_confidence_not_selected():
    result = analyzer.analyze(
        gap_id="GAP-0007",
        component="KnowledgeEngine",
        evidence=make_evidence(),
        candidates=[
            {
                "cause": "uncertain cause",
                "evidence_ids": ["EVD-001"],
                "confidence": 0.49,
                "rationale": "Evidence belum cukup kuat.",
            }
        ],
    )

    assert result.selected_cause is None


def highest_confidence_selected():
    result = analyzer.analyze(
        gap_id="GAP-0008",
        component="KnowledgeEngine",
        evidence=make_evidence(),
        candidates=[
            {
                "cause": "cause A",
                "evidence_ids": ["EVD-001"],
                "confidence": 0.61,
                "rationale": "Evidence A.",
            },
            {
                "cause": "cause B",
                "evidence_ids": ["EVD-002"],
                "confidence": 0.91,
                "rationale": "Evidence B.",
            },
        ],
    )

    assert result.selected_cause == "cause B"


def payload_serializable():
    result = analyzer.analyze(
        gap_id="GAP-0009",
        component="DeveloperCore",
        evidence=make_evidence(),
        candidates=make_candidates(),
    )

    encoded = json.dumps(
        result.to_payload(),
        ensure_ascii=False,
        sort_keys=True,
    )

    assert "RCA-" in encoded
    assert "KnowledgeEngine" not in encoded


def duplicate_evidence_blocked():
    evidence = make_evidence()
    evidence.append(
        dict(evidence[0])
    )

    try:
        analyzer.analyze(
            gap_id="GAP-0010",
            component="KnowledgeEngine",
            evidence=evidence,
            candidates=make_candidates(),
        )
    except RootCauseAnalysisError:
        return

    raise AssertionError(
        "Duplicate evidence diterima"
    )


def duplicate_cause_blocked():
    candidates = make_candidates()
    candidates.append(
        {
            "cause": candidates[0]["cause"],
            "evidence_ids": ["EVD-001"],
            "confidence": 0.70,
            "rationale": "Duplicate cause.",
        }
    )

    try:
        analyzer.analyze(
            gap_id="GAP-0011",
            component="KnowledgeEngine",
            evidence=make_evidence(),
            candidates=candidates,
        )
    except RootCauseAnalysisError:
        return

    raise AssertionError(
        "Duplicate cause diterima"
    )


def no_production_execution_api():
    source = (
        ROOT
        / "app"
        / "research"
        / "root_cause.py"
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
        "os.replace(",
        "open(",
        "write_text(",
        "write_bytes(",
        "unlink(",
        "rmtree(",
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
                "Forbidden production mutation primitive: "
                + pattern
            )


print("=" * 72)
print("NUSANTARA GATE 17.3")
print("ROOT CAUSE ANALYSIS CONTRACT")
print("=" * 72)

check(
    "17.3.1 Valid root-cause analysis",
    valid_analysis,
)

check(
    "17.3.2 Deterministic analysis ID",
    deterministic_analysis_id,
)

check(
    "17.3.3 Evidence order deterministic",
    evidence_order_deterministic,
)

check(
    "17.3.4 Missing evidence blocked",
    missing_evidence_blocked,
)

check(
    "17.3.5 Missing candidates blocked",
    missing_candidates_blocked,
)

check(
    "17.3.6 Cause without evidence blocked",
    cause_without_evidence_blocked,
)

check(
    "17.3.7 Unknown evidence blocked",
    unknown_evidence_blocked,
)

check(
    "17.3.8 Confidence range enforced",
    confidence_range_blocked,
)

check(
    "17.3.9 Low confidence not selected",
    low_confidence_not_selected,
)

check(
    "17.3.10 Highest confidence selected",
    highest_confidence_selected,
)

check(
    "17.3.11 Payload serializable",
    payload_serializable,
)

check(
    "17.3.12 Duplicate evidence blocked",
    duplicate_evidence_blocked,
)

check(
    "17.3.13 Duplicate cause blocked",
    duplicate_cause_blocked,
)

check(
    "17.3.14 Production mutation blocked",
    no_production_execution_api,
)

print("-" * 72)
print(f"VALIDATION CHECKS : {passed + failed}")
print(f"PASS              : {passed}")
print(f"FAIL              : {failed}")
print("-" * 72)

if failed == 0:
    print("GATE 17.3 FINAL   : PASS")
    print("PRODUCTION WRITE  : NOT ENABLED")
    print("EXECUTION         : NOT ENABLED")
    print("LLM               : NOT REQUIRED")
else:
    print("GATE 17.3 FINAL   : FAIL")
    raise SystemExit(1)

print("=" * 72)
