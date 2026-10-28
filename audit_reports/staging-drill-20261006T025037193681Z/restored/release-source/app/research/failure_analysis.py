"""Phase 13 - failure analysis. Hanya menganalisis & merekomendasikan; tidak mengubah kode."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

CATEGORIES = ("INPUT_FAILURE", "MODEL_FAILURE", "RAG_FAILURE", "MEMORY_FAILURE", "TOOL_FAILURE",
              "POLICY_FAILURE", "SYSTEM_FAILURE", "DATA_FAILURE", "USER_ERROR", "UNKNOWN")
PIPELINE_ORDER = ["input", "policy", "memory_read", "understand", "retrieve", "generate", "trust",
                  "memory_write", "tool", "feedback"]
STAGE_TO_CAT = {"input": "INPUT_FAILURE", "policy": "POLICY_FAILURE", "memory_read": "MEMORY_FAILURE",
                "memory_write": "MEMORY_FAILURE", "understand": "SYSTEM_FAILURE", "retrieve": "RAG_FAILURE",
                "generate": "MODEL_FAILURE", "trust": "SYSTEM_FAILURE", "tool": "TOOL_FAILURE"}
_BASE = {"POLICY_FAILURE": 2, "SYSTEM_FAILURE": 2, "MODEL_FAILURE": 1, "RAG_FAILURE": 1, "TOOL_FAILURE": 1,
         "MEMORY_FAILURE": 1, "DATA_FAILURE": 1, "INPUT_FAILURE": 0, "USER_ERROR": 0, "UNKNOWN": 0}
_SEV = ["low", "medium", "high", "critical"]
RECOMMENDATION = {
    "MODEL_FAILURE": "Periksa kesehatan provider/model, timeout, dan validasi output; pertimbangkan eksperimen prompt/model.",
    "RAG_FAILURE": "Periksa cakupan korpus, versi dokumen, dan konfigurasi retrieval; ajukan eksperimen retrieval.",
    "MEMORY_FAILURE": "Periksa penyimpanan memory (izin file, ruang disk, konsistensi).",
    "TOOL_FAILURE": "Periksa handler tool, skema input/output, dan circuit breaker.",
    "POLICY_FAILURE": "Tinjau aturan kebijakan; kegagalan policy bersifat fail-closed dan perlu perhatian manusia.",
    "SYSTEM_FAILURE": "Periksa komponen internal (language/trust) dan log terkait request_id.",
    "INPUT_FAILURE": "Periksa validasi input dan pesan penolakan; pastikan tidak terlalu ketat.",
    "DATA_FAILURE": "Periksa kualitas/versi data sumber.",
    "USER_ERROR": "Perbaiki UX/petunjuk pengguna.",
    "UNKNOWN": "Kumpulkan lebih banyak konteks sebelum menyimpulkan.",
}


@dataclass
class Failure:
    request_id: str
    stage: str
    category: str
    error_type: str
    source: str  # event | feedback
    timestamp: str = ""


@dataclass
class Pattern:
    category: str
    stage: str
    count: int
    severity: str
    recommendation: str
    example_request_ids: list[str] = field(default_factory=list)


@dataclass
class FailureReport:
    failures: list[Failure]
    root_causes: dict[str, Failure]
    patterns: list[Pattern]


def _stage_of(component: str) -> str:
    return component if component in STAGE_TO_CAT else ("tool" if component.startswith("tool") else component)


def extract_failures(events: list[dict[str, Any]], feedback: list[dict[str, Any]] | None = None) -> list[Failure]:
    out: list[Failure] = []
    for e in events:
        if e.get("component") == "orchestrator" or e.get("status") in (None, "ok"):
            continue
        stage = _stage_of(str(e.get("component", "")))
        et = str((e.get("metadata") or {}).get("error_type", e.get("status")))
        out.append(Failure(str(e.get("request_id", "-")), stage, STAGE_TO_CAT.get(stage, "UNKNOWN"), et,
                           "event", str(e.get("timestamp", ""))))
    for f in feedback or []:
        if f.get("polarity") == "negative":
            out.append(Failure(str(f.get("request_id", "-")), "feedback", f.get("failure_class") or "UNKNOWN",
                               str(f.get("type")), "feedback", str(f.get("created_at", ""))))
    return out


def _severity(category: str, count: int) -> str:
    score = _BASE.get(category, 0) + (2 if count >= 25 else 1 if count >= 10 else 0)
    return _SEV[min(score, 3)]


def analyze(events: list[dict[str, Any]], feedback: list[dict[str, Any]] | None = None) -> FailureReport:
    fails = extract_failures(events, feedback)
    by_req: dict[str, list[Failure]] = defaultdict(list)
    for f in fails:
        by_req[f.request_id].append(f)
    order = {s: i for i, s in enumerate(PIPELINE_ORDER)}
    roots = {rid: min(fs, key=lambda x: order.get(x.stage, 99)) for rid, fs in by_req.items()}
    # pola dihitung dari root cause (bukan gejala turunan) agar tidak menggandakan hitungan
    cnt = Counter((r.category, r.stage) for r in roots.values())
    patterns = []
    for (cat, stage), n in cnt.items():
        ex = [rid for rid, r in roots.items() if (r.category, r.stage) == (cat, stage)][:5]
        patterns.append(Pattern(cat, stage, n, _severity(cat, n), RECOMMENDATION.get(cat, ""), ex))
    patterns.sort(key=lambda p: (_SEV.index(p.severity), p.count), reverse=True)
    return FailureReport(fails, roots, patterns)
