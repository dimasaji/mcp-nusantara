from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.research.experiment import (
    ControlledExperiment,
    ExperimentError,
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


ENGINE = ControlledExperiment()


def base_kwargs():
    return {
        "proposal_id": "PROP-GAP-0001",
        "hypothesis": (
            "Peningkatan ranking retrieval "
            "meningkatkan relevansi evidence."
        ),
        "baseline": {
            "relevance": 0.70,
            "grounding": 0.80,
        },
        "candidate": {
            "relevance": 0.85,
            "grounding": 0.90,
        },
        "evidence": [
            "EVD-001",
            "EVD-002",
        ],
    }


def valid_experiment():
    result = ENGINE.run(**base_kwargs())

    assert result.experiment_id.startswith("EXP-")
    assert result.proposal_id == "PROP-GAP-0001"
    assert result.hypothesis
    assert result.verdict == "IMPROVEMENT"


def proposal_binding():
    result = ENGINE.run(**base_kwargs())

    assert result.proposal_id == (
        base_kwargs()["proposal_id"]
    )


def evidence_required():
    kwargs = base_kwargs()
    kwargs["evidence"] = []

    try:
        ENGINE.run(**kwargs)
    except ExperimentError:
        return

    raise AssertionError(
        "experiment tanpa evidence diterima"
    )


def hypothesis_required():
    kwargs = base_kwargs()
    kwargs["hypothesis"] = ""

    try:
        ENGINE.run(**kwargs)
    except ExperimentError:
        return

    raise AssertionError(
        "experiment tanpa hypothesis diterima"
    )


def baseline_required():
    kwargs = base_kwargs()
    kwargs["baseline"] = {}

    try:
        ENGINE.run(**kwargs)
    except ExperimentError:
        return

    raise AssertionError(
        "experiment tanpa baseline diterima"
    )


def candidate_required():
    kwargs = base_kwargs()
    kwargs["candidate"] = {}

    try:
        ENGINE.run(**kwargs)
    except ExperimentError:
        return

    raise AssertionError(
        "experiment tanpa candidate diterima"
    )


def metric_schema_must_match():
    kwargs = base_kwargs()
    kwargs["candidate"] = {
        "relevance": 0.90,
        "latency": 0.40,
    }

    try:
        ENGINE.run(**kwargs)
    except ExperimentError:
        return

    raise AssertionError(
        "metric schema berbeda diterima"
    )


def improvement_detected():
    kwargs = base_kwargs()

    result = ENGINE.run(**kwargs)

    assert result.verdict == "IMPROVEMENT"
    assert result.delta["relevance"] > 0
    assert result.delta["grounding"] > 0


def no_change_detected():
    kwargs = base_kwargs()
    kwargs["candidate"] = kwargs["baseline"].copy()

    result = ENGINE.run(**kwargs)

    assert result.verdict == "NO_CHANGE"


def regression_detected():
    kwargs = base_kwargs()
    kwargs["candidate"] = {
        "relevance": 0.50,
        "grounding": 0.60,
    }

    result = ENGINE.run(**kwargs)

    assert result.verdict == "REGRESSION"


def inconclusive_detected():
    kwargs = base_kwargs()
    kwargs["candidate"] = {
        "relevance": 0.90,
        "grounding": 0.70,
    }

    result = ENGINE.run(**kwargs)

    assert result.verdict == "INCONCLUSIVE"


def deterministic_id():
    a = ENGINE.run(**base_kwargs())
    b = ENGINE.run(**base_kwargs())

    assert a.experiment_id == b.experiment_id


def evidence_deterministic():
    kwargs_a = base_kwargs()
    kwargs_b = base_kwargs()

    kwargs_a["evidence"] = [
        "EVD-002",
        "EVD-001",
    ]

    kwargs_b["evidence"] = [
        "EVD-001",
        "EVD-002",
    ]

    a = ENGINE.run(**kwargs_a)
    b = ENGINE.run(**kwargs_b)

    assert a.experiment_id == b.experiment_id
    assert a.evidence == b.evidence


def duplicate_evidence_blocked():
    kwargs = base_kwargs()
    kwargs["evidence"] = [
        "EVD-001",
        "EVD-001",
    ]

    try:
        ENGINE.run(**kwargs)
    except ExperimentError:
        return

    raise AssertionError(
        "duplicate evidence diterima"
    )


def invalid_metric_blocked():
    kwargs = base_kwargs()
    kwargs["candidate"] = {
        "relevance": "invalid",
        "grounding": 0.90,
    }

    try:
        ENGINE.run(**kwargs)
    except ExperimentError:
        return

    raise AssertionError(
        "metric non-numeric diterima"
    )


def payload_serializable():
    result = ENGINE.run(**base_kwargs())

    payload = ENGINE.to_payload(result)

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert encoded
    assert result.experiment_id in encoded


def no_production_mutation():
    source = (
        ROOT
        / "app"
        / "research"
        / "experiment.py"
    ).read_text(encoding="utf-8")

    forbidden = [
        "import subprocess",
        "from subprocess import",
        "subprocess.run(",
        "subprocess.Popen(",
        "subprocess.call(",
        "os.system(",
        "os.popen(",
        "os.spawn",
        "os.exec",
        "os.replace(",
        "write_text(",
        "write_bytes(",
        "unlink(",
        "rmtree(",
    ]

    for pattern in forbidden:
        assert pattern not in source, (
            "Forbidden production mutation primitive: "
            + pattern
        )


print("=" * 72)
print("NUSANTARA GATE 17.5")
print("CONTROLLED EXPERIMENT CONTRACT")
print("=" * 72)

check(
    "17.5.1 Valid experiment",
    valid_experiment,
)

check(
    "17.5.2 Proposal binding",
    proposal_binding,
)

check(
    "17.5.3 Evidence required",
    evidence_required,
)

check(
    "17.5.4 Hypothesis required",
    hypothesis_required,
)

check(
    "17.5.5 Baseline required",
    baseline_required,
)

check(
    "17.5.6 Candidate required",
    candidate_required,
)

check(
    "17.5.7 Metric schema consistency",
    metric_schema_must_match,
)

check(
    "17.5.8 IMPROVEMENT detected",
    improvement_detected,
)

check(
    "17.5.9 NO_CHANGE detected",
    no_change_detected,
)

check(
    "17.5.10 REGRESSION detected",
    regression_detected,
)

check(
    "17.5.11 INCONCLUSIVE detected",
    inconclusive_detected,
)

check(
    "17.5.12 Deterministic experiment ID",
    deterministic_id,
)

check(
    "17.5.13 Evidence deterministic",
    evidence_deterministic,
)

check(
    "17.5.14 Duplicate evidence blocked",
    duplicate_evidence_blocked,
)

check(
    "17.5.15 Invalid metric blocked",
    invalid_metric_blocked,
)

check(
    "17.5.16 Payload serializable",
    payload_serializable,
)

check(
    "17.5.17 Production mutation blocked",
    no_production_mutation,
)

print("-" * 72)
print(f"VALIDATION CHECKS : {passed + failed}")
print(f"PASS              : {passed}")
print(f"FAIL              : {failed}")
print("-" * 72)

if failed == 0:
    print("GATE 17.5 FINAL   : PASS")
    print("PRODUCTION WRITE  : NOT ENABLED")
    print("EXECUTION         : NOT ENABLED")
    print("EXPERIMENT        : CONTROLLED")
else:
    print("GATE 17.5 FINAL   : FAIL")
    raise SystemExit(1)

print("=" * 72)
