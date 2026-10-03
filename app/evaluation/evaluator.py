"""Phase 12 - evaluasi 10 dimensi + baseline + deteksi REGRESSION. Tidak pernah auto-accept."""
from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from app.rag.store import tokenize

DIMENSIONS = ("correctness", "relevance", "groundedness", "retrieval_quality", "tool_accuracy",
              "policy_compliance", "latency", "reliability", "consistency", "cost")


@dataclass
class EvalCase:
    case_id: str
    query: str
    expected_contains: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    expected_docs: list[str] | None = None
    expected_tool: str | None = None      # None = tidak dinilai; "none" = harus tanpa tool
    expected_policy: str | None = None
    requires_evidence: bool = False


@dataclass
class EvalRecord:
    case_id: str
    answer: str = ""
    evidence: list[str] = field(default_factory=list)
    retrieved_doc_ids: list[str] = field(default_factory=list)
    tool_called: str | None = None
    policy_decision: str | None = None
    latency_ms: float = 0.0
    error: bool = False
    cost: float = 0.0
    repeat_answers: list[str] = field(default_factory=list)


def score_record(case: EvalCase, rec: EvalRecord, *, latency_target_ms: float = 2000.0,
                 cost_budget: float | None = None) -> dict[str, float | None]:
    ans = rec.answer.casefold()
    s: dict[str, float | None] = dict.fromkeys(DIMENSIONS)
    if case.expected_contains:
        s["correctness"] = sum(k.casefold() in ans for k in case.expected_contains) / len(case.expected_contains)
    q = set(tokenize(case.query))
    if q:
        s["relevance"] = len(q & set(tokenize(rec.answer))) / len(q)
    if rec.evidence:
        ev = set(tokenize(" ".join(rec.evidence)))
        at = [t for t in set(tokenize(rec.answer)) if len(t) > 3]
        s["groundedness"] = (sum(t in ev for t in at) / len(at)) if at else None
    elif case.requires_evidence:
        s["groundedness"] = 0.0
    if case.expected_docs:
        s["retrieval_quality"] = len(set(case.expected_docs) & set(rec.retrieved_doc_ids)) / len(set(case.expected_docs))
    if case.expected_tool is not None:
        want = None if case.expected_tool == "none" else case.expected_tool
        s["tool_accuracy"] = 1.0 if rec.tool_called == want else 0.0
    if case.expected_policy is not None or case.forbidden:
        ok = not any(f.casefold() in ans for f in case.forbidden)
        if case.expected_policy is not None:
            ok = ok and rec.policy_decision == case.expected_policy
        s["policy_compliance"] = 1.0 if ok else 0.0
    s["latency"] = 1.0 if rec.latency_ms <= 0 else min(1.0, latency_target_ms / rec.latency_ms)
    s["reliability"] = 0.0 if rec.error else 1.0
    if len(rec.repeat_answers) > 1:
        norm = Counter(a.strip().casefold() for a in rec.repeat_answers)
        s["consistency"] = norm.most_common(1)[0][1] / len(rec.repeat_answers)
    if cost_budget:
        s["cost"] = 1.0 if rec.cost <= 0 else min(1.0, cost_budget / rec.cost)
    return s


def aggregate(scores: list[dict[str, float | None]]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for d in DIMENSIONS:
        vals = [x[d] for x in scores if x.get(d) is not None]
        out[d] = round(sum(vals) / len(vals), 4) if vals else None
    return out


def run_cases(system: Callable[[str], dict[str, Any]], cases: list[EvalCase], *, repeats: int = 1,
              **score_kw: Any) -> dict[str, Any]:
    scores = []
    for c in cases:
        answers, rec = [], None
        for _ in range(max(1, repeats)):
            t0 = time.perf_counter()
            try:
                data = dict(system(c.query))
                data.setdefault("latency_ms", (time.perf_counter() - t0) * 1000)
                rec = EvalRecord(case_id=c.case_id, **{k: v for k, v in data.items() if k in EvalRecord.__dataclass_fields__ and k != "case_id"})
            except Exception:  # noqa: BLE001
                rec = EvalRecord(case_id=c.case_id, error=True, latency_ms=(time.perf_counter() - t0) * 1000)
            answers.append(rec.answer)
        rec.repeat_answers = answers
        scores.append(score_record(c, rec, **score_kw))
    return {"cases": len(cases), "metrics": aggregate(scores)}


def compare(baseline: dict[str, float | None], candidate: dict[str, float | None],
            tolerance: float = 0.05) -> dict[str, Any]:
    dims: dict[str, Any] = {}
    for d in DIMENSIONS:
        b, c = baseline.get(d), candidate.get(d)
        if b is None or c is None:
            continue
        delta = round(c - b, 4)
        dims[d] = {"baseline": b, "candidate": c, "delta": delta,
                   "status": "regressed" if delta < -tolerance else "improved" if delta > tolerance else "same"}
    reg = [d for d, v in dims.items() if v["status"] == "regressed"]
    imp = [d for d, v in dims.items() if v["status"] == "improved"]
    verdict = "REGRESSION" if reg else "IMPROVED" if imp else "NEUTRAL"
    return {"verdict": verdict, "regressed": reg, "improved": imp, "mixed": bool(reg and imp),
            "dimensions": dims, "auto_accept": False}


def save_baseline(path: Path, name: str, result: dict[str, Any], **meta: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({"name": name, "meta": meta, **result}, indent=2, ensure_ascii=False), "utf-8")


def load_baseline(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text("utf-8"))
