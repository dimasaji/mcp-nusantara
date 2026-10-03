"""Phase 14 - gap detection. Menghasilkan kandidat gap; tidak ada self-modification."""
from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.rag.store import tokenize
from app.research.failure_analysis import FailureReport

GAP_TYPES = ("KNOWLEDGE_GAP", "CAPABILITY_GAP", "TOOL_GAP", "DATA_GAP", "POLICY_GAP", "RAG_GAP",
             "MEMORY_GAP", "EVALUATION_GAP")
_CAT_TO_GAP = {"RAG_FAILURE": "RAG_GAP", "TOOL_FAILURE": "TOOL_GAP", "MEMORY_FAILURE": "MEMORY_GAP",
               "POLICY_FAILURE": "POLICY_GAP", "MODEL_FAILURE": "CAPABILITY_GAP", "DATA_FAILURE": "DATA_GAP"}
_SEV = ["low", "medium", "high", "critical"]


@dataclass
class GapCandidate:
    gap_id: str
    gap_type: str
    description: str
    evidence: list[str]
    frequency: int
    severity: str
    confidence: float  # heuristik: min(1, frekuensi / (3 x ambang)); bukan probabilitas terkalibrasi
    source: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _gid(kind: str, key: str) -> str:
    return "GAP-" + hashlib.sha1(f"{kind}|{key}".encode()).hexdigest()[:8]


def detect_gaps(report: FailureReport, *, unanswered_queries: list[str] | None = None,
                missing_eval_dimensions: list[str] | None = None, min_frequency: int = 3) -> list[GapCandidate]:
    gaps: list[GapCandidate] = []
    for p in report.patterns:
        if p.count < min_frequency or p.category not in _CAT_TO_GAP:
            continue
        gt = _CAT_TO_GAP[p.category]
        gaps.append(GapCandidate(_gid(gt, f"{p.category}:{p.stage}"), gt,
                                 f"{p.count} kegagalan {p.category} pada tahap '{p.stage}'",
                                 [f"request_id={r}" for r in p.example_request_ids], p.count, p.severity,
                                 round(min(1.0, p.count / (3 * min_frequency)), 2), "failure_analysis"))
    groups: dict[str, list[str]] = {}
    for q in unanswered_queries or []:
        key = " ".join(sorted(set(tokenize(q))))
        if key:
            groups.setdefault(key, []).append(q)
    for key, qs in groups.items():
        if len(qs) >= min_frequency:
            gaps.append(GapCandidate(_gid("KNOWLEDGE_GAP", key), "KNOWLEDGE_GAP",
                                     f"Pertanyaan serupa berulang tanpa evidence: '{qs[0][:80]}'",
                                     [q[:120] for q in qs[:3]], len(qs), "medium",
                                     round(min(1.0, len(qs) / (3 * min_frequency)), 2), "query_log"))
    for d in missing_eval_dimensions or []:
        gaps.append(GapCandidate(_gid("EVALUATION_GAP", d), "EVALUATION_GAP",
                                 f"Dimensi evaluasi '{d}' belum terukur", [f"dimension={d}"], 1, "low", 0.5,
                                 "evaluation"))
    gaps.sort(key=lambda g: (_SEV.index(g.severity), g.frequency), reverse=True)
    return gaps
