from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


VERDICTS = {
    "IMPROVEMENT",
    "NO_CHANGE",
    "REGRESSION",
    "INCONCLUSIVE",
}


class ExperimentError(ValueError):
    pass


@dataclass(frozen=True)
class ExperimentResult:
    experiment_id: str
    proposal_id: str
    hypothesis: str
    baseline: dict[str, float]
    candidate: dict[str, float]
    delta: dict[str, float]
    verdict: str
    evidence: tuple[str, ...]


class ControlledExperiment:
    """
    Gate 17.5.

    Controlled evaluation only.

    Tidak:
      - menulis source production
      - melakukan patch
      - menjalankan shell
      - menjalankan subprocess
      - melakukan deployment

    Engine hanya membandingkan baseline dan candidate metrics.
    """

    def run(
        self,
        *,
        proposal_id: str,
        hypothesis: str,
        baseline: dict[str, float],
        candidate: dict[str, float],
        evidence: list[str],
    ) -> ExperimentResult:

        self._validate(
            proposal_id=proposal_id,
            hypothesis=hypothesis,
            baseline=baseline,
            candidate=candidate,
            evidence=evidence,
        )

        if set(baseline) != set(candidate):
            raise ExperimentError(
                "baseline dan candidate harus memiliki metric yang sama"
            )

        delta = {
            key: round(
                float(candidate[key]) - float(baseline[key]),
                10,
            )
            for key in sorted(baseline)
        }

        verdict = self._evaluate(
            baseline=baseline,
            candidate=candidate,
        )

        experiment_id = self._experiment_id(
            proposal_id=proposal_id,
            hypothesis=hypothesis,
            baseline=baseline,
            candidate=candidate,
            evidence=evidence,
        )

        return ExperimentResult(
            experiment_id=experiment_id,
            proposal_id=proposal_id,
            hypothesis=hypothesis,
            baseline=dict(sorted(baseline.items())),
            candidate=dict(sorted(candidate.items())),
            delta=delta,
            verdict=verdict,
            evidence=tuple(sorted(set(evidence))),
        )

    @staticmethod
    def _validate(
        *,
        proposal_id: str,
        hypothesis: str,
        baseline: dict[str, float],
        candidate: dict[str, float],
        evidence: list[str],
    ) -> None:

        if not proposal_id.strip():
            raise ExperimentError(
                "proposal_id wajib"
            )

        if not hypothesis.strip():
            raise ExperimentError(
                "hypothesis wajib"
            )

        if not baseline:
            raise ExperimentError(
                "baseline wajib"
            )

        if not candidate:
            raise ExperimentError(
                "candidate wajib"
            )

        if not evidence:
            raise ExperimentError(
                "evidence wajib"
            )

        for name, metrics in (
            ("baseline", baseline),
            ("candidate", candidate),
        ):
            if not isinstance(metrics, dict):
                raise ExperimentError(
                    f"{name} harus dictionary"
                )

            for key, value in metrics.items():
                if not isinstance(key, str) or not key.strip():
                    raise ExperimentError(
                        f"{name} memiliki metric invalid"
                    )

                if isinstance(value, bool):
                    raise ExperimentError(
                        f"{name}.{key} tidak boleh boolean"
                    )

                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    raise ExperimentError(
                        f"{name}.{key} harus numeric"
                    )

                if numeric != numeric:
                    raise ExperimentError(
                        f"{name}.{key} tidak boleh NaN"
                    )

        normalized_evidence = [
            str(item).strip()
            for item in evidence
        ]

        if not all(normalized_evidence):
            raise ExperimentError(
                "evidence tidak boleh kosong"
            )

        if len(normalized_evidence) != len(set(normalized_evidence)):
            raise ExperimentError(
                "duplicate evidence tidak diperbolehkan"
            )

    @staticmethod
    def _evaluate(
        *,
        baseline: dict[str, float],
        candidate: dict[str, float],
    ) -> str:

        deltas = [
            float(candidate[key]) - float(baseline[key])
            for key in sorted(baseline)
        ]

        if all(delta > 0 for delta in deltas):
            return "IMPROVEMENT"

        if all(delta == 0 for delta in deltas):
            return "NO_CHANGE"

        if all(delta < 0 for delta in deltas):
            return "REGRESSION"

        return "INCONCLUSIVE"

    @staticmethod
    def _experiment_id(
        *,
        proposal_id: str,
        hypothesis: str,
        baseline: dict[str, float],
        candidate: dict[str, float],
        evidence: list[str],
    ) -> str:

        payload = {
            "proposal_id": proposal_id,
            "hypothesis": hypothesis,
            "baseline": dict(sorted(baseline.items())),
            "candidate": dict(sorted(candidate.items())),
            "evidence": sorted(set(evidence)),
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

        return f"EXP-{digest}"

    @staticmethod
    def to_payload(
        result: ExperimentResult,
    ) -> dict[str, Any]:

        return {
            "experiment_id": result.experiment_id,
            "proposal_id": result.proposal_id,
            "hypothesis": result.hypothesis,
            "baseline": result.baseline,
            "candidate": result.candidate,
            "delta": result.delta,
            "verdict": result.verdict,
            "evidence": list(result.evidence),
        }
