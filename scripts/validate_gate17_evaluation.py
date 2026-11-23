from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.research.experiment import (
    ControlledExperiment,
)
from app.research.experiment_evaluator import (
    EvaluationError,
    ExperimentEvaluator,
)


ENGINE = ControlledExperiment()
EVALUATOR = ExperimentEvaluator()

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


def experiment_kwargs():
    return {
        "proposal_id": "PROP-GAP-0001",
        "hypothesis": (
            "Peningkatan retrieval meningkatkan "
            "relevansi evidence."
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


def valid_result():
    return ENGINE.run(
        **experiment_kwargs()
    )


def valid_evaluation():
    result = EVALUATOR.evaluate(
        valid_result()
    )

    assert result.evaluation_id.startswith(
        "EVAL-"
    )
    assert result.experiment_id
    assert result.proposal_id
    assert result.verdict == "IMPROVEMENT"
    assert result.evidence_valid is True
    assert result.metrics_valid is True
    assert result.eligible_for_next_gate is True


def experiment_binding():
    result = valid_result()

    evaluation = EVALUATOR.evaluate(
        result
    )

    assert evaluation.experiment_id == (
        result.experiment_id
    )

    assert evaluation.proposal_id == (
        result.proposal_id
    )


def improvement_accepted():
    result = valid_result()

    evaluation = EVALUATOR.evaluate(
        result
    )

    assert evaluation.verdict == "IMPROVEMENT"
    assert evaluation.eligible_for_next_gate is True


def no_change_rejected():
    kwargs = experiment_kwargs()

    kwargs["candidate"] = (
        kwargs["baseline"].copy()
    )

    result = ENGINE.run(**kwargs)
    evaluation = EVALUATOR.evaluate(
        result
    )

    assert evaluation.verdict == "NO_CHANGE"
    assert evaluation.eligible_for_next_gate is False


def regression_rejected():
    kwargs = experiment_kwargs()

    kwargs["candidate"] = {
        "relevance": 0.50,
        "grounding": 0.60,
    }

    result = ENGINE.run(**kwargs)
    evaluation = EVALUATOR.evaluate(
        result
    )

    assert evaluation.verdict == "REGRESSION"
    assert evaluation.eligible_for_next_gate is False


def inconclusive_rejected():
    kwargs = experiment_kwargs()

    kwargs["candidate"] = {
        "relevance": 0.90,
        "grounding": 0.70,
    }

    result = ENGINE.run(**kwargs)
    evaluation = EVALUATOR.evaluate(
        result
    )

    assert evaluation.verdict == "INCONCLUSIVE"
    assert evaluation.eligible_for_next_gate is False


def invalid_delta_blocked():
    result = valid_result()

    broken = replace(
        result,
        delta={
            "relevance": 999.0,
            "grounding": 999.0,
        },
    )

    try:
        EVALUATOR.evaluate(broken)
    except EvaluationError:
        return

    raise AssertionError(
        "delta invalid diterima"
    )


def invalid_evidence_blocked():
    result = valid_result()

    broken = replace(
        result,
        evidence=(),
    )

    try:
        EVALUATOR.evaluate(broken)
    except EvaluationError:
        return

    raise AssertionError(
        "evidence kosong diterima"
    )


def duplicate_evidence_blocked():
    result = valid_result()

    broken = replace(
        result,
        evidence=(
            "EVD-001",
            "EVD-001",
        ),
    )

    try:
        EVALUATOR.evaluate(broken)
    except EvaluationError:
        return

    raise AssertionError(
        "duplicate evidence diterima"
    )


def invalid_verdict_blocked():
    result = valid_result()

    broken = replace(
        result,
        verdict="INVALID",
    )

    try:
        EVALUATOR.evaluate(broken)
    except EvaluationError:
        return

    raise AssertionError(
        "verdict invalid diterima"
    )


def deterministic_evaluation_id():
    result = valid_result()

    a = EVALUATOR.evaluate(result)
    b = EVALUATOR.evaluate(result)

    assert a.evaluation_id == (
        b.evaluation_id
    )


def payload_serializable():
    result = valid_result()

    evaluation = EVALUATOR.evaluate(
        result
    )

    payload = EVALUATOR.to_payload(
        evaluation
    )

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert encoded
    assert evaluation.evaluation_id in encoded


def production_mutation_blocked():
    source = (
        ROOT
        / "app"
        / "research"
        / "experiment_evaluator.py"
    ).read_text(
        encoding="utf-8"
    )

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
            "Forbidden mutation primitive: "
            + pattern
        )


print("=" * 72)
print("NUSANTARA GATE 17.6")
print("EXPERIMENT EVALUATION CONTRACT")
print("=" * 72)

check(
    "17.6.1 Valid evaluation",
    valid_evaluation,
)

check(
    "17.6.2 Experiment binding",
    experiment_binding,
)

check(
    "17.6.3 IMPROVEMENT accepted",
    improvement_accepted,
)

check(
    "17.6.4 NO_CHANGE rejected",
    no_change_rejected,
)

check(
    "17.6.5 REGRESSION rejected",
    regression_rejected,
)

check(
    "17.6.6 INCONCLUSIVE rejected",
    inconclusive_rejected,
)

check(
    "17.6.7 Invalid delta blocked",
    invalid_delta_blocked,
)

check(
    "17.6.8 Empty evidence blocked",
    invalid_evidence_blocked,
)

check(
    "17.6.9 Duplicate evidence blocked",
    duplicate_evidence_blocked,
)

check(
    "17.6.10 Invalid verdict blocked",
    invalid_verdict_blocked,
)

check(
    "17.6.11 Deterministic evaluation ID",
    deterministic_evaluation_id,
)

check(
    "17.6.12 Payload serializable",
    payload_serializable,
)

check(
    "17.6.13 Production mutation blocked",
    production_mutation_blocked,
)

print("-" * 72)
print(f"VALIDATION CHECKS : {passed + failed}")
print(f"PASS              : {passed}")
print(f"FAIL              : {failed}")
print("-" * 72)

if failed == 0:
    print("GATE 17.6 FINAL   : PASS")
    print("PRODUCTION WRITE  : NOT ENABLED")
    print("EXECUTION         : NOT ENABLED")
    print("EVALUATION        : DETERMINISTIC")
else:
    print("GATE 17.6 FINAL   : FAIL")
    raise SystemExit(1)

print("=" * 72)
