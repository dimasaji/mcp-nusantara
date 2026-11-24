from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.research.evidence_collector import (
    EvidenceCollector,
    EvidenceCollectionError,
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


collector = EvidenceCollector()


def valid_runtime_evidence():
    result = collector.collect(
        source="runtime",
        evidence_type="health",
        data={
            "status": "ok",
            "latency_ms": 120,
        },
    )

    assert result["source"] == "runtime"
    assert result["evidence_type"] == "health"
    assert result["data"]["status"] == "ok"


def valid_graph_evidence():
    result = collector.collect(
        source="graph",
        evidence_type="connectivity",
        data={
            "nodes": 2824,
            "links": 5920,
        },
    )

    assert result["source"] == "graph"
    assert result["data"]["nodes"] == 2824


def nested_data_normalized():
    result = collector.collect(
        source="evaluation",
        evidence_type="result",
        data={
            "metrics": {
                "recall": 0.8,
                "precision": 0.9,
            },
            "cases": [
                {"id": "B"},
                {"id": "A"},
            ],
        },
    )

    assert list(result["data"]["metrics"].keys()) == [
        "precision",
        "recall",
    ]


def invalid_source_blocked():
    try:
        collector.collect(
            source="random_source",
            evidence_type="test",
            data={"result": "fail"},
        )
    except EvidenceCollectionError:
        return

    raise AssertionError(
        "Invalid evidence source diterima"
    )


def empty_type_blocked():
    try:
        collector.collect(
            source="runtime",
            evidence_type="",
            data={"result": "fail"},
        )
    except EvidenceCollectionError:
        return

    raise AssertionError(
        "Evidence type kosong diterima"
    )


def non_dict_data_blocked():
    try:
        collector.collect(
            source="runtime",
            evidence_type="health",
            data=["invalid"],
        )
    except EvidenceCollectionError:
        return

    raise AssertionError(
        "Evidence non-dictionary diterima"
    )


def empty_data_blocked():
    try:
        collector.collect(
            source="runtime",
            evidence_type="health",
            data={},
        )
    except EvidenceCollectionError:
        return

    raise AssertionError(
        "Evidence kosong diterima"
    )


def collect_many_sorted():
    result = collector.collect_many(
        [
            {
                "source": "graph",
                "evidence_type": "z",
                "data": {"x": 1},
            },
            {
                "source": "runtime",
                "evidence_type": "a",
                "data": {"x": 2},
            },
            {
                "source": "evaluation",
                "evidence_type": "b",
                "data": {"x": 3},
            },
        ]
    )

    sources = [item["source"] for item in result]

    assert sources == sorted(sources)


def deterministic_normalization():
    data_a = {
        "z": 1,
        "a": {
            "y": 2,
            "x": 3,
        },
    }

    data_b = {
        "a": {
            "x": 3,
            "y": 2,
        },
        "z": 1,
    }

    a = collector.collect(
        source="test",
        evidence_type="deterministic",
        data=data_a,
    )

    b = collector.collect(
        source="test",
        evidence_type="deterministic",
        data=data_b,
    )

    assert a == b


def serializable_output():
    result = collector.collect(
        source="rag",
        evidence_type="retrieval",
        data={
            "query": "KTP-el",
            "top_k": 5,
            "matches": 3,
        },
    )

    encoded = json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert "KTP-el" in encoded


def no_production_execution_api():
    source = (
        ROOT
        / "app"
        / "research"
        / "evidence_collector.py"
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
                "Forbidden execution primitive: "
                + pattern
            )


print("=" * 72)
print("NUSANTARA GATE 17.2")
print("EVIDENCE COLLECTION CONTRACT")
print("=" * 72)

check(
    "17.2.1 Runtime evidence collected",
    valid_runtime_evidence,
)

check(
    "17.2.2 Graph evidence collected",
    valid_graph_evidence,
)

check(
    "17.2.3 Nested evidence normalized",
    nested_data_normalized,
)

check(
    "17.2.4 Invalid source blocked",
    invalid_source_blocked,
)

check(
    "17.2.5 Empty evidence type blocked",
    empty_type_blocked,
)

check(
    "17.2.6 Non-dictionary evidence blocked",
    non_dict_data_blocked,
)

check(
    "17.2.7 Empty evidence data blocked",
    empty_data_blocked,
)

check(
    "17.2.8 Multiple evidence deterministic",
    collect_many_sorted,
)

check(
    "17.2.9 Deterministic normalization",
    deterministic_normalization,
)

check(
    "17.2.10 Production execution blocked",
    no_production_execution_api,
)

print("-" * 72)
print(f"VALIDATION CHECKS : {passed + failed}")
print(f"PASS              : {passed}")
print(f"FAIL              : {failed}")
print("-" * 72)

if failed == 0:
    print("GATE 17.2 FINAL   : PASS")
    print("PRODUCTION WRITE  : NOT ENABLED")
    print("EXECUTION         : NOT ENABLED")
else:
    print("GATE 17.2 FINAL   : FAIL")
    raise SystemExit(1)

print("=" * 72)
