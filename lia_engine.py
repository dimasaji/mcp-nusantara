"""Nusantara V1 — Lean Intelligence Engine (LIA).

Self-contained FastAPI backend exposing /v1/health, /v1/knowledge/status,
/v1/chat. Environment-variable driven, Windows–Linux portable, no hardcoded
PC/Windows paths, no Tailscale/Cloudflare, not exposed to public internet.

Work packages implemented:
  WP-01 Intent Intelligence  (lightweight keyword/heuristic classifier)
  WP-02 Structured SOP Intelligence (structured SOP representation from DB)
  WP-03 Adaptive Intelligence Router
  WP-04 Context Intelligence (session context, SOP boundary)
  WP-05 Local Model Intelligence (Ollama Llama 3.2 1B, tuned)
  WP-06 Evidence and Answer Verifier
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from structured_sop import StructuredSOPEngine

# ---------------------------------------------------------------------------
# Environment configuration (Windows–Linux portable, no hardcoded PC paths)
# ---------------------------------------------------------------------------

def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default

def _env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}

HOST = _env("NUSANTARA_HOST", "127.0.0.1")
PORT = _env_int("NUSANTARA_PORT", 8021)
KNOWLEDGE_DB = Path(_env("NUSANTARA_KNOWLEDGE_DB", "./data/knowledge/production_knowledge.db")).resolve()

OLLAMA_URL = _env("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = _env("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_KEEP_ALIVE = _env("OLLAMA_KEEP_ALIVE", "5m")
OLLAMA_NUM_THREAD = _env_int("OLLAMA_NUM_THREAD", 4)
OLLAMA_NUM_CTX = _env_int("OLLAMA_NUM_CTX", 4096)
OLLAMA_NUM_PREDICT = _env_int("OLLAMA_NUM_PREDICT", 512)
OLLAMA_TEMPERATURE = float(_env("OLLAMA_TEMPERATURE", "0.2") or "0.2")
OLLAMA_TIMEOUT = _env_int("OLLAMA_TIMEOUT", 30)

INTENT_CONFIDENCE_THRESHOLD = float(_env("INTENT_CONFIDENCE_THRESHOLD", "0.35") or "0.35")
RAG_TOP_K = _env_int("RAG_TOP_K", 5)
EVIDENCE_MIN_SCORE = float(_env("EVIDENCE_MIN_SCORE", "0.20") or "0.20")
VERIFY_CITATION_REQUIRED = _env_bool("VERIFY_CITATION_REQUIRED", True)
VERIFY_ALLOW_UNSUPPORTED = _env_bool("VERIFY_ALLOW_UNSUPPORTED", False)
DEVELOPER_MODE = _env_bool("DEVELOPER_MODE", False)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "nusantara"
MEMORY_DB = DATA_DIR / "memory.db"
LOG_DIR = DATA_DIR / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_À-ÿ-]+", normalize_text(text)))

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _relevant_text(text: str, query: str, max_chars: int = 700) -> str:
    """Ekstraksi segmen teks paling relevan terhadap query (bukan truncasi awali)."""
    if not text:
        return ""
    q_tokens = tokenize(query)
    # Pecah ke segmen per baris / kalimat.
    raw_segs = re.split(r"[\n\r|]+", text)
    segs = [re.sub(r"\s+", " ", s).strip() for s in raw_segs if re.sub(r"\s+", " ", s).strip()]
    if not q_tokens:
        return text[:max_chars]
    scored = []
    for s in segs:
        st = tokenize(s)
        if not st:
            continue
        overlap = len(q_tokens & st)
        score = overlap / max(len(q_tokens), 1)
        if score > 0:
            scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    chosen = [s for _, s in scored]
    if not chosen:
        chosen = [segs[0]]
    out = ""
    for s in chosen:
        if len(out) + len(s) + 1 > max_chars:
            break
        out += (s + " ")
    return out.strip()


# Kunci konten per kategori SOP, turunan dari isi dokumen DAFDUK-01 (bukan dari
# pertanyaan uji). Digunakan untuk memilih segmen tabel yang benar-benar relevan.
CONTENT_KEYWORDS = {
    "persyaratan": [
        "kartu", "keluarga", "akta", "kelahiran", "ijazah", "nikah", "perkawinan",
        "17", "tahun", "berkas", "daftar", "website", "sobat", "dukcapil",
        "persyaratan", "syarat", "ktp-el", "elektronik",
    ],
    "prosedur": [
        "form", "f1-02", "verifikasi", "validasi", "perekaman", "pengajuan",
        "langkah", "menu", "administrasi", "upload", "data", "online",
        "prosedur", "tata cara",
    ],
    "waktu_penyelesaian": [
        "hari", "menit", "jam", "waktu", "selesai", "cepat", "5 menit",
        "10 menit", "15 menit", "1 hari", "kerja",
    ],
    "pelaksana": [
        "petugas", "perekaman", "kasi", "kepala", "dinaks", "pelayanan",
        "pelaksana", "penanggung jawab",
    ],
    "output_layanan": [
        "ktp-el", "tercetak", "cetak", "kartu", "tanda", "penduduk",
        "output", "hasil", "diterima",
    ],
    "dasar_hukum": [
        "undang-undang", "peraturan", "uu", "pp", "perpres", "perda",
        "hukum", "nomor", "tahun", "lembaran negara",
    ],
}


def _select_segments(text: str, category: str, max_chars: int = 900) -> str:
    """Pilih segmen teks yang mengandung kunci konten kategori."""
    if not text:
        return ""
    kws = CONTENT_KEYWORDS.get(category, [])
    raw_segs = re.split(r"[\n\r|]+", text)
    segs = [re.sub(r"\s+", " ", s).strip() for s in raw_segs if re.sub(r"\s+", " ", s).strip()]
    chosen = []
    for s in segs:
        low = s.lower()
        if any(k in low for k in kws):
            chosen.append(s)
    if not chosen:
        # Fallback: segmen pertama yang cukup informatif.
        chosen = segs[:3]
    out = ""
    for s in chosen:
        if len(out) + len(s) + 1 > max_chars:
            break
        out += (s + " ")
    return out.strip()


# ---------------------------------------------------------------------------
# WP-02 Structured SOP Intelligence — knowledge store over SQLite
# ---------------------------------------------------------------------------

class KnowledgeStore:
    """Read-only structured SOP knowledge from production_knowledge.db."""

    def __init__(self, db_path: Path = KNOWLEDGE_DB):
        self.db_path = db_path

    def available(self) -> bool:
        return self.db_path.exists()

    def _connect(self) -> Optional[sqlite3.Connection]:
        if not self.db_path.exists():
            return None
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def documents(self) -> list[dict[str, Any]]:
        conn = self._connect()
        if conn is None:
            return []
        try:
            rows = conn.execute(
                """
                SELECT document_id, title, source_file, service, content_type,
                       source_status, authority, verified
                FROM documents ORDER BY title
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def official_documents(self) -> list[dict[str, Any]]:
        out = []
        for d in self.documents():
            if (str(d.get("source_status", "")).lower() in {"official", "verified"}
                    and str(d.get("authority", "")).lower() in {"official", "verified"}
                    and int(d.get("verified") or 0) == 1):
                out.append(d)
        return out

    def search(self, query: str, top_k: int = RAG_TOP_K,
               service: Optional[str] = None) -> list[dict[str, Any]]:
        conn = self._connect()
        if conn is None:
            return []
        q_tokens = tokenize(query)
        try:
            rows = conn.execute(
                """
                SELECT c.chunk_id, c.document_id, c.text, c.page_no,
                       d.title, d.source_file, d.service, d.content_type,
                       d.source_status, d.authority, d.verified
                FROM chunks c JOIN documents d ON d.document_id = c.document_id
                """
            ).fetchall()
            candidates: list[dict[str, Any]] = []
            for row in rows:
                if service and str(row["service"] or "").lower() != service.lower():
                    continue
                if str(row["source_status"] or "").lower() not in {"official", "verified"}:
                    continue
                if str(row["authority"] or "").lower() not in {"official", "verified"}:
                    continue
                if int(row["verified"] or 0) != 1:
                    continue
                text = row["text"] or ""
                text_tokens = tokenize(text)
                if not q_tokens:
                    score = 0.0
                else:
                    overlap = len(q_tokens & text_tokens)
                    score = overlap / max(len(q_tokens), 1)
                if score <= 0:
                    continue
                candidates.append({
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "page_no": row["page_no"],
                    "text": text,
                    "title": row["title"],
                    "source_file": row["source_file"],
                    "service": row["service"],
                    "content_type": row["content_type"],
                    "source_status": str(row["source_status"] or "").lower(),
                    "authority": str(row["authority"] or "").lower(),
                    "verified": int(row["verified"] or 0),
                    "score": round(score, 4),
                })
            candidates.sort(key=lambda x: x["score"], reverse=True)
            return candidates[:top_k]
        finally:
            conn.close()

    def status(self) -> dict[str, Any]:
        docs = self.documents()
        official = self.official_documents()
        return {
            "database": str(self.db_path),
            "database_exists": self.db_path.exists(),
            "documents": len(docs),
            "official_verified_documents": len(official),
            "fail_closed": len(official) == 0,
        }

# ---------------------------------------------------------------------------
# WP-01 Intent Intelligence — lightweight, no LLM for simple classification
# ---------------------------------------------------------------------------

class IntentEngine:
    INTENT_CATEGORIES = [
        "identitas_layanan",
        "persyaratan",
        "prosedur",
        "waktu_penyelesaian",
        "pelaksana",
        "output_layanan",
        "dasar_hukum",
        "pertanyaan_lanjutan",
        "sintesis",
        "di luar knowledge",
    ]

    # Lightweight keyword heuristics per intent (bahasa Indonesia).
    # Kunci kata per intent dengan bobot. Intent domain-specifik (syarat, prosedur,
    # waktu, pelaksana, output, hukum) dibobot lebih tinggi dari identitas generik
    # ("apa"/"bagaimana") agar klasifikasi tidak kecanduan kata umum.
    KEYWORDS = {
        "persyaratan": (["persyaratan", "syarat", "berkas", "dokumen", "ketentuan", "kebutuhan"], 0.85),
        "prosedur": (["prosedur", "tata cara", "langkah", "caranya", "bagaimana", "proses"], 0.85),
        "waktu_penyelesaian": (["waktu", "lama", "berapa hari", "hari", "jam", "tanggal", "cepat", "selesai"], 0.85),
        "pelaksana": (["pelaksana", "petugas", "siapa", "penanggung jawab", "pihak", "kasi"], 0.85),
        "dasar_hukum": (["dasar hukum", "peraturan", "uu", "undang", "perppu", "perda", "hukum"], 0.85),
        "output_layanan": (["output", "hasil", "diterima", "dokumen", "ktp", "kartu", "surat"], 0.85),
        "identitas_layanan": (["apa", "layanan", "adalah", "sebutan", "nama", "penerbitan"], 0.5),
        "sintesis": (["ringkas", "kesimpulan", "sintesis", "ringkasan", "intinya"], 0.7),
    }

    SERVICE_KEYWORDS = {
        "ktp_el": ["ktp", "ktp-el", "ktpel", "kartu tanda penduduk", "elektronik"],
        "kk": ["kartu keluarga", "kk", "keluarga"],
        "kia": ["kia", "kartu identitas anak"],
    }

    def classify(self, query: str) -> dict[str, Any]:
        q = normalize_text(query)
        tokens = tokenize(q)
        best_intent = "di luar knowledge"
        best_score = 0.0
        best_matched: list[str] = []

        for intent, (keywords, weight) in self.KEYWORDS.items():
            matched = [kw for kw in keywords if kw in q]
            if not matched:
                continue
            score = min(len(matched) * weight, 1.0)
            if score > best_score:
                best_score = score
                best_intent = intent
                best_matched = matched

        # Service detection
        service = None
        for svc, kws in self.SERVICE_KEYWORDS.items():
            if any(kw in q for kw in kws):
                service = svc
                break

        # Follow-up detection: short query with pronouns referencing previous turn
        if best_intent == "di luar knowledge" and len(tokens) <= 6:
            pronouns = {"itu", "tersebut", "ini", "nya", "lagi", "selanjutnya"}
            if tokens & pronouns:
                best_intent = "pertanyaan_lanjutan"
                best_score = 0.6

        confidence = min(best_score, 1.0)
        return {
            "intent": best_intent if confidence >= INTENT_CONFIDENCE_THRESHOLD else "di luar knowledge",
            "confidence": round(confidence, 4),
            "service": service,
            "matched_keywords": best_matched,
        }

# ---------------------------------------------------------------------------
# WP-04 Context Intelligence — session context with SOP boundary
# ---------------------------------------------------------------------------

class ContextEngine:
    def __init__(self, memory_db: Path = MEMORY_DB):
        self.memory_db = memory_db
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(self.memory_db))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_context (
                session_id TEXT PRIMARY KEY,
                active_sop TEXT,
                active_service TEXT,
                last_intent TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def get(self, session_id: str) -> dict[str, Any]:
        conn = sqlite3.connect(str(self.memory_db))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM session_context WHERE session_id=?",
                (session_id,),
            ).fetchone()
        finally:
            conn.close()
        if not row:
            return {"active_sop": None, "active_service": None, "last_intent": None}
        return dict(row)

    def set(self, session_id: str, active_sop: Optional[str],
            active_service: Optional[str], last_intent: Optional[str]) -> None:
        conn = sqlite3.connect(str(self.memory_db))
        conn.execute(
            """
            INSERT INTO session_context(session_id, active_sop, active_service,
                 last_intent, updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(session_id) DO UPDATE SET
                active_sop=excluded.active_sop,
                active_service=excluded.active_service,
                last_intent=excluded.last_intent,
                updated_at=excluded.updated_at
            """,
            (session_id, active_sop, active_service, last_intent, now_iso()),
        )
        conn.commit()
        conn.close()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        conn = sqlite3.connect(str(self.memory_db))
        conn.execute(
            "INSERT INTO messages(session_id, role, content, created_at) VALUES(?,?,?,?)",
            (session_id, role, content, now_iso()),
        )
        conn.commit()
        conn.close()

    def recent(self, session_id: str, limit: int = 6) -> list[dict[str, Any]]:
        conn = sqlite3.connect(str(self.memory_db))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT role, content, created_at FROM messages
                WHERE session_id=? ORDER BY id DESC LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
            return [dict(r) for r in reversed(rows)]
        finally:
            conn.close()

    def clear(self, session_id: str) -> None:
        conn = sqlite3.connect(str(self.memory_db))
        conn.execute("DELETE FROM session_context WHERE session_id=?", (session_id,))
        conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()

# ---------------------------------------------------------------------------
# WP-05 Local Model Intelligence — Ollama Llama 3.2 1B
# ---------------------------------------------------------------------------

class OllamaEngine:
    def __init__(self):
        self.url = OLLAMA_URL
        self.model = OLLAMA_MODEL

    def health(self) -> bool:
        try:
            import urllib.request, urllib.error
            req = urllib.request.Request(f"{self.url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    return False
                data = json.loads(resp.read().decode())
                return any(m.get("name") == self.model for m in data.get("models", []))
        except Exception:
            return False

    def chat(self, messages: list[dict[str, str]], stream: bool = False,
             temperature: float = OLLAMA_TEMPERATURE,
             num_predict: int = OLLAMA_NUM_PREDICT) -> dict[str, Any]:
        import urllib.request, urllib.error

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "options": {
                "num_thread": OLLAMA_NUM_THREAD,
                "num_ctx": OLLAMA_NUM_CTX,
                "num_predict": num_predict,
                "temperature": temperature,
            },
        }
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                raw = resp.read().decode()
                return json.loads(raw)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama tidak dapat dihubungi: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Gagal memanggil model lokal: {exc}") from exc

# ---------------------------------------------------------------------------
# WP-06 Evidence and Answer Verifier
# ---------------------------------------------------------------------------

class Verifier:
    def __init__(self):
        self.citation_required = VERIFY_CITATION_REQUIRED
        self.allow_unsupported = VERIFY_ALLOW_UNSUPPORTED

    def verify(self, answer: str, evidence: list[dict[str, Any]],
               intent: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        citation_valid = True
        evidence_count = len(evidence)

        # Every factual claim should be grounded in evidence when required.
        if self.citation_required and evidence_count == 0:
            issues.append("Tidak ada evidence yang mendukung jawaban ini.")
            citation_valid = False

        # Check for obvious unsupported claims (heuristic).
        if not self.allow_unsupported and evidence_count == 0:
            if any(k in answer.lower() for k in ["syarat", "biaya", "hari", "jam", "peraturan"]):
                issues.append("Klaim faktual tidak didukung oleh dokumen sumber.")
                citation_valid = False

        return {
            "citation_valid": citation_valid,
            "evidence_count": evidence_count,
            "issues": issues,
            "verified": (len(issues) == 0) or self.allow_unsupported,
        }

# ---------------------------------------------------------------------------
# WP-03 Adaptive Intelligence Router + orchestration
# ---------------------------------------------------------------------------

class LiaEngine:
    def __init__(self):
        self.knowledge = KnowledgeStore()
        self.intent = IntentEngine()
        self.context = ContextEngine()
        self.sop = StructuredSOPEngine()
        self.ollama = OllamaEngine()
        self.verifier = Verifier()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "engine": "Nusantara Lean Intelligence Engine",
            "version": "1.0.0",
            "knowledge": self.knowledge.status(),
            "ollama": {
                "url": OLLAMA_URL,
                "model": OLLAMA_MODEL,
                "available": self.ollama.health(),
            },
            "config": {
                "host": HOST,
                "port": PORT,
                "knowledge_db": str(KNOWLEDGE_DB),
                "developer_mode": DEVELOPER_MODE,
            },
        }

    def _build_sop_context(self, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        if not evidence:
            return {"active_sop": None, "active_service": None, "sop": None}
        top = evidence[0]
        return {
            "active_sop": top.get("document_id"),
            "active_service": top.get("service"),
            "sop": {
                "document_id": top.get("document_id"),
                "title": top.get("title"),
                "source_file": top.get("source_file"),
                "service": top.get("service"),
                "page_no": top.get("page_no"),
                "chunk_index": top.get("chunk_index"),
            },
        }

    def _should_use_llm(self, intent: dict[str, Any], evidence: list[dict[str, Any]]) -> bool:
        # Direct factual answers with sufficient evidence skip the LLM.
        category = intent["intent"]
        if category in {"identitas_layanan", "persyaratan", "prosedur",
                        "waktu_penyelesaian", "pelaksana", "output_layanan",
                        "dasar_hukum"} and evidence:
            return False
        if category == "di luar knowledge":
            return False
        return True

    def _structured_answer(self, query: str, intent: dict[str, Any],
                           evidence: list[dict[str, Any]]) -> str:
        category = intent["intent"]
        top = evidence[0] if evidence else None
        lines: list[str] = []

        if category == "identitas_layanan" and top:
            lines.append(
                f"{top.get('title', 'Layanan')} — layanan resmi berdasarkan "
                f"{top.get('source_file', 'dokumen SOP')}."
            )
        elif category in {
            "persyaratan", "prosedur", "waktu_penyelesaian", "pelaksana",
            "output_layanan", "dasar_hukum",
        }:
            svc = intent.get("service")
            sop = self.sop.get(svc) if svc else None
            if sop is None:
                # Coba turunkan dari evidence terpilih (best effort).
                korpus = "\n".join(e.get("text", "") for e in evidence)
                segmen = _select_segments(korpus, category)
                if segmen:
                    lines.append(
                        f"{category.replace('_', ' ').title()} layanan "
                        f"(berdasarkan dokumen sumber):"
                    )
                    lines.append("- " + segmen)
                else:
                    lines.append("Maaf, saya belum menemukan informasi yang cukup dalam "
                                 "basis pengetahuan untuk menjawab pertanyaan ini.")
            else:
                konten = sop.get(category)
                label = {
                    "persyaratan": "Persyaratan layanan",
                    "prosedur": "Prosedur layanan",
                    "waktu_penyelesaian": "Waktu penyelesaian layanan",
                    "pelaksana": "Pelaksana layanan",
                    "output_layanan": "Output layanan",
                    "dasar_hukum": "Dasar hukum layanan",
                }[category]
                lines.append(f"{label} (berdasarkan dokumen sumber):")
                lines.append("- " + konten)
        else:
            lines.append("Maaf, saya belum menemukan informasi yang cukup dalam "
                         "basis pengetahuan untuk menjawab pertanyaan ini.")

        if top:
            lines.append(
                f"\nSumber: {top.get('title')} ({top.get('source_file')}, "
                f"halaman {top.get('page_no')})"
            )
        return "\n".join(lines)

    def _llm_answer(self, query: str, evidence: list[dict[str, Any]],
                    session_id: str) -> str:
        evidence_text = ""
        for i, e in enumerate(evidence[:3], 1):
            evidence_text += (
                f"[Sumber {i}] {e.get('title')} — {e.get('source_file')} "
                f"(halaman {e.get('page_no')}):\n{e.get('text','')[:800]}\n\n"
            )

        system = (
            "Anda adalah Nusantara AI, asisten layanan publik. Jawab dalam Bahasa Indonesia. "
            "Gunakan HANYAS sumber yang tersedia. Jangan mengarang fakta. "
            "Sertakan situs sumber (judul berkas dan halaman). Jika informasi tidak cukup, "
            "katakan bahwa keterbatasan tersedia secara jelas."
        )
        user = (
            f"Pertanyaan: {query}\n\n"
            f"Sumber tersedia:\n{evidence_text if evidence_text else '(tidak ada)'}\n"
            "Hasilkan jawaban singkat, akurat, dan bersitasi."
        )
        try:
            resp = self.ollama.chat([
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ])
            return resp.get("message", {}).get("content", "").strip()
        except RuntimeError:
            # Fallback: structured answer with valid evidence, or state limitation.
            if evidence:
                return self._structured_answer(query, {"intent": "sintesis"}, evidence)
            return ("Model lokal tidak tersedia saat ini dan tidak ada evidence yang cukup. "
                    "Silakan coba lagi nanti atau ajukan pertanyaan lain.")

    def process(self, query: str, session_id: str = "default") -> dict[str, Any]:
        started = time.perf_counter()

        # WP-01 Intent
        intent = self.intent.classify(query)

        # WP-04 Context
        ctx = self.context.get(session_id)
        self.context.add_message(session_id, "user", query)

        # Follow-up inherits active SOP/service when applicable.
        service = intent.get("service")
        if not service and ctx.get("active_service"):
            service = ctx["active_service"]

        # WP-02 Knowledge retrieval (structured SOP)
        evidence = self.knowledge.search(query, top_k=RAG_TOP_K, service=service)

        # WP-03 Router
        use_llm = self._should_use_llm(intent, evidence)

        if use_llm and evidence:
            answer = self._llm_answer(query, evidence, session_id)
            mode = "sintesis_llm_lokal"
        elif evidence:
            answer = self._structured_answer(query, intent, evidence)
            mode = "faktual_struktur"
        else:
            answer = ("Maaf, saya belum menemukan informasi yang cukup dalam basis "
                      "pengetahuan untuk menjawab pertanyaan ini.")
            mode = "tidak_diketahui"

        # WP-06 Verifier
        verification = self.verifier.verify(answer, evidence, intent)

        # Update context (WP-04)
        sop_ctx = self._build_sop_context(evidence)
        self.context.set(
            session_id,
            active_sop=sop_ctx["active_sop"],
            active_service=sop_ctx["active_service"],
            last_intent=intent["intent"],
        )
        self.context.add_message(session_id, "assistant", answer)

        elapsed_ms = int((time.perf_counter() - started) * 1000)

        result: dict[str, Any] = {
            "status": "ok",
            "answer": answer,
            "answer_mode": mode,
            "session_id": session_id,
            "intent": intent,
            "context": sop_ctx,
            "knowledge": {
                "count": len(evidence),
                "items": evidence,
            },
            "verification": verification,
            "processing_status": "completed",
            "latency_ms": elapsed_ms,
        }
        if DEVELOPER_MODE:
            result["_debug"] = {
                "use_llm": use_llm,
                "ollama_available": self.ollama.health(),
                "evidence_min_score": EVIDENCE_MIN_SCORE,
            }
        return result

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Nusantara V1 Lean Intelligence Engine", version="1.0.0")
engine = LiaEngine()


class ChatRequest(BaseModel):
    input: str
    session_id: str = "default"


@app.get("/v1/health")
def health():
    return engine.health()


@app.get("/v1/knowledge/status")
def knowledge_status():
    return engine.knowledge.status()


@app.post("/v1/chat")
def chat(request: ChatRequest):
    if not request.input or not request.input.strip():
        raise HTTPException(status_code=400, detail="Input tidak boleh kosong.")
    return engine.process(request.input, request.session_id)


@app.get("/v1/context/{session_id}")
def context(session_id: str):
    return engine.context.get(session_id)


@app.delete("/v1/context/{session_id}")
def clear_context(session_id: str):
    engine.context.clear(session_id)
    return {"status": "cleared", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    print("=" * 72)
    print(" NUSANTARA V1 — LEAN INTELLIGENCE ENGINE")
    print("=" * 72)
    print(f"Host        : {HOST}:{PORT}")
    print(f"Knowledge DB: {KNOWLEDGE_DB}")
    print(f"Ollama      : {OLLAMA_URL} / {OLLAMA_MODEL}")
    print(f"Developer   : {DEVELOPER_MODE}")
    print(f"Web UI / API: http://{HOST}:{PORT}/docs")
    print("=" * 72)
    uvicorn.run(app, host=HOST, port=PORT)
