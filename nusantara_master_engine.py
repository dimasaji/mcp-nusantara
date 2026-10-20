from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

import urllib.request
import urllib.parse
import urllib.error

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


# ================================================================
# NUSANTARA MASTER ENGINE
# ================================================================
#
# Master orchestrator untuk:
#
# 01 Official Production Knowledge
# 02 Intent Engine
# 03 Entity Engine
# 04 Context Engine
# 05 Problem Engine
# 06 Reasoning Core
# 07 Workflow Engine
# 08 Policy Engine
# 09 Trust Engine
# 10 Memory Engine
# 11 Tool Engine
# 12 MCP Engine
# 13 Human Handoff
# 14 Evaluation Engine
# 15 Observability
# 16 Local Web UI
#
# Filosofi:
# - local first
# - CPU friendly
# - Ollama
# - fail closed untuk knowledge resmi
# - tidak mengarang sumber resmi
# - tidak mengubah Developer Core lama
# ================================================================


ROOT = Path(__file__).resolve().parent

DATA_DIR = ROOT / "data" / "nusantara"
OFFICIAL_DIR = DATA_DIR / "official_knowledge"
MEMORY_DB = DATA_DIR / "memory.db"
ENGINE_DB = DATA_DIR / "engine.db"
LOG_DIR = DATA_DIR / "logs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OFFICIAL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "llama3.2:1b"

DEVELOPER_CORE_URL = "http://127.0.0.1:8010"


# ================================================================
# UTILITIES
# ================================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> set[str]:
    return set(
        re.findall(
            r"[a-zA-Z0-9_À-ÿ-]+",
            normalize_text(text),
        )
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def safe_json(data: Any) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


# ================================================================
# OBSERVABILITY ENGINE
# ================================================================

class ObservabilityEngine:

    def __init__(self):
        self.events_db = ENGINE_DB
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.events_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                event_type TEXT,
                payload TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def event(
        self,
        event_type: str,
        payload: dict[str, Any],
    ):
        conn = sqlite3.connect(self.events_db)
        conn.execute(
            """
            INSERT INTO events
            (event_id, event_type, payload, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                event_type,
                safe_json(payload),
                now_iso(),
            ),
        )
        conn.commit()
        conn.close()

    def recent(self, limit: int = 50):
        conn = sqlite3.connect(self.events_db)
        rows = conn.execute(
            """
            SELECT event_id, event_type, payload, created_at
            FROM events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()

        return [
            {
                "event_id": r[0],
                "event_type": r[1],
                "payload": json.loads(r[2]),
                "created_at": r[3],
            }
            for r in rows
        ]



# ================================================================
# DEVELOPER CORE CLIENT
# ================================================================

class DeveloperCoreClient:

    """
    Adapter Master Engine -> Developer Core 8010.

    Developer Core tetap menjadi specialist engine:
      - Graph RAG
      - Source RAG
      - Graphify
      - source search
      - code analysis

    Master Engine hanya melakukan orchestration.
    """

    def __init__(
        self,
        base_url: str = DEVELOPER_CORE_URL,
    ):
        self.base_url = base_url.rstrip("/")

    def _get(
        self,
        path: str,
        timeout: int = 20,
    ) -> dict:

        url = self.base_url + path

        try:

            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "Accept": "application/json"
                },
            )

            with urllib.request.urlopen(
                req,
                timeout=timeout,
            ) as response:

                raw = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

                return json.loads(raw)

        except Exception as e:

            return {
                "status": "error",
                "error": str(e),
                "url": url,
            }

    def health(self) -> dict:

        result = self._get(
            "/v1/developer/health",
            timeout=5,
        )

        if result.get("status") != "error":
            return result

        return self._get(
            "/v1/health",
            timeout=5,
        )

    def rag_context(
        self,
        query: str,
        top_k: int = 8,
    ) -> dict:

        encoded = urllib.parse.quote(
            query,
            safe="",
        )

        result = self._get(
            f"/v1/rag/context?q={encoded}",
            timeout=30,
        )

        if result.get("status") == "error":

            return {
                "status": "error",
                "query": query,
                "items": [],
                "error": result.get(
                    "error"
                ),
            }

        return {
            "status": "ok",
            "query": query,
            "raw": result,
            "items": self._normalize_items(
                result,
                top_k,
            ),
        }

    def _normalize_items(
        self,
        data: dict,
        top_k: int = 8,
    ) -> list[dict]:

        items = []

        def add_items(
            values,
            source_type,
        ):

            if not isinstance(
                values,
                list,
            ):
                return

            for item in values:

                if isinstance(
                    item,
                    str,
                ):

                    items.append(
                        {
                            "source_type":
                                source_type,
                            "text": item,
                        }
                    )

                elif isinstance(
                    item,
                    dict,
                ):

                    copy = dict(item)

                    copy.setdefault(
                        "source_type",
                        source_type,
                    )

                    text = (
                        copy.get("text")
                        or copy.get("content")
                        or copy.get("snippet")
                        or copy.get("source")
                        or ""
                    )

                    copy["text"] = str(
                        text
                    )

                    items.append(copy)

        # Common Developer Core formats.

        add_items(
            data.get("graph"),
            "graph",
        )

        add_items(
            data.get("graph_results"),
            "graph",
        )

        add_items(
            data.get("source"),
            "source",
        )

        add_items(
            data.get("source_results"),
            "source",
        )

        add_items(
            data.get("evidence"),
            "evidence",
        )

        add_items(
            data.get("results"),
            "rag",
        )

        # Some versions return nested objects.

        for key in (
            "data",
            "context",
            "rag",
        ):

            nested = data.get(key)

            if isinstance(
                nested,
                dict,
            ):

                add_items(
                    nested.get("graph"),
                    "graph",
                )

                add_items(
                    nested.get("graph_results"),
                    "graph",
                )

                add_items(
                    nested.get("source"),
                    "source",
                )

                add_items(
                    nested.get("source_results"),
                    "source",
                )

                add_items(
                    nested.get("evidence"),
                    "evidence",
                )

                add_items(
                    nested.get("results"),
                    "rag",
                )

        return items[:top_k]

    def search(
        self,
        query: str,
        top_k: int = 8,
    ) -> dict:

        return self.rag_context(
            query,
            top_k,
        )


# ================================================================
# MASTER QUERY DOMAIN
# ================================================================

class MasterDomainEngine:

    SERVICE_TERMS = [
        "ktp",
        "ktp-el",
        "ktpel",
        "kartu tanda penduduk",
        "kartu keluarga",
        "kk",
        "kia",
        "akta kelahiran",
        "akta kematian",
        "kematian",
        "kelahiran",
        "perkawinan",
        "pernikahan",
        "perceraian",
        "cerai",
        "pindah",
        "domisili",
        "nik",
        "dukcapil",
        "dokumen kependudukan",
        "administrasi kependudukan",
        "pelayanan",
        "persyaratan",
        "syarat",
        "pengajuan",
        "permohonan",
        "status pengajuan",
        "berapa hari",
        "lama proses",
    ]

    DEVELOPER_TERMS = [
        "python",
        "powershell",
        "source code",
        "kode",
        "coding",
        "program",
        "programming",
        "developer",
        "engine",
        "api",
        "endpoint",
        "fastapi",
        "ollama",
        "graphify",
        "graph rag",
        "source rag",
        "rag",
        "database",
        "sqlite",
        "json",
        "bug",
        "error",
        "exception",
        "traceback",
        "function",
        "class",
        "module",
        "route",
        "routes.py",
        "developer_core_engine.py",
        "dependency",
        "dependencies",
        "powershell",
        "server",
        "uvicorn",
        "localhost",
        "port 8010",
        "port 8020",
    ]

    def classify(
        self,
        query: str,
    ) -> str:

        text = normalize_text(query)

        developer_score = sum(
            1
            for term in self.DEVELOPER_TERMS
            if term in text
        )

        service_score = sum(
            1
            for term in self.SERVICE_TERMS
            if term in text
        )

        if developer_score > 0:
            return "developer"

        if service_score > 0:
            return "service"

        return "general"


# ================================================================
# OFFICIAL PRODUCTION KNOWLEDGE ENGINE
# ================================================================

class OfficialKnowledgeEngine:

    """
    Hanya mengambil knowledge yang memenuhi:

        source_status = official / verified
        authority     = official / verified
        verified      = 1

    Test fixture tidak boleh masuk ke jawaban resmi.
    """

    ALLOWED_STATUS = {"official", "verified"}
    ALLOWED_AUTHORITY = {"official", "verified"}

    def __init__(self):
        self.db = ROOT / "data" / "knowledge" / "production_knowledge.db"

    def available(self) -> bool:
        return self.db.exists()

    def _connect(self):
        if not self.db.exists():
            return None

        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        return conn

    def documents(self) -> list[dict]:
        conn = self._connect()

        if conn is None:
            return []

        try:
            rows = conn.execute(
                """
                SELECT
                    document_id,
                    title,
                    source_file,
                    service,
                    content_type,
                    source_status,
                    authority,
                    verified
                FROM documents
                ORDER BY title
                """
            ).fetchall()

            result = []

            for row in rows:
                result.append(dict(row))

            return result

        except Exception:
            return []

        finally:
            conn.close()

    def official_documents(self) -> list[dict]:
        docs = self.documents()

        return [
            d
            for d in docs
            if str(d.get("source_status", "")).lower()
            in self.ALLOWED_STATUS
            and str(d.get("authority", "")).lower()
            in self.ALLOWED_AUTHORITY
            and int(d.get("verified") or 0) == 1
        ]

    def search(
        self,
        query: str,
        top_k: int = 5,
        service: Optional[str] = None,
    ) -> list[dict]:

        conn = self._connect()

        if conn is None:
            return []

        q_tokens = tokenize(query)

        try:
            rows = conn.execute(
                """
                SELECT
                    c.chunk_id,
                    c.document_id,
                    c.chunk_index,
                    c.text,
                    d.title,
                    d.source_file,
                    d.service,
                    d.content_type,
                    d.source_status,
                    d.authority,
                    d.verified
                FROM chunks c
                JOIN documents d
                  ON d.document_id = c.document_id
                """
            ).fetchall()

            candidates = []

            for row in rows:

                if (
                    service
                    and str(row["service"] or "").lower()
                    != service.lower()
                ):
                    continue

                source_status = str(
                    row["source_status"] or ""
                ).lower()

                authority = str(
                    row["authority"] or ""
                ).lower()

                verified = int(row["verified"] or 0)

                if source_status not in self.ALLOWED_STATUS:
                    continue

                if authority not in self.ALLOWED_AUTHORITY:
                    continue

                if verified != 1:
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

                candidates.append(
                    {
                        "chunk_id": row["chunk_id"],
                        "document_id": row["document_id"],
                        "chunk_index": row["chunk_index"],
                        "text": text,
                        "title": row["title"],
                        "source_file": row["source_file"],
                        "service": row["service"],
                        "content_type": row["content_type"],
                        "source_status": source_status,
                        "authority": authority,
                        "verified": verified,
                        "score": round(score, 4),
                    }
                )

            candidates.sort(
                key=lambda x: x["score"],
                reverse=True,
            )

            return candidates[:top_k]

        except Exception:
            return []

        finally:
            conn.close()

    def status(self) -> dict:

        docs = self.documents()
        official = self.official_documents()

        return {
            "database": str(self.db),
            "database_exists": self.db.exists(),
            "documents": len(docs),
            "official_verified_documents": len(official),
            "fail_closed": len(official) == 0,
            "documents_detail": docs,
        }


# ================================================================
# INTENT ENGINE
# ================================================================

class IntentEngine:

    SERVICE_PATTERNS = {
        "ktp_el": [
            "ktp",
            "ktp-el",
            "ktpel",
            "kartu tanda penduduk",
        ],
        "kk": [
            "kartu keluarga",
            "kk",
        ],
        "kia": [
            "kia",
            "kartu identitas anak",
        ],
        "akta_kelahiran": [
            "akta kelahiran",
            "kelahiran",
        ],
        "akta_kematian": [
            "akta kematian",
            "kematian",
        ],
        "perkawinan": [
            "perkawinan",
            "pernikahan",
        ],
        "perceraian": [
            "perceraian",
            "cerai",
        ],
        "pindah": [
            "pindah",
            "domisili",
        ],
    }

    INTENTS = {
        "check_status": [
            "cek status",
            "check status",
            "status pengajuan",
            "sudah sampai mana",
            "sampai mana",
            "proses saya",
        ],
        "requirements": [
            "syarat",
            "persyaratan",
            "dokumen apa",
            "harus membawa",
            "dibutuhkan",
        ],
        "procedure": [
            "cara",
            "bagaimana",
            "prosedur",
            "langkah",
            "mengajukan",
        ],
        "duration": [
            "berapa hari",
            "berapa lama",
            "lama proses",
            "waktu proses",
        ],
        "complaint": [
            "pengaduan",
            "keluhan",
            "komplain",
            "tidak bisa",
            "gagal",
        ],
    }

    def classify(self, text: str) -> dict:

        normalized = normalize_text(text)

        service = None
        service_score = 0

        for name, patterns in self.SERVICE_PATTERNS.items():
            score = sum(
                1
                for p in patterns
                if p in normalized
            )

            if score > service_score:
                service = name
                service_score = score

        intent = "general"
        intent_score = 0

        for name, patterns in self.INTENTS.items():
            score = sum(
                1
                for p in patterns
                if p in normalized
            )

            if score > intent_score:
                intent = name
                intent_score = score

        return {
            "intent": intent,
            "confidence": round(
                min(intent_score / 2, 1.0),
                3,
            ),
            "service": service,
            "service_confidence": round(
                min(service_score / 2, 1.0),
                3,
            ),
            "query": text,
        }


# ================================================================
# ENTITY ENGINE
# ================================================================

class EntityEngine:

    ENTITY_PATTERNS = {
        "NIK": r"\b\d{16}\b",
        "PHONE": r"(?:\+62|62|0)8\d{8,13}\b",
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    }

    def extract(self, text: str) -> dict:

        entities = {}

        for name, pattern in self.ENTITY_PATTERNS.items():

            values = re.findall(
                pattern,
                text or "",
                flags=re.IGNORECASE,
            )

            if values:
                entities[name] = list(
                    dict.fromkeys(values)
                )

        return entities


# ================================================================
# CONTEXT ENGINE
# ================================================================

class ContextEngine:

    def build(
        self,
        query: str,
        intent: dict,
        entities: dict,
        memory: list[dict],
    ) -> dict:

        return {
            "query": query,
            "intent": intent,
            "entities": entities,
            "conversation_memory": memory[-5:],
            "timestamp": now_iso(),
        }


# ================================================================
# PROBLEM ENGINE
# ================================================================

class ProblemEngine:

    def analyze(
        self,
        query: str,
        intent: dict,
        entities: dict,
    ) -> dict:

        normalized = normalize_text(query)

        problem_type = "information_request"

        if intent["intent"] == "check_status":
            problem_type = "status_inquiry"

        elif intent["intent"] == "complaint":
            problem_type = "service_problem"

        elif "gagal" in normalized:
            problem_type = "transaction_failure"

        elif "error" in normalized:
            problem_type = "technical_error"

        return {
            "problem_type": problem_type,
            "service": intent.get("service"),
            "intent": intent.get("intent"),
            "entities": entities,
            "goal": self._goal(intent),
        }

    def _goal(self, intent: dict) -> str:

        mapping = {
            "check_status": "mengetahui status pelayanan",
            "requirements": "mengetahui persyaratan",
            "procedure": "mengetahui prosedur",
            "duration": "mengetahui waktu pelayanan",
            "complaint": "mendapatkan penyelesaian masalah",
        }

        return mapping.get(
            intent.get("intent"),
            "mendapatkan informasi",
        )


# ================================================================
# POLICY ENGINE
# ================================================================

class PolicyEngine:

    def authorize(
        self,
        query: str,
        intent: dict,
        knowledge: list[dict],
    ) -> dict:

        official_count = len(knowledge)

        if intent.get("service") and official_count == 0:
            return {
                "allowed": False,
                "reason": "official_knowledge_required",
                "message": (
                    "Sumber resmi atau terverifikasi "
                    "belum tersedia untuk pertanyaan pelayanan ini."
                ),
            }

        return {
            "allowed": True,
            "reason": "policy_pass",
            "message": None,
        }


# ================================================================
# TRUST ENGINE
# ================================================================

class TrustEngine:

    def evaluate(
        self,
        evidence: list[dict],
        answer: Optional[str] = None,
    ) -> dict:

        if not evidence:
            return {
                "level": "NO_TRUST",
                "score": 0.0,
                "grounded": False,
            }

        evidence_score = max(
            float(x.get("score", 0))
            for x in evidence
        )

        answer_score = 1.0

        if answer:
            answer_tokens = tokenize(answer)
            evidence_tokens = tokenize(
                " ".join(
                    x.get("text", "")
                    for x in evidence
                )
            )

            if answer_tokens:
                overlap = (
                    len(answer_tokens & evidence_tokens)
                    / len(answer_tokens)
                )

                answer_score = min(
                    overlap * 1.5,
                    1.0,
                )

        score = round(
            0.6 * evidence_score
            + 0.4 * answer_score,
            4,
        )

        if score >= 0.70:
            level = "HIGH"
        elif score >= 0.40:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "level": level,
            "score": score,
            "grounded": score >= 0.40,
        }


# ================================================================
# REASONING CORE
# ================================================================

class ReasoningCore:

    def build_plan(
        self,
        query: str,
        context: dict,
        evidence: list[dict],
    ) -> dict:

        steps = [
            "interpret_query",
            "validate_entities",
            "inspect_authoritative_knowledge",
        ]

        if evidence:
            steps.append("construct_grounded_answer")
        else:
            steps.append("fail_closed")

        return {
            "reasoning_id": str(uuid.uuid4()),
            "steps": steps,
            "evidence_count": len(evidence),
            "context": context,
        }


# ================================================================
# WORKFLOW ENGINE
# ================================================================

class WorkflowEngine:

    def execute(
        self,
        query: str,
        context: dict,
        evidence: list[dict],
        policy: dict,
    ) -> dict:

        return {
            "workflow_id": str(uuid.uuid4()),
            "status": (
                "READY"
                if policy["allowed"]
                else "BLOCKED"
            ),
            "steps": [
                {
                    "name": "intent",
                    "status": "completed",
                },
                {
                    "name": "entity",
                    "status": "completed",
                },
                {
                    "name": "context",
                    "status": "completed",
                },
                {
                    "name": "knowledge",
                    "status": (
                        "completed"
                        if evidence
                        else "empty"
                    ),
                },
                {
                    "name": "policy",
                    "status": (
                        "passed"
                        if policy["allowed"]
                        else "blocked"
                    ),
                },
            ],
        }


# ================================================================
# MEMORY ENGINE
# ================================================================

class MemoryEngine:

    def __init__(self):
        self.db = MEMORY_DB
        self._init()

    def _init(self):

        conn = sqlite3.connect(self.db)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                created_at TEXT
            )
        """)

        conn.commit()
        conn.close()

    def add(
        self,
        session_id: str,
        role: str,
        content: str,
    ):

        conn = sqlite3.connect(self.db)

        conn.execute(
            """
            INSERT INTO memory
            (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                now_iso(),
            ),
        )

        conn.commit()
        conn.close()

    def recent(
        self,
        session_id: str,
        limit: int = 10,
    ):

        conn = sqlite3.connect(self.db)

        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM memory
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                session_id,
                limit,
            ),
        ).fetchall()

        conn.close()

        rows.reverse()

        return [
            {
                "role": r[0],
                "content": r[1],
                "created_at": r[2],
            }
            for r in rows
        ]


# ================================================================
# TOOL ENGINE
# ================================================================

class ToolEngine:

    def __init__(self):
        self.tools = {}

    def register(
        self,
        name: str,
        description: str,
        handler,
    ):

        self.tools[name] = {
            "name": name,
            "description": description,
            "handler": handler,
        }

    def list(self):

        return [
            {
                "name": v["name"],
                "description": v["description"],
            }
            for v in self.tools.values()
        ]

    def execute(
        self,
        name: str,
        arguments: dict,
    ):

        tool = self.tools.get(name)

        if not tool:
            raise ValueError(
                f"Tool tidak ditemukan: {name}"
            )

        return tool["handler"](**arguments)


# ================================================================
# MCP ENGINE
# ================================================================

class MCPEngine:

    def __init__(
        self,
        tool_engine: ToolEngine,
    ):
        self.tool_engine = tool_engine

    def manifest(self):

        return {
            "name": "nusantara-mcp",
            "version": "1.0.0",
            "protocol": "local-json-rpc",
            "tools": self.tool_engine.list(),
        }

    def handle(
        self,
        request: dict,
    ) -> dict:

        method = request.get("method")
        params = request.get("params") or {}

        if method == "tools/list":

            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": self.tool_engine.list(),
            }

        if method == "tools/call":

            name = params.get("name")
            arguments = params.get(
                "arguments",
                {},
            )

            try:

                result = self.tool_engine.execute(
                    name,
                    arguments,
                )

                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": result,
                }

            except Exception as e:

                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32000,
                        "message": str(e),
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32601,
                "message": "Method not found",
            },
        }


# ================================================================
# HUMAN HANDOFF ENGINE
# ================================================================

class HumanHandoffEngine:

    def create(
        self,
        query: str,
        reason: str,
        context: dict,
    ) -> dict:

        handoff_id = str(uuid.uuid4())

        return {
            "handoff_id": handoff_id,
            "status": "PENDING",
            "reason": reason,
            "query": query,
            "context": context,
            "created_at": now_iso(),
        }


# ================================================================
# EVALUATION ENGINE
# ================================================================

class EvaluationEngine:

    def evaluate(
        self,
        query: str,
        answer: str,
        evidence: list[dict],
        trust: dict,
    ) -> dict:

        answer_tokens = tokenize(answer)

        evidence_tokens = tokenize(
            " ".join(
                e.get("text", "")
                for e in evidence
            )
        )

        overlap = 0.0

        if answer_tokens:
            overlap = (
                len(answer_tokens & evidence_tokens)
                / len(answer_tokens)
            )

        return {
            "evaluation_id": str(uuid.uuid4()),
            "grounding_overlap": round(
                overlap,
                4,
            ),
            "evidence_count": len(evidence),
            "trust": trust,
            "answer_nonempty": bool(
                answer.strip()
            ),
            "evaluated_at": now_iso(),
        }


# ================================================================
# OLLAMA ENGINE
# ================================================================

class OllamaEngine:

    def __init__(
        self,
        url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
    ):

        self.url = url.rstrip("/")
        self.model = model

    def health(self) -> bool:

        try:

            req = urllib.request.Request(
                self.url + "/api/tags",
                method="GET",
            )

            with urllib.request.urlopen(
                req,
                timeout=5,
            ) as response:

                return response.status == 200

        except Exception:
            return False

    def generate(
        self,
        system: str,
        prompt: str,
    ) -> str:

        payload = {
            "model": self.model,
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
            "system": system,
            "prompt": prompt,
        }

        data = json.dumps(
            payload
        ).encode("utf-8")

        request = urllib.request.Request(
            self.url + "/api/generate",
            data=data,
            headers={
                "Content-Type":
                    "application/json"
            },
            method="POST",
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=180,
            ) as response:

                result = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

                return str(
                    result.get(
                        "response",
                        "",
                    )
                ).strip()

        except Exception as e:

            return (
                "Ollama tidak dapat digunakan: "
                + str(e)
            )


# ================================================================
# GROUNDING GUARD
# ================================================================

class GroundingGuard:

    def validate(
        self,
        answer: str,
        evidence: list[dict],
    ) -> dict:

        if not evidence:
            return {
                "allowed": False,
                "reason": "no_evidence",
                "answer": (
                    "Informasi resmi atau sumber "
                    "terverifikasi belum tersedia."
                ),
            }

        answer_tokens = tokenize(answer)

        evidence_tokens = tokenize(
            " ".join(
                x.get("text", "")
                for x in evidence
            )
        )

        overlap = 0.0

        if answer_tokens:
            overlap = (
                len(
                    answer_tokens
                    & evidence_tokens
                )
                / len(answer_tokens)
            )

        if overlap < 0.15:

            return {
                "allowed": False,
                "reason": "answer_not_grounded",
                "overlap": round(
                    overlap,
                    4,
                ),
                "answer": (
                    "Jawaban tidak dapat "
                    "diverifikasi terhadap "
                    "sumber resmi."
                ),
            }

        return {
            "allowed": True,
            "reason": "grounded",
            "overlap": round(
                overlap,
                4,
            ),
            "answer": answer,
        }


# ================================================================
# MASTER ENGINE
# ================================================================

class NusantaraMasterEngine:

    def __init__(self):

        self.observability = (
            ObservabilityEngine()
        )

        self.knowledge = (
            OfficialKnowledgeEngine()
        )

        self.developer_core = (
            DeveloperCoreClient()
        )

        self.domain_engine = (
            MasterDomainEngine()
        )

        self.intent = IntentEngine()
        self.entity = EntityEngine()
        self.context = ContextEngine()
        self.problem = ProblemEngine()
        self.reasoning = ReasoningCore()
        self.workflow = WorkflowEngine()
        self.policy = PolicyEngine()
        self.trust = TrustEngine()
        self.memory = MemoryEngine()
        self.tools = ToolEngine()
        self.mcp = MCPEngine(
            self.tools
        )
        self.handoff = (
            HumanHandoffEngine()
        )
        self.evaluation = (
            EvaluationEngine()
        )
        self.ollama = OllamaEngine()
        self.grounding = GroundingGuard()

        self._register_tools()

    def _register_tools(self):

        self.tools.register(
            "developer_core_health",
            "Memeriksa Developer Core 8010.",
            lambda: self.developer_core.health(),
        )

        self.tools.register(
            "developer_rag_search",
            "Mencari Graph RAG dan Source RAG Developer Core.",
            lambda query, top_k=8:
                self.developer_core.search(
                    query,
                    int(top_k),
                ),
        )

        self.tools.register(
            "knowledge_status",
            "Menampilkan status Official Production Knowledge.",
            lambda: self.knowledge.status(),
        )

        self.tools.register(
            "search_official_knowledge",
            "Mencari knowledge resmi.",
            lambda query, top_k=5:
                self.knowledge.search(
                    query,
                    int(top_k),
                ),
        )

        self.tools.register(
            "system_health",
            "Memeriksa kesehatan engine.",
            lambda: self.health(),
        )

    def health(self):

        return {
            "status": "ok",
            "engine": "Nusantara Master Engine",
            "version": "1.0.0",
            "official_knowledge":
                self.knowledge.status(),
            "ollama": {
                "url": self.ollama.url,
                "model": self.ollama.model,
                "available":
                    self.ollama.health(),
            },
            "developer_core": self.developer_core.health(),
            "engines": {
                "intent": True,
                "entity": True,
                "context": True,
                "problem": True,
                "reasoning": True,
                "workflow": True,
                "policy": True,
                "trust": True,
                "memory": True,
                "tool": True,
                "mcp": True,
                "human_handoff": True,
                "evaluation": True,
                "observability": True,
                "local_ui": True,
            },
        }

    def process(
        self,
        query: str,
        session_id: str = "default",
    ) -> dict:

        started = time.perf_counter()

        self.observability.event(
            "request_started",
            {
                "query": query,
                "session_id": session_id,
            },
        )

        # --------------------------------------------------------
        # 1. INTENT
        # --------------------------------------------------------

        intent = self.intent.classify(
            query
        )

        # --------------------------------------------------------
        # 2. ENTITY
        # --------------------------------------------------------

        entities = self.entity.extract(
            query
        )

        # --------------------------------------------------------
        # 3. MEMORY
        # --------------------------------------------------------

        memory = self.memory.recent(
            session_id
        )

        # --------------------------------------------------------
        # 4. CONTEXT
        # --------------------------------------------------------

        context = self.context.build(
            query,
            intent,
            entities,
            memory,
        )

        # --------------------------------------------------------
        # 5. PROBLEM
        # --------------------------------------------------------

        problem = self.problem.analyze(
            query,
            intent,
            entities,
        )

        # --------------------------------------------------------
        # 6. MASTER DOMAIN ROUTING
        # --------------------------------------------------------

        master_domain = self.domain_engine.classify(
            query
        )

        developer_context = None

        # --------------------------------------------------------
        # 7. DEVELOPER CORE
        # --------------------------------------------------------

        if master_domain == "developer":

            developer_context = (
                self.developer_core.search(
                    query,
                    top_k=8,
                )
            )

            evidence = []

            developer_items = (
                developer_context.get(
                    "items",
                    []
                )
                if isinstance(
                    developer_context,
                    dict,
                )
                else []
            )

            for item in developer_items:

                evidence.append(
                    {
                        "chunk_id": None,
                        "document_id": None,
                        "chunk_index": 0,
                        "text": item.get(
                            "text",
                            "",
                        ),
                        "title": (
                            item.get("name")
                            or item.get("title")
                            or "Developer Core"
                        ),
                        "source_file": (
                            item.get("path")
                            or item.get("file")
                            or "Developer Core 8010"
                        ),
                        "service": "developer",
                        "content_type": (
                            item.get(
                                "source_type"
                            )
                            or "code"
                        ),
                        "source_status": "developer",
                        "authority": "developer",
                        "verified": 1,
                        "score": float(
                            item.get(
                                "score",
                                0.0,
                            )
                            or 0.0
                        ),
                    }
                )

        # --------------------------------------------------------
        # 8. OFFICIAL PRODUCTION KNOWLEDGE
        # --------------------------------------------------------

        else:

            evidence = self.knowledge.search(
                query,
                top_k=5,
                service=intent.get(
                    "service"
                ),
            )

        # --------------------------------------------------------
        # 9. POLICY
        # --------------------------------------------------------

        if master_domain == "developer":

            policy = {
                "allowed": bool(evidence),
                "reason": (
                    "developer_core_evidence_available"
                    if evidence
                    else "developer_core_no_evidence"
                ),
                "message": (
                    None
                    if evidence
                    else
                    "Developer Core tidak menemukan "
                    "evidence yang cukup untuk pertanyaan ini."
                ),
            }

        else:

            policy = self.policy.authorize(
                query,
                intent,
                evidence,
            )

        # --------------------------------------------------------
        # 8. REASONING
        # --------------------------------------------------------

        context["master_domain"] = master_domain

        if developer_context is not None:
            context["developer_core"] = {
                "status":
                    developer_context.get(
                        "status"
                    ),
                "item_count":
                    len(
                        developer_context.get(
                            "items",
                            [],
                        )
                    ),
            }

        reasoning = self.reasoning.build_plan(
            query,
            context,
            evidence,
        )

        # --------------------------------------------------------
        # 9. WORKFLOW
        # --------------------------------------------------------

        workflow = self.workflow.execute(
            query,
            context,
            evidence,
            policy,
        )

        # --------------------------------------------------------
        # 10. FAIL CLOSED
        # --------------------------------------------------------

        if not policy["allowed"]:

            handoff = self.handoff.create(
                query,
                policy["reason"],
                context,
            )

            answer = policy["message"]

            trust = self.trust.evaluate(
                evidence
            )

            evaluation = self.evaluation.evaluate(
                query,
                answer,
                evidence,
                trust,
            )

            self.memory.add(
                session_id,
                "user",
                query,
            )

            self.memory.add(
                session_id,
                "assistant",
                answer,
            )

            result = {
                "status": "blocked",
                "answer": answer,
                "master_domain": master_domain,
                "developer_core": (
                    developer_context
                    if master_domain == "developer"
                    else None
                ),
                "intent": intent,
                "entities": entities,
                "context": context,
                "problem": problem,
                "knowledge": {
                    "count": len(evidence),
                    "items": evidence,
                },
                "policy": policy,
                "trust": trust,
                "reasoning": reasoning,
                "workflow": workflow,
                "handoff": handoff,
                "evaluation": evaluation,
            }

            self.observability.event(
                "request_blocked",
                result,
            )

            return result

        # --------------------------------------------------------
        # 11. BUILD GROUNDED PROMPT
        # --------------------------------------------------------

        evidence_text = "\n\n".join(
            [
                (
                    f"[SOURCE {i + 1}]\n"
                    f"Title: {e['title']}\n"
                    f"File: {e['source_file']}\n"
                    f"Status: {e['source_status']}\n"
                    f"Authority: {e['authority']}\n"
                    f"Verified: {e['verified']}\n"
                    f"Score: {e.get('score', 0)}\n"
                    f"Content:\n{e['text']}"
                )
                for i, e in enumerate(
                    evidence
                )
            ]
        )

        system_prompt = """
Anda adalah Nusantara AI.

ATURAN MUTLAK:

1. Jawaban harus Bahasa Indonesia.
2. Jangan mengarang fakta.
3. Untuk SERVICE QUERY:
   gunakan hanya sumber resmi/terverifikasi.
4. Untuk DEVELOPER QUERY:
   gunakan evidence dari Developer Core 8010,
   Graph RAG, Source RAG, dan Graphify.
5. Jangan membuat persyaratan,
   prosedur, biaya, waktu atau kebijakan
   yang tidak terdapat dalam evidence.
6. Jika evidence tidak cukup,
   katakan bahwa informasi belum tersedia.
7. Jangan mengklaim melakukan transaksi
   pelayanan jika tool transaksi tidak dijalankan.
8. Untuk kode/programming, berikan solusi
   berdasarkan source/evidence yang ditemukan.
"""

        user_prompt = f"""
PERTANYAAN:
{query}

INTENT:
{safe_json(intent)}

ENTITY:
{safe_json(entities)}

PROBLEM:
{safe_json(problem)}

SUMBER RESMI:
{evidence_text}

Berikan jawaban berdasarkan SOURCE resmi.
"""

        # --------------------------------------------------------
        # 12. OLLAMA
        # --------------------------------------------------------

        answer = self.ollama.generate(
            system_prompt,
            user_prompt,
        )

        # --------------------------------------------------------
        # 13. TRUST
        # --------------------------------------------------------

        trust = self.trust.evaluate(
            evidence,
            answer,
        )

        # --------------------------------------------------------
        # 14. GROUNDING GUARD
        # --------------------------------------------------------

        grounding = self.grounding.validate(
            answer,
            evidence,
        )

        if not grounding["allowed"]:

            answer = grounding["answer"]

        # --------------------------------------------------------
        # 15. EVALUATION
        # --------------------------------------------------------

        evaluation = self.evaluation.evaluate(
            query,
            answer,
            evidence,
            trust,
        )

        # --------------------------------------------------------
        # 16. MEMORY
        # --------------------------------------------------------

        self.memory.add(
            session_id,
            "user",
            query,
        )

        self.memory.add(
            session_id,
            "assistant",
            answer,
        )

        elapsed = round(
            time.perf_counter()
            - started,
            4,
        )

        result = {
            "status": "ok",
            "answer": answer,
            "latency_seconds": elapsed,
            "master_domain": master_domain,
            "developer_core": (
                developer_context
                if master_domain == "developer"
                else None
            ),
            "intent": intent,
            "entities": entities,
            "context": context,
            "problem": problem,
            "knowledge": {
                "count": len(evidence),
                "items": evidence,
            },
            "policy": policy,
            "reasoning": reasoning,
            "workflow": workflow,
            "trust": trust,
            "grounding": grounding,
            "evaluation": evaluation,
        }

        self.observability.event(
            "request_completed",
            {
                "session_id": session_id,
                "status": result["status"],
                "intent": intent,
                "knowledge_count":
                    len(evidence),
                "trust": trust,
                "latency":
                    elapsed,
            },
        )

        return result


# ================================================================
# API
# ================================================================

app = FastAPI(
    title="Nusantara Master Engine",
    version="1.0.0",
)

engine = NusantaraMasterEngine()


class ChatRequest(BaseModel):

    input: str
    session_id: str = "default"


class MCPRequest(BaseModel):

    jsonrpc: str = "2.0"
    id: Any = 1
    method: str
    params: dict[str, Any] = {}


@app.get(
    "/",
    response_class=HTMLResponse,
)
def ui():

    return """
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width,initial-scale=1">

<title>Nusantara Master Engine</title>

<style>

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #101827;
    color: #e5e7eb;
}

header {
    padding: 22px 30px;
    background: #172033;
    border-bottom: 1px solid #2d3a50;
}

h1 {
    margin: 0;
    font-size: 24px;
}

small {
    color: #94a3b8;
}

main {
    max-width: 1200px;
    margin: auto;
    padding: 25px;
}

textarea {
    width: 100%;
    min-height: 110px;
    padding: 15px;
    box-sizing: border-box;
    background: #0b1220;
    color: white;
    border: 1px solid #334155;
    border-radius: 8px;
    resize: vertical;
}

button {
    margin-top: 12px;
    padding: 12px 22px;
    border: 0;
    border-radius: 7px;
    background: #2563eb;
    color: white;
    cursor: pointer;
}

button:hover {
    background: #1d4ed8;
}

.card {
    margin-top: 20px;
    padding: 20px;
    background: #172033;
    border: 1px solid #2d3a50;
    border-radius: 10px;
}

pre {
    white-space: pre-wrap;
    word-break: break-word;
    background: #0b1220;
    padding: 15px;
    border-radius: 8px;
    overflow: auto;
}

.status {
    display: grid;
    grid-template-columns:
        repeat(auto-fit,minmax(180px,1fr));
    gap: 10px;
}

.item {
    padding: 14px;
    background: #0b1220;
    border-radius: 8px;
}

</style>
</head>

<body>

<header>

<h1>NUSANTARA MASTER ENGINE</h1>

<small>
Official Knowledge • Reasoning • Workflow • Trust • MCP
</small>

</header>

<main>

<div class="card">

<h3>Chat</h3>

<textarea
id="question"
placeholder="Masukkan pertanyaan..."
></textarea>

<br>

<button onclick="ask()">
Jalankan Nusantara
</button>

</div>

<div class="card">

<h3>Jawaban</h3>

<pre id="answer">
Belum ada permintaan.
</pre>

</div>

<div class="card">

<h3>Engine Trace</h3>

<pre id="trace">
-
</pre>

</div>

<div class="card">

<h3>Health</h3>

<pre id="health">
Memuat...
</pre>

</div>

</main>

<script>

async function ask() {

    const q =
        document.getElementById(
            "question"
        ).value;

    const answer =
        document.getElementById(
            "answer"
        );

    const trace =
        document.getElementById(
            "trace"
        );

    answer.textContent =
        "Memproses...";

    const response =
        await fetch(
            "/v1/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    input: q,
                    session_id: "web"
                })
            }
        );

    const data =
        await response.json();

    answer.textContent =
        data.answer || "-";

    trace.textContent =
        JSON.stringify(
            {
                status: data.status,
                intent: data.intent,
                entities: data.entities,
                problem: data.problem,
                knowledge:
                    data.knowledge,
                policy: data.policy,
                trust: data.trust,
                grounding:
                    data.grounding,
                workflow:
                    data.workflow,
                evaluation:
                    data.evaluation
            },
            null,
            2
        );
}


async function health() {

    const response =
        await fetch(
            "/v1/health"
        );

    const data =
        await response.json();

    document.getElementById(
        "health"
    ).textContent =
        JSON.stringify(
            data,
            null,
            2
        );
}

health();

</script>

</body>
</html>
"""


@app.get("/v1/health")
def health():

    return engine.health()


@app.get("/v1/knowledge/status")
def knowledge_status():

    return engine.knowledge.status()


@app.get("/v1/tools")
def tools():

    return engine.tools.list()


@app.get("/v1/mcp")
def mcp_manifest():

    return engine.mcp.manifest()


@app.get("/v1/observability")
def observability():

    return engine.observability.recent()


@app.post("/v1/mcp")
def mcp(
    request: MCPRequest,
):

    return engine.mcp.handle(
        request.model_dump()
    )


@app.post("/v1/chat")
def chat(
    request: ChatRequest,
):

    if not request.input.strip():

        raise HTTPException(
            status_code=400,
            detail="Input tidak boleh kosong.",
        )

    return engine.process(
        request.input,
        request.session_id,
    )


@app.get("/v1/official/search")
def official_search(
    q: str,
    top_k: int = 5,
):

    return {
        "query": q,
        "results":
            engine.knowledge.search(
                q,
                top_k,
            ),
    }


# ================================================================
# START
# ================================================================

if __name__ == "__main__":

    import uvicorn

    print()
    print("=" * 72)
    print(" NUSANTARA MASTER ENGINE")
    print("=" * 72)
    print("Official Production Knowledge : ENABLED")
    print("Intent Engine                 : ENABLED")
    print("Entity Engine                 : ENABLED")
    print("Context Engine                : ENABLED")
    print("Problem Engine                : ENABLED")
    print("Reasoning Core                : ENABLED")
    print("Workflow Engine               : ENABLED")
    print("Policy Engine                 : ENABLED")
    print("Trust Engine                  : ENABLED")
    print("Memory Engine                 : ENABLED")
    print("Tool Engine                   : ENABLED")
    print("MCP Engine                    : ENABLED")
    print("Human Handoff                 : ENABLED")
    print("Evaluation Engine             : ENABLED")
    print("Observability                 : ENABLED")
    print("Local Web UI                  : ENABLED")
    print("Ollama                        :", OLLAMA_MODEL)
    print("=" * 72)
    print()
    print("Web UI : http://127.0.0.1:8020")
    print("API    : http://127.0.0.1:8020/docs")
    print()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8020,
        log_level="info",
    )
