"""Phase 7 - RAG: versi dokumen, metadata wajib, kontrol akses, deteksi konflik, sitasi.

Stdlib-only. Retriever V1 (app/knowledge) tetap ada; layer ini menambah kontrak metadata,
versi, dan konflik di atasnya dan dapat dipakai lewat `as_retriever` di orchestrator V2.
"""
from __future__ import annotations

import math
import re
import threading
from collections import Counter
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

ACCESS_RANK = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
_TOKEN = re.compile(r"\w+", re.U)
_NUM = re.compile(r"\d+(?:[.,]\d+)?")
_STOP = {"yang", "dan", "di", "ke", "dari", "untuk", "the", "a", "of", "to", "is", "itu", "ini",
         "dengan", "adalah", "atau", "in", "and"}


def tokenize(text: str) -> list[str]:
    return [w for w in _TOKEN.findall(text.lower()) if w not in _STOP]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class DocMeta:
    document_id: str
    version: int
    source: str
    created_at: str
    updated_at: str
    authority: int
    topic: str
    access_level: str
    superseded: bool = False


@dataclass
class Hit:
    meta: DocMeta
    chunk_index: int
    text: str
    score: float
    conflict: bool = False

    @property
    def citation(self) -> str:
        return f"{self.meta.document_id}@v{self.meta.version}#{self.chunk_index}"


@dataclass
class Conflict:
    topic: str
    documents: list[tuple[str, int]]
    reason: str
    authority_tie: bool


@dataclass
class RetrievalResult:
    hits: list[Hit] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)


def chunk_text(text: str, size: int = 120, overlap: int = 20) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(1, size - overlap)
    out, i = [], 0
    while i < len(words):
        out.append(" ".join(words[i:i + size]))
        if i + size >= len(words):
            break
        i += step
    return out


def _numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in _NUM.findall(text)}


def _content_tokens(text: str) -> set[str]:
    return {t for t in tokenize(text) if not t.isdigit()}


def detect_conflicts(hits: list[Hit]) -> list[Conflict]:
    """Dua dokumen BERBEDA, topik sama, teks mirip tetapi angka berbeda -> konflik (tidak dipilih diam-diam)."""
    found: dict[tuple, Conflict] = {}
    for i, a in enumerate(hits):
        for b in hits[i + 1:]:
            if a.meta.document_id == b.meta.document_id or a.meta.topic != b.meta.topic:
                continue
            na, nb = _numbers(a.text), _numbers(b.text)
            if not na or not nb or na == nb:
                continue
            ta, tb = _content_tokens(a.text), _content_tokens(b.text)
            if not ta or not tb or len(ta & tb) / len(ta | tb) < 0.2:
                continue
            key = (a.meta.topic, frozenset({a.meta.document_id, b.meta.document_id}))
            if key not in found:
                found[key] = Conflict(a.meta.topic,
                                      [(a.meta.document_id, a.meta.version), (b.meta.document_id, b.meta.version)],
                                      f"nilai berbeda: {sorted(na)} vs {sorted(nb)}",
                                      a.meta.authority == b.meta.authority)
            a.conflict = b.conflict = True
    return list(found.values())


class VersionedKnowledgeStore:
    def __init__(self, chunk_words: int = 120, overlap: int = 20):
        self._docs: dict[str, list[tuple[DocMeta, list[str]]]] = {}
        self._lock = threading.Lock()
        self.chunk_words, self.overlap = chunk_words, overlap

    def add_document(self, document_id: str, text: str, *, source: str, topic: str,
                     authority: int = 50, access_level: str = "internal") -> DocMeta:
        if not document_id.strip() or not text.strip() or not source.strip() or not topic.strip():
            raise ValueError("document_id, text, source, topic wajib diisi")
        if access_level not in ACCESS_RANK:
            raise ValueError(f"access_level harus salah satu dari {sorted(ACCESS_RANK)}")
        if not 0 <= authority <= 100:
            raise ValueError("authority harus 0..100")
        with self._lock:
            versions = self._docs.setdefault(document_id, [])
            if versions:
                versions[-1] = (replace(versions[-1][0], superseded=True), versions[-1][1])
            created = versions[0][0].created_at if versions else _now()
            meta = DocMeta(document_id, len(versions) + 1, source, created, _now(), authority,
                           topic, access_level)
            versions.append((meta, chunk_text(text, self.chunk_words, self.overlap)))
            return meta

    def versions(self, document_id: str) -> list[DocMeta]:
        with self._lock:
            return [m for m, _ in self._docs.get(document_id, [])]

    def retrieve(self, query: str, *, max_access: str = "internal", top_k: int = 5,
                 include_superseded: bool = False) -> RetrievalResult:
        if max_access not in ACCESS_RANK:
            raise ValueError("max_access tidak valid")
        limit = ACCESS_RANK[max_access]
        q = set(tokenize(query))
        with self._lock:
            cands = [(m, i, c) for vs in self._docs.values() for (m, chunks) in vs
                     if ACCESS_RANK[m.access_level] <= limit and (include_superseded or not m.superseded)
                     for i, c in enumerate(chunks)]
        if not q or not cands:
            return RetrievalResult()
        toks = [Counter(tokenize(c)) for _, _, c in cands]
        df = Counter(t for tf in toks for t in tf)
        n = len(cands)
        idf = {t: math.log(1 + n / df[t]) for t in q if df[t]}
        denom = sum(idf.values()) or 1.0
        scored: list[Hit] = []
        for (m, i, c), tf in zip(cands, toks):
            s = sum(idf[t] * (1 + math.log(tf[t])) for t in idf if t in tf) / denom
            if s > 0:  # rerank: otoritas sumber menaikkan skor secara moderat
                scored.append(Hit(m, i, c, round(s * (1 + m.authority / 200), 4)))
        scored.sort(key=lambda h: h.score, reverse=True)
        hits = scored[:top_k]
        return RetrievalResult(hits, detect_conflicts(hits))


def grounded_context(result: RetrievalResult) -> str:
    if not result.hits:
        return "Tidak ada evidence yang ditemukan."
    lines = [f"[{i}] ({h.citation}; sumber: {h.meta.source}) {h.text}" for i, h in enumerate(result.hits, 1)]
    for c in result.conflicts:
        lines.append(f"PERINGATAN KONFLIK topik '{c.topic}': {c.reason} antara "
                     f"{', '.join(f'{d}@v{v}' for d, v in c.documents)}"
                     + (" (otoritas sama)" if c.authority_tie else ""))
    return "\n".join(lines)


def as_retriever(store: VersionedKnowledgeStore, *, max_access: str = "internal", top_k: int = 5):
    """Adapter ke V2Orchestrator(retrieve=...). Menyertakan sitasi & flag konflik."""
    def retrieve(text: str) -> list[dict[str, Any]]:
        r = store.retrieve(text, max_access=max_access, top_k=top_k)
        return [{"document_id": h.meta.document_id, "title": h.meta.document_id, "chunk": h.text,
                 "score": h.score, "source": h.meta.source, "citation": h.citation,
                 "version": h.meta.version, "conflict": h.conflict} for h in r.hits]
    return retrieve
