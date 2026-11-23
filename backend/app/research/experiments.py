"""Phase 16 - experiment engine. Hasil eksperimen tidak pernah di-deploy otomatis."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from app.evaluation.evaluator import EvalCase, compare, run_cases
from app.observability.context import new_id


@dataclass
class Experiment:
    experiment_id: str
    hypothesis: str
    baseline: str
    change: str
    dataset: str
    metrics: list[str]
    expected_result: str
    risk: str
    actual_result: dict[str, Any] | None = None
    status: str = "draft"
    deployment: str = "not_deployed"


class ExperimentRunner:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else None

    def define(self, *, hypothesis: str, baseline: str, change: str, dataset: str, metrics: list[str],
               expected_result: str, risk: str = "low") -> Experiment:
        if not hypothesis.strip() or not change.strip() or not metrics:
            raise ValueError("hypothesis, change, metrics wajib")
        if risk not in ("low", "medium", "high", "critical"):
            raise ValueError("risk tidak valid")
        return Experiment(new_id("exp"), hypothesis, baseline, change, dataset, metrics, expected_result, risk)

    def run(self, exp: Experiment, baseline_system: Callable[[str], dict[str, Any]],
            candidate_system: Callable[[str], dict[str, Any]], cases: list[EvalCase],
            tolerance: float = 0.05) -> Experiment:
        b = run_cases(baseline_system, cases)
        c = run_cases(candidate_system, cases)
        cmp = compare(b["metrics"], c["metrics"], tolerance)
        exp.actual_result = {"baseline": b, "candidate": c, "comparison": cmp, "verdict": cmp["verdict"]}
        exp.status = "completed"
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(exp), ensure_ascii=False, default=str) + "\n")
        return exp
