from __future__ import annotations

import json
import re
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


# ============================================================
# NUSANTARA MASTER ENGINE DEVELOPER AI
# ============================================================

ROOT = Path(__file__).resolve().parent

MASTER_PORT = 8020
DEVELOPER_CORE_URL = "http://127.0.0.1:8010"
OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "llama3.2:1b"

KNOWLEDGE_DB = ROOT / "data" / "knowledge" / "production_knowledge.db"


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Nusantara Master Engine Developer AI",
    version="1.0.0",
)


# ============================================================
# REQUEST
# ============================================================

class ChatRequest(BaseModel):
    input: str
    model: str | None = None


# ============================================================
# HTTP HELPER
# ============================================================

def http_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:

    data = None

    headers = {
        "Accept": "application/json",
    }

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            raw = response.read().decode(
                "utf-8",
                errors="replace",
            )

            return json.loads(raw)

    except Exception as exc:

        return {
            "ok": False,
            "error": str(exc),
        }


# ============================================================
# DOMAIN CLASSIFIER
# ============================================================

SERVICE_TERMS = [
    "ktp",
    "ktp-el",
    "ktpel",
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
    "dependency",
    "dependencies",
    "master engine",
    "developer core",
    "software",
]


def classify_domain(text: str) -> str:

    q = (text or "").lower().strip()

    if any(term in q for term in DEVELOPER_TERMS):
        return "developer"

    if any(term in q for term in SERVICE_TERMS):
        return "service"

    return "general"


# ============================================================
# INTENT
# ============================================================

def classify_intent(text: str) -> str:

    q = (text or "").lower()

    if any(
        x in q
        for x in [
            "syarat",
            "persyaratan",
            "dokumen",
            "harus membawa",
        ]
    ):
        return "requirements"

    if any(
        x in q
        for x in [
            "cara",
            "bagaimana",
            "prosedur",
            "langkah",
            "buat",
        ]
    ):
        return "procedure"

    if any(
        x in q
        for x in [
            "berapa hari",
            "lama",
            "durasi",
            "kapan selesai",
        ]
    ):
        return "duration"

    if any(
        x in q
        for x in [
            "status",
            "sudah selesai",
            "sudah jadi",
            "cek pengajuan",
        ]
    ):
        return "check_status"

    if any(
        x in q
        for x in [
            "pengaduan",
            "keluhan",
            "komplain",
            "mengadu",
        ]
    ):
        return "complaint"

    return "general"


# ============================================================
# OFFICIAL KNOWLEDGE
# ============================================================

def search_official_knowledge(
    query: str,
    limit: int = 8,
) -> list[dict[str, Any]]:

    if not KNOWLEDGE_DB.exists():
        return []

    terms = re.findall(
        r"[a-zA-Z0-9_-]+",
        query.lower(),
    )

    terms = [
        x
        for x in terms
        if len(x) >= 2
    ]

    if not terms:
        return []

    conn = sqlite3.connect(
        str(KNOWLEDGE_DB)
    )

    conn.row_factory = sqlite3.Row

    try:

        rows = conn.execute(
            """
            SELECT
                c.chunk_id,
                c.document_id,
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
            WHERE
                d.active = 1
                AND LOWER(COALESCE(d.source_status, ''))
                    IN ('official', 'verified')
                AND LOWER(COALESCE(d.authority, ''))
                    IN ('official', 'verified')
                AND COALESCE(d.verified, 0) = 1
                AND LOWER(COALESCE(d.service, ''))
                    = 'ktp_el'
            ORDER BY d.ingested_at DESC
            """
        ).fetchall()

        scored = []

        for row in rows:

            text = str(
                row["text"] or ""
            )

            lower_text = text.lower()

            score = 0

            for term in terms:

                if term in lower_text:
                    score += 1

            # Strong domain terms
            if "ktp-el" in lower_text:
                score += 3

            if "persyaratan" in lower_text:
                score += 3

            if "perekaman" in lower_text:
                score += 2

            if "pemula" in lower_text:
                score += 4

            if score <= 0:
                continue

            scored.append(
                (
                    score,
                    dict(row),
                )
            )

        scored.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        result = []

        for score, item in scored[:limit]:

            item["score"] = score
            item["authority"] = "official"
            item["verified"] = 1

            result.append(item)

        return result

    finally:

        conn.close()


# ============================================================
# DEVELOPER CORE
# ============================================================

def developer_core(query: str) -> dict[str, Any]:

    return http_json(
        DEVELOPER_CORE_URL + "/v1/chat",
        method="POST",
        payload={
            "input": query,
        },
        timeout=60,
    )


# ============================================================
# OLLAMA
# ============================================================

def ollama_chat(
    query: str,
    context: str,
    model: str | None = None,
) -> dict[str, Any]:

    selected_model = (
        model
        or OLLAMA_MODEL
    )

    system_prompt = """
Anda adalah Nusantara AI.

Aturan utama:
1. Jawab dalam Bahasa Indonesia.
2. Jangan mengarang fakta.
3. Untuk informasi pelayanan publik, gunakan hanya evidence resmi/terverifikasi.
4. Jika evidence tidak cukup, katakan bahwa informasi belum tersedia.
5. Jangan mengklaim dapat mengecek status pribadi seseorang tanpa sistem status yang benar-benar terhubung.
6. Untuk pertanyaan developer, gunakan context Developer Core bila tersedia.
7. Bedakan fakta dari asumsi.
"""

    prompt = f"""
PERTANYAAN:
{query}

EVIDENCE:
{context}

Berikan jawaban yang ringkas, jelas, dan berdasarkan evidence.
"""

    result = http_json(
        OLLAMA_URL + "/api/chat",
        method="POST",
        payload={
            "model": selected_model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        },
        timeout=180,
    )

    return result


# ============================================================
# GROUNDING
# ============================================================

def grounding_check(
    answer: str,
    evidence: str,
) -> dict[str, Any]:

    answer_tokens = set(
        re.findall(
            r"\b[a-zA-Z0-9-]{3,}\b",
            answer.lower(),
        )
    )

    evidence_tokens = set(
        re.findall(
            r"\b[a-zA-Z0-9-]{3,}\b",
            evidence.lower(),
        )
    )

    if not answer_tokens:
        return {
            "grounded": False,
            "score": 0,
        }

    overlap = (
        len(answer_tokens & evidence_tokens)
        / len(answer_tokens)
    )

    if overlap >= 0.35:
        level = "GROUNDED"
    elif overlap >= 0.15:
        level = "PARTIAL"
    else:
        level = "UNSUPPORTED"

    return {
        "grounded": level != "UNSUPPORTED",
        "level": level,
        "score": round(overlap, 4),
    }


# ============================================================
# SERVICE ANSWER
# ============================================================

def service_pipeline(
    query: str,
    model: str | None = None,
) -> dict[str, Any]:

    intent = classify_intent(
        query
    )

    evidence = search_official_knowledge(
        query,
        limit=8,
    )

    # --------------------------------------------------------
    # FAIL CLOSED
    # --------------------------------------------------------

    if not evidence:

        return {
            "status": "blocked",
            "domain": "service",
            "intent": intent,
            "answer": (
                "Sumber resmi atau terverifikasi "
                "belum ditemukan untuk pertanyaan pelayanan ini. "
                "Jawaban tidak dibuat berdasarkan asumsi model."
            ),
            "knowledge": [],
            "trust": {
                "level": "NO_TRUST",
                "grounded": False,
            },
        }

    context_parts = []

    for item in evidence:

        context_parts.append(
            f"""
SOURCE: {item['source_file']}
TITLE: {item['title']}
SERVICE: {item['service']}
AUTHORITY: {item['authority']}
VERIFIED: {item['verified']}
TEXT:
{item['text']}
"""
        )

    context = "\n".join(
        context_parts
    )

    llm = ollama_chat(
        query,
        context,
        model=model,
    )

    answer = (
        llm.get("message", {})
        .get("content", "")
    )

    if not answer:

        answer = (
            "Evidence resmi ditemukan, "
            "tetapi Ollama tidak menghasilkan jawaban."
        )

    grounding = grounding_check(
        answer,
        context,
    )

    return {
        "status": "ok",
        "domain": "service",
        "intent": intent,
        "answer": answer,
        "knowledge": evidence,
        "trust": {
            "level": grounding["level"],
            "grounded": grounding["grounded"],
            "score": grounding["score"],
        },
        "model": model or OLLAMA_MODEL,
    }


# ============================================================
# DEVELOPER PIPELINE
# ============================================================

def developer_pipeline(
    query: str,
) -> dict[str, Any]:

    result = developer_core(
        query
    )

    if not result.get("ok", True):

        return {
            "status": "developer_core_error",
            "domain": "developer",
            "answer": (
                "Developer Core tidak dapat dihubungi."
            ),
            "developer_core": result,
        }

    return {
        "status": "ok",
        "domain": "developer",
        "answer": result.get(
            "answer",
            result.get(
                "output",
                result,
            ),
        ),
        "developer_core": result,
    }


# ============================================================
# MASTER CHAT
# ============================================================

def master_chat(
    query: str,
    model: str | None = None,
) -> dict[str, Any]:

    query = (
        query or ""
    ).strip()

    if not query:

        return {
            "status": "error",
            "answer": "Pertanyaan kosong.",
        }

    domain = classify_domain(
        query
    )

    if domain == "service":

        return service_pipeline(
            query,
            model=model,
        )

    if domain == "developer":

        return developer_pipeline(
            query
        )

    # General:
    # gunakan official knowledge bila tersedia.
    evidence = search_official_knowledge(
        query,
        limit=5,
    )

    if evidence:

        context = "\n\n".join(
            item["text"]
            for item in evidence
        )

        llm = ollama_chat(
            query,
            context,
            model=model,
        )

        answer = (
            llm.get("message", {})
            .get("content", "")
        )

        return {
            "status": "ok",
            "domain": "general",
            "answer": answer,
            "knowledge": evidence,
        }

    return {
        "status": "blocked",
        "domain": "general",
        "answer": (
            "Belum tersedia evidence pengetahuan "
            "yang cukup untuk menjawab pertanyaan ini."
        ),
    }


# ============================================================
# API
# ============================================================

@app.get(
    "/v1/health"
)
def health():

    developer = http_json(
        DEVELOPER_CORE_URL
        + "/v1/developer/health",
        timeout=5,
    )

    ollama = http_json(
        OLLAMA_URL
        + "/api/tags",
        timeout=5,
    )

    conn_ok = False
    official_count = 0
    document_count = 0

    if KNOWLEDGE_DB.exists():

        try:

            conn = sqlite3.connect(
                str(KNOWLEDGE_DB)
            )

            document_count = conn.execute(
                "SELECT COUNT(*) FROM documents"
            ).fetchone()[0]

            official_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM documents
                WHERE
                    LOWER(COALESCE(source_status,'')) 
                        IN ('official','verified')
                    AND LOWER(COALESCE(authority,'')) 
                        IN ('official','verified')
                    AND COALESCE(verified,0)=1
                """
            ).fetchone()[0]

            conn.close()

            conn_ok = True

        except Exception:
            conn_ok = False

    return {
        "status": "ok",
        "service": "Nusantara Master Engine Developer AI",
        "master_port": MASTER_PORT,
        "developer_core": developer,
        "ollama_available": bool(
            ollama.get("models") is not None
        ),
        "knowledge": {
            "database_exists": KNOWLEDGE_DB.exists(),
            "database_ok": conn_ok,
            "documents": document_count,
            "official_verified": official_count,
        },
    }


@app.post(
    "/v1/chat"
)
def chat(
    request: ChatRequest,
):

    return master_chat(
        request.input,
        request.model,
    )


@app.get(
    "/v1/knowledge/status"
)
def knowledge_status():

    if not KNOWLEDGE_DB.exists():

        return {
            "status": "missing",
            "database": str(
                KNOWLEDGE_DB
            ),
        }

    conn = sqlite3.connect(
        str(KNOWLEDGE_DB)
    )

    documents = conn.execute(
        """
        SELECT
            document_id,
            title,
            source_file,
            service,
            source_status,
            authority,
            verified,
            chunk_count
        FROM documents
        ORDER BY source_file
        """
    ).fetchall()

    conn.close()

    return {
        "status": "ok",
        "documents": [
            {
                "document_id": x[0],
                "title": x[1],
                "source_file": x[2],
                "service": x[3],
                "source_status": x[4],
                "authority": x[5],
                "verified": x[6],
                "chunk_count": x[7],
            }
            for x in documents
        ],
    }


# ============================================================
# LOCAL WEB UI
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse,
)
def web_ui():

    return """
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Nusantara Master Engine Developer AI</title>

<style>
body {
    font-family: Arial, sans-serif;
    max-width: 1100px;
    margin: 40px auto;
    padding: 0 20px;
    background: #f4f6f8;
}

h1 {
    margin-bottom: 5px;
}

textarea {
    width: 100%;
    height: 130px;
    padding: 15px;
    font-size: 16px;
    box-sizing: border-box;
}

button {
    margin-top: 12px;
    padding: 12px 24px;
    font-size: 16px;
    cursor: pointer;
}

pre {
    white-space: pre-wrap;
    background: white;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #ddd;
}

.status {
    margin-top: 20px;
    padding: 12px;
    background: white;
    border-radius: 8px;
}
</style>

</head>

<body>

<h1>Nusantara Master Engine Developer AI</h1>

<p>
Master Engine 8020 · Developer Core 8010 · Ollama · Production Knowledge
</p>

<textarea id="input"
placeholder="Contoh: Saya ingin membuat KTP-el pemula, apa persyaratannya?"></textarea>

<br>

<button onclick="send()">ASK NUSANTARA AI</button>

<div class="status" id="status">
Ready
</div>

<h2>Response</h2>

<pre id="output"></pre>

<script>

async function send() {

    const input =
        document.getElementById("input").value;

    document.getElementById("status").innerText =
        "Processing...";

    document.getElementById("output").innerText =
        "";

    try {

        const response =
            await fetch("/v1/chat", {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    input: input
                })
            });

        const data =
            await response.json();

        document.getElementById("output").innerText =
            JSON.stringify(
                data,
                null,
                2
            );

        document.getElementById("status").innerText =
            "Completed";

    } catch (error) {

        document.getElementById("status").innerText =
            "ERROR";

        document.getElementById("output").innerText =
            error.toString();
    }
}

</script>

</body>
</html>
"""


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print("=" * 70)
    print(" NUSANTARA MASTER ENGINE DEVELOPER AI")
    print("=" * 70)
    print("MASTER PORT       :", MASTER_PORT)
    print("DEVELOPER CORE    :", DEVELOPER_CORE_URL)
    print("OLLAMA            :", OLLAMA_URL)
    print("OLLAMA MODEL      :", OLLAMA_MODEL)
    print("KNOWLEDGE DB      :", KNOWLEDGE_DB)
    print("=" * 70)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=MASTER_PORT,
        log_level="info",
    )
