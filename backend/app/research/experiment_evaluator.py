from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from app.research.experiment import (
    ExperimentResult,
    VERDICTS,
)


class EvaluationError(ValueError):
    pass


ELIGIBLE_VERDICTS = {
    "IMPROVEMENT",
    "NO_CHANGE",
    "INCONCLUSIVE",
}

REJECTED_VERDICTS = {
    "REGRESSION",
}


@dataclass(frozen=True)
class EvaluationResult:
    evaluation_id: str
    experiment_id: str
    proposal_id: str
    verdict: str
    evidence_valid: bool
    metrics_valid: bool
    eligible_for_next_gate: bool
    reason: str


class ExperimentEvaluator:
    """
    Gate 17.6.

    Mengevaluasi hasil ControlledExperiment.

    Tidak melakukan:
      - write
      - patch
      - execute
      - subprocess
      - deployment
    """

    def evaluate(
        self,
        result: ExperimentResult,
    ) -> EvaluationResult:

        self._validate_result(result)

        metrics_valid = self._validate_metrics(result)
        evidence_valid = self._validate_evidence(result)

        if not metrics_valid:
            raise EvaluationError(
                "experiment metrics tidak valid"
            )

        if not evidence_valid:
            raise EvaluationError(
                "experiment evidence tidak valid"
            )

        if result.verdict == "REGRESSION":
            eligible = False
            reason = (
                "REGRESSION tidak eligible "
                "untuk improvement"
            )

        elif result.verdict == "IMPROVEMENT":
            eligible = True
            reason = (
                "Experiment menunjukkan improvement "
                "dan evidence valid"
            )

        elif result.verdict == "NO_CHANGE":
            eligible = False
            reason = (
                "Tidak terdapat perubahan metric"
            )

        elif result.verdict == "INCONCLUSIVE":
            eligible = False
            reason = (
                "Hasil experiment belum konklusif"
            )

        else:
            raise EvaluationError(
                "verdict tidak dikenal"
            )

        evaluation_id = self._evaluation_id(
            result=result,
            evidence_valid=evidence_valid,
            metrics_valid=metrics_valid,
            eligible=eligible,
        )

        return EvaluationResult(
            evaluation_id=evaluation_id,
            experiment_id=result.experiment_id,
            proposal_id=result.proposal_id,
            verdict=result.verdict,
            evidence_valid=evidence_valid,
            metrics_valid=metrics_valid,
            eligible_for_next_gate=eligible,
            reason=reason,
        )

    @staticmethod
    def _validate_result(
        result: ExperimentResult,
    ) -> None:

        if not isinstance(
            result,
            ExperimentResult,
        ):
            raise EvaluationError(
                "result harus ExperimentResult"
            )

        if not result.experiment_id.strip():
            raise EvaluationError(
                "experiment_id wajib"
            )

        if not result.proposal_id.strip():
            raise EvaluationError(
                "proposal_id wajib"
            )

        if not result.hypothesis.strip():
            raise EvaluationError(
                "hypothesis wajib"
            )

        if result.verdict not in VERDICTS:
            raise EvaluationError(
                "verdict tidak valid"
            )

    @staticmethod
    def _validate_metrics(
        result: ExperimentResult,
    ) -> bool:

        if not result.baseline:
            return False

        if not result.candidate:
            return False

        if set(result.baseline) != set(
            result.candidate
        ):
            return False

        if set(result.delta) != set(
            result.baseline
        ):
            return False

        for key in result.baseline:
            baseline = float(
                result.baseline[key]
            )

            candidate = float(
                result.candidate[key]
            )

            delta = float(
                result.delta[key]
            )

            expected = round(
                candidate - baseline,
                10,
            )

            if delta != expected:
                return False

        return True

    @staticmethod
    def _validate_evidence(
        result: ExperimentResult,
    ) -> bool:

        if not result.evidence:
            return False

        normalized = [
            str(item).strip()
            for item in result.evidence
        ]

        if not all(normalized):
            return False

        if len(normalized) != len(
            set(normalized)
        ):
            return False

        return True

    @staticmethod
    def _evaluation_id(
        *,
        result: ExperimentResult,
        evidence_valid: bool,
        metrics_valid: bool,
        eligible: bool,
    ) -> str:

        payload = {
            "experiment_id":
                result.experiment_id,
            "proposal_id":
                result.proposal_id,
            "verdict":
                result.verdict,
            "baseline":
                result.baseline,
            "candidate":
                result.candidate,
            "delta":
                result.delta,
            "evidence":
                list(result.evidence),
            "evidence_valid":
                evidence_valid,
            "metrics_valid":
                metrics_valid,
            "eligible":
                eligible,
        }

        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

        digest = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()[:16]

        return f"EVAL-{digest}"

    @staticmethod
    def to_payload(
        result: EvaluationResult,
    ) -> dict[str, Any]:

        return {
            "evaluation_id":
                result.evaluation_id,
            "experiment_id":
                result.experiment_id,
            "proposal_id":
                result.proposal_id,
            "verdict":
                result.verdict,
            "evidence_valid":
                result.evidence_valid,
            "metrics_valid":
                result.metrics_valid,
            "eligible_for_next_gate":
                result.eligible_for_next_gate,
            "reason":
                result.reason,
        }
