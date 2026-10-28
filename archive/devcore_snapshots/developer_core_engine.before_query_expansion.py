from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from typing import Any, Optional

import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


# ============================================================
# NUSANTARA DEVELOPER CORE ENGINE
# Grounded Chat + Authority + Grounding Guard + E2E
# ============================================================

ROOT = Path(__file__).resolve().parent

GRAPH_FILE = ROOT / "graphify-out" / "graph.json"

OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2:1b"

app = FastAPI(
    title="Nusantara Developer Core Engine",
    version="2.0.0",
    description=(
        "Local Developer Core dengan Graph RAG, Source RAG, "
        "Production Knowledge RAG, Authority dan Grounding Guard."
    ),
)


# ============================================================
# PRODUCTION RAG
# ============================================================

try:
    from app.knowledge.production_hybrid_rag import (
        ProductionHybridRAG,
    )
except Exception:
    ProductionHybridRAG = None


_production_rag = None


def get_production_rag():
    global _production_rag

    if ProductionHybridRAG is None:
        return None

    if _production_rag is None:
        try:
            _production_rag = ProductionHybridRAG()
        except Exception as exc:
            print(
                "[Production RAG] initialization failed:",
                exc,
            )
            _production_rag = None

    return _production_rag


# ============================================================
# GRAPH
# ============================================================

_GRAPH_CACHE: Optional[dict[str, Any]] = None


def load_graph() -> dict[str, Any]:
    global _GRAPH_CACHE

    if _GRAPH_CACHE is not None:
        return _GRAPH_CACHE

    if not GRAPH_FILE.exists():
        return {
            "nodes": [],
            "edges": [],
        }

    try:
        data = json.loads(
            GRAPH_FILE.read_text(
                encoding="utf-8-sig"
            )
        )

        if not isinstance(data, dict):
            data = {}

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        if not isinstance(nodes, list):
            nodes = []

        if not isinstance(edges, list):
            edges = []

        _GRAPH_CACHE = {
            "nodes": nodes,
            "edges": edges,
        }

        return _GRAPH_CACHE

    except Exception as exc:
        print(
            "[Graph] load failed:",
            exc,
        )

        return {
            "nodes": [],
            "edges": [],
        }


def search_graph(
    query: str,
    limit: int = 12,
) -> list[dict[str, Any]]:

    graph = load_graph()

    nodes = graph["nodes"]
    edges = graph["edges"]

    tokens = set(
        re.findall(
            r"[a-zA-Z0-9_]+",
            query.lower(),
        )
    )

    if not tokens:
        return []

    node_scores: dict[str, int] = {}

    for node in nodes:
        text = " ".join(
            str(node.get(key, ""))
            for key in (
                "id",
                "label",
                "source_file",
                "source_location",
                "file_type",
            )
        ).lower()

        score = sum(
            1
            for token in tokens
            if token in text
        )

        if score > 0:
            node_scores[
                str(node.get("id", ""))
            ] = score

    ranked_nodes = sorted(
        (
            (node_id, score)
            for node_id, score in node_scores.items()
        ),
        key=lambda x: x[1],
        reverse=True,
    )

    results: list[dict[str, Any]] = []

    node_map = {
        str(node.get("id", "")): node
        for node in nodes
    }

    for node_id, score in ranked_nodes[:limit]:
        node = node_map.get(node_id, {})

        results.append(
            {
                "type": "node",
                "id": node_id,
                "label": node.get(
                    "label",
                    node_id,
                ),
                "source_file": node.get(
                    "source_file",
                    "",
                ),
                "source_location": node.get(
                    "source_location",
                    "",
                ),
                "score": score,
            }
        )

    selected_ids = set(
        node_id
        for node_id, _ in ranked_nodes[:limit]
    )

    relationship_count = 0

    for edge in edges:

        source = str(
            edge.get("source", "")
        )

        target = str(
            edge.get("target", "")
        )

        if (
            source not in selected_ids
            and target not in selected_ids
        ):
            continue

        results.append(
            {
                "type": "relationship",
                "source": source,
                "target": target,
                "relation": edge.get(
                    "relation",
                    "",
                ),
                "context": edge.get(
                    "context",
                    "",
                ),
                "source_file": edge.get(
                    "source_file",
                    "",
                ),
                "source_location": edge.get(
                    "source_location",
                    "",
                ),
                "confidence": edge.get(
                    "confidence",
                    "",
                ),
            }
        )

        relationship_count += 1

        if relationship_count >= 30:
            break

    return results


# ============================================================
# SOURCE RAG
# ============================================================

EXCLUDED_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "backup",
    "backups",
    "research",
    "archive",
    "archives",
    "quarantine",
    "benchmark",
    "node_modules",
    "graphify-out",
    "dist",
    "build",
}

EXCLUDED_NAME_PARTS = {
    ".bak",
    ".backup",
    "backup_",
    "_backup",
    "before_",
    "_before_",
    "after_",
    "_after_",
    "patch_",
    "_patch",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
}


def collect_source_files() -> list[Path]:

    files: list[Path] = []

    for path in ROOT.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue

        relative_parts = {
            part.lower()
            for part in path.relative_to(ROOT).parts
        }

        if relative_parts.intersection(
            EXCLUDED_DIRS
        ):
            continue

        name = path.name.lower()

        if any(
            token in name
            for token in EXCLUDED_NAME_PARTS
        ):
            continue

        files.append(path)

    return files


def search_source(
    query: str,
    limit: int = 8,
) -> list[dict[str, Any]]:

    tokens = set(
        re.findall(
            r"[a-zA-Z0-9_]+",
            query.lower(),
        )
    )

    if not tokens:
        return []

    scored: list[tuple[int, Path]] = []

    for path in collect_source_files():

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        low = text.lower()

        score = sum(
            1
            for token in tokens
            if token in low
        )

        if score > 0:
            scored.append(
                (
                    score,
                    path,
                )
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    results: list[dict[str, Any]] = []

    for score, path in scored[:limit]:

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        # Jangan kirim source file terlalu besar ke model.
        if len(text) > 5000:
            text = text[:5000] + "\n...[TRUNCATED]"

        results.append(
            {
                "type": "source",
                "path": str(
                    path.relative_to(ROOT)
                ),
                "score": score,
                "content": text,
            }
        )

    return results


# ============================================================
# PRODUCTION KNOWLEDGE RAG
# ============================================================

AUTHORITY_LEVELS = {
    "official": 4,
    "verified": 3,
    "pending": 2,
    "unknown": 1,
    "expired": 0,
    "test": 0,
}


def normalize_authority(
    value: Any,
    text: str = "",
) -> str:

    raw = str(
        value or ""
    ).strip().lower()

    if raw in AUTHORITY_LEVELS:
        return raw

    combined = (
        raw
        + " "
        + text.lower()
    )

    # Fixture/test data harus selalu diperlakukan
    # sebagai non-authoritative.
    if (
        "test fixture" in combined
        or "data pengujian" in combined
        or "bukan sumber resmi" in combined
        or "test-" in combined
    ):
        return "test"

    return "unknown"


def object_to_dict(
    value: Any,
) -> Any:

    if value is None:
        return None

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            pass

    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return dict(
                value.__dict__
            )
        except Exception:
            pass

    return value


def normalize_production_pack(
    pack: Any,
) -> list[dict[str, Any]]:

    pack = object_to_dict(pack)

    if pack is None:
        return []

    if isinstance(pack, str):

        try:
            parsed = json.loads(pack)
            return normalize_production_pack(
                parsed
            )
        except Exception:
            return []

    if isinstance(pack, list):
        raw_items = pack

    elif isinstance(pack, dict):

        raw_items = None

        for key in (
            "evidence",
            "results",
            "items",
            "documents",
            "chunks",
        ):
            if isinstance(
                pack.get(key),
                list,
            ):
                raw_items = pack[key]
                break

        if raw_items is None:
            raw_items = []

    else:
        raw_items = []

    output: list[dict[str, Any]] = []

    for item in raw_items:

        item = object_to_dict(item)

        if not isinstance(item, dict):
            continue

        text = str(
            item.get("text")
            or item.get("chunk")
            or item.get("content")
            or ""
        ).strip()

        authority = normalize_authority(
            item.get("source_status")
            or item.get("authority")
            or item.get("status"),
            text,
        )

        normalized = {
            "chunk_id": item.get(
                "chunk_id"
            ),
            "document_id": item.get(
                "document_id"
            ),
            "title": item.get(
                "title"
            ),
            "service": item.get(
                "service"
            ),
            "content_type": item.get(
                "content_type"
            ),
            "text": text,
            "score": item.get(
                "score",
                0,
            ),
            "semantic_score": item.get(
                "semantic_score"
            ),
            "lexical_score": item.get(
                "lexical_score"
            ),
            "source_status": authority,
            "authority": authority,
            "source": item.get(
                "source"
            ),
            "url": item.get(
                "url"
            ),
        }

        output.append(normalized)

    return output



def search_production_knowledge(
    query: str,
    top_k: int = 5,
    service: str | None = None,
    content_type: str | None = None,
    require_authoritative_source: bool = False,
):
    """
    Production Knowledge adapter.

    Architectural contract
    ----------------------
    This function is the single bridge between Developer Core /v1/chat
    and the Production Knowledge subsystem.

    Responsibilities:
      1. Use the Production Hybrid RAG when available.
      2. Preserve authority/provenance metadata.
      3. Normalize multiple evidence-pack formats.
      4. Never manufacture evidence.
      5. Never promote test/unknown/pending/expired data to authoritative.
      6. Return [] when no usable Production evidence exists.

    It intentionally does NOT generate an answer.
    """

    if not query or not str(query).strip():
        return []

    query = str(query).strip()

    try:
        # ------------------------------------------------------------
        # Resolve Production RAG lazily.
        # ------------------------------------------------------------
        rag = None

        # Preferred: existing application-level factory/object.
        try:
            rag = get_production_rag()
        except Exception:
            rag = None

        # Fallback: construct the stable Production Hybrid RAG directly.
        if rag is None:
            try:
                from app.knowledge.production_hybrid_rag import (
                    ProductionHybridRAG,
                )
                rag = ProductionHybridRAG()
            except Exception:
                rag = None

        if rag is None:
            return []

        # ------------------------------------------------------------
        # Retrieval
        # ------------------------------------------------------------
        result = None

        retrieve = getattr(rag, "retrieve", None)

        if callable(retrieve):
            kwargs = {
                "top_k": max(1, int(top_k)),
            }

            if service:
                kwargs["service"] = service

            if content_type:
                kwargs["content_type"] = content_type

            if require_authoritative_source:
                kwargs["require_authoritative_source"] = True

            try:
                result = retrieve(query, **kwargs)
            except TypeError:
                # Compatibility with older retrieve() signatures.
                reduced_kwargs = {
                    "top_k": max(1, int(top_k)),
                }

                if service:
                    reduced_kwargs["service"] = service

                if content_type:
                    reduced_kwargs["content_type"] = content_type

                try:
                    result = retrieve(query, **reduced_kwargs)
                except TypeError:
                    result = retrieve(query, max(1, int(top_k)))

        # ------------------------------------------------------------
        # Compatibility: some implementations expose retrieve_json().
        # ------------------------------------------------------------
        if result is None:
            retrieve_json = getattr(rag, "retrieve_json", None)

            if callable(retrieve_json):
                try:
                    result = retrieve_json(
                        query,
                        top_k=max(1, int(top_k)),
                    )
                except TypeError:
                    result = retrieve_json(query)

        # ------------------------------------------------------------
        # Normalize evidence pack.
        # ------------------------------------------------------------
        if result is None:
            return []

        candidates = []

        if isinstance(result, list):
            candidates = result

        elif isinstance(result, tuple):
            candidates = list(result)

        elif isinstance(result, dict):
            for key in (
                "evidence",
                "results",
                "items",
                "matches",
                "documents",
                "chunks",
            ):
                value = result.get(key)
                if isinstance(value, list):
                    candidates = value
                    break

            if not candidates and result.get("text"):
                candidates = [result]

        else:
            for attr in (
                "evidence",
                "results",
                "items",
                "matches",
                "documents",
                "chunks",
            ):
                value = getattr(result, attr, None)

                if isinstance(value, list):
                    candidates = value
                    break

        # ------------------------------------------------------------
        # Normalize one evidence item.
        # ------------------------------------------------------------
        def get_value(item, *names, default=None):
            if isinstance(item, dict):
                for name in names:
                    if name in item and item[name] is not None:
                        return item[name]
                return default

            for name in names:
                value = getattr(item, name, None)
                if value is not None:
                    return value

            return default

        normalized = []

        for item in candidates:
            if item is None:
                continue

            text_value = get_value(
                item,
                "text",
                "content",
                "chunk_text",
                "page_content",
                default="",
            )

            if not text_value:
                continue

            metadata = get_value(
                item,
                "metadata",
                default={},
            )

            if not isinstance(metadata, dict):
                metadata = {}

            source_status = get_value(
                item,
                "source_status",
                default=None,
            )

            authority = get_value(
                item,
                "authority",
                default=None,
            )

            service_value = get_value(
                item,
                "service",
                default=None,
            )

            content_type_value = get_value(
                item,
                "content_type",
                default=None,
            )

            source_name = get_value(
                item,
                "source_name",
                "source_file",
                default=None,
            )

            source_id = get_value(
                item,
                "source_id",
                "document_id",
                default=None,
            )

            chunk_id = get_value(
                item,
                "chunk_id",
                default=None,
            )

            source_url = get_value(
                item,
                "source_url",
                "url",
                default=None,
            )

            score = get_value(
                item,
                "score",
                "relevance_score",
                default=0.0,
            )

            semantic_score = get_value(
                item,
                "semantic_score",
                default=None,
            )

            lexical_score = get_value(
                item,
                "lexical_score",
                default=None,
            )

            # Metadata hydration fallback.
            source_status = (
                source_status
                if source_status is not None
                else metadata.get("source_status")
            )

            authority = (
                authority
                if authority is not None
                else metadata.get("authority")
            )

            service_value = (
                service_value
                if service_value is not None
                else metadata.get("service")
            )

            content_type_value = (
                content_type_value
                if content_type_value is not None
                else metadata.get("content_type")
            )

            source_name = (
                source_name
                if source_name is not None
                else metadata.get("source_name")
            )

            source_id = (
                source_id
                if source_id is not None
                else metadata.get("document_id")
            )

            chunk_id = (
                chunk_id
                if chunk_id is not None
                else metadata.get("chunk_id")
            )

            source_url = (
                source_url
                if source_url is not None
                else metadata.get("source_url")
            )

            # --------------------------------------------------------
            # Governance:
            # only OFFICIAL / VERIFIED may be authoritative.
            # --------------------------------------------------------
            status = str(source_status or "").strip().lower()
            auth = str(authority or "").strip().lower()

            authoritative = (
                status in {"official", "verified"}
                or auth in {"official", "verified"}
            )

            # Test/unknown/pending/expired can NEVER become authoritative.
            if status in {
                "test",
                "unknown",
                "pending",
                "expired",
            }:
                authoritative = False

            if auth in {
                "test",
                "unknown",
                "pending",
                "expired",
            }:
                authoritative = False

            metadata = dict(metadata)

            metadata.update(
                {
                    "source_status": source_status,
                    "authority": authority,
                    "service": service_value,
                    "content_type": content_type_value,
                    "source_name": source_name,
                    "source_id": source_id,
                    "chunk_id": chunk_id,
                    "source_url": source_url,
                    "semantic_score": semantic_score,
                    "lexical_score": lexical_score,
                    "authoritative": authoritative,
                }
            )

            normalized.append(
                {
                    "text": str(text_value),
                    "score": float(score or 0.0),
                    "semantic_score": semantic_score,
                    "lexical_score": lexical_score,
                    "source_id": source_id,
                    "source_name": source_name,
                    "source_status": source_status,
                    "authority": authority,
                    "service": service_value,
                    "content_type": content_type_value,
                    "source_url": source_url,
                    "chunk_id": chunk_id,
                    "authoritative": authoritative,
                    "metadata": metadata,
                }
            )

        # ------------------------------------------------------------
        # Optional authoritative filtering.
        # ------------------------------------------------------------
        if require_authoritative_source:
            normalized = [
                item
                for item in normalized
                if item["authoritative"]
            ]

        # ------------------------------------------------------------
        # Stable ranking.
        # ------------------------------------------------------------
        normalized.sort(
            key=lambda item: (
                1 if item["authoritative"] else 0,
                float(item["score"] or 0.0),
            ),
            reverse=True,
        )

        return normalized[: max(1, int(top_k))]

    except Exception as exc:
        # Production retrieval must fail closed.
        #
        # Do not return fabricated evidence and do not allow an
        # infrastructure error to silently become an authoritative
        # answer.
        print(
            "[Production RAG] retrieval error:",
            repr(exc),
        )
        return []

def split_authority(
    evidence: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:

    official = []
    verified = []
    non_authoritative = []

    for item in evidence:

        authority = normalize_authority(
            item.get("authority"),
            item.get("text", ""),
        )

        item["authority"] = authority
        item["source_status"] = authority

        if authority == "official":
            official.append(item)

        elif authority == "verified":
            verified.append(item)

        else:
            non_authoritative.append(item)

    return {
        "official": official,
        "verified": verified,
        "non_authoritative": non_authoritative,
    }


def authority_summary(
    groups: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:

    official = groups["official"]
    verified = groups["verified"]
    non_authoritative = groups[
        "non_authoritative"
    ]

    if official:
        level = "OFFICIAL"

    elif verified:
        level = "VERIFIED"

    elif non_authoritative:
        level = "NON_AUTHORITATIVE"

    else:
        level = "NO_EVIDENCE"

    return {
        "level": level,
        "official_count": len(official),
        "verified_count": len(verified),
        "non_authoritative_count": len(
            non_authoritative
        ),
        "grounding_allowed": bool(
            official or verified
        ),
    }


# ============================================================
# EVIDENCE BUILDER
# ============================================================

def build_grounding_context(
    query: str,
    graph: list[dict[str, Any]],
    source: list[dict[str, Any]],
    production: list[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:

    groups = split_authority(
        production
    )

    summary = authority_summary(
        groups
    )

    lines: list[str] = []

    lines.append(
        "=== NUSANTARA DEVELOPER CORE EVIDENCE ==="
    )

    lines.append(
        f"QUERY: {query}"
    )

    lines.append("")

    lines.append(
        "=== GRAPH RAG ==="
    )

    for item in graph:

        if item.get("type") == "node":

            lines.append(
                "- NODE: "
                + str(
                    item.get("label", "")
                )
                + " | file="
                + str(
                    item.get("source_file", "")
                )
                + " | score="
                + str(
                    item.get("score", "")
                )
            )

        elif item.get(
            "type"
        ) == "relationship":

            lines.append(
                "- RELATION: "
                + str(
                    item.get("source", "")
                )
                + " --"
                + str(
                    item.get("relation", "")
                )
                + "--> "
                + str(
                    item.get("target", "")
                )
            )

    lines.append("")

    lines.append(
        "=== SOURCE RAG ==="
    )

    for item in source:

        lines.append(
            "- FILE: "
            + str(
                item.get("path", "")
            )
            + " | score="
            + str(
                item.get("score", "")
            )
        )

        content = str(
            item.get("content", "")
        )

        lines.append(
            content[:2500]
        )

    lines.append("")

    lines.append(
        "=== PRODUCTION KNOWLEDGE AUTHORITY ==="
    )

    lines.append(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )

    # HANYA official/verified menjadi
    # grounding evidence untuk jawaban.
    authoritative = (
        groups["official"]
        + groups["verified"]
    )

    if authoritative:

        lines.append("")

        lines.append(
            "=== AUTHORITATIVE KNOWLEDGE ==="
        )

        for index, item in enumerate(
            authoritative,
            start=1,
        ):

            lines.append(
                f"[AUTHORITY {index}]"
            )

            lines.append(
                "Authority: "
                + str(
                    item.get(
                        "authority"
                    )
                )
            )

            lines.append(
                "Service: "
                + str(
                    item.get(
                        "service"
                    )
                )
            )

            lines.append(
                "Title: "
                + str(
                    item.get(
                        "title"
                    )
                )
            )

            lines.append(
                "Text: "
                + str(
                    item.get(
                        "text"
                    )
                )[:4000]
            )

    else:

        lines.append("")

        lines.append(
            "=== AUTHORITATIVE KNOWLEDGE ==="
        )

        lines.append(
            "TIDAK ADA SUMBER OFFICIAL/VERIFIED."
        )

        lines.append(
            "Jangan membuat klaim pelayanan resmi."
        )

    return (
        "\n".join(lines),
        summary,
    )


# ============================================================
# OLLAMA
# ============================================================

def ollama_available() -> bool:

    try:
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5,
        )

        return response.ok

    except Exception:
        return False


def ollama_generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
) -> str:

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.8,
            "num_predict": 700,
        },
    }

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    return str(
        data.get(
            "response",
            "",
        )
    ).strip()


# ============================================================
# GROUNDING GUARD
# ============================================================

STOPWORDS = {
    "yang",
    "dan",
    "atau",
    "untuk",
    "dari",
    "dengan",
    "pada",
    "dalam",
    "adalah",
    "ini",
    "itu",
    "sebagai",
    "ke",
    "di",
    "apa",
    "saya",
    "anda",
    "bisa",
    "dapat",
    "akan",
    "jika",
    "tidak",
    "ada",
    "the",
    "and",
    "for",
    "from",
    "with",
}


def content_tokens(
    text: str,
) -> set[str]:

    words = re.findall(
        r"[a-zA-Z0-9_-]+",
        text.lower(),
    )

    return {
        word
        for word in words
        if len(word) >= 3
        and word not in STOPWORDS
    }



# ============================================================
# HARD GROUNDING GATE
# ============================================================

# ============================================================
# QUERY DOMAIN CLASSIFIER
# ============================================================

SERVICE_QUERY_TERMS = [
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
    "datang",
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

DEVELOPER_QUERY_TERMS = [
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
]

def classify_query_domain(query: str) -> str:
    """
    Menentukan jalur retrieval berdasarkan isi pertanyaan.

    service   -> Production Knowledge + Authority Engine
    developer -> Graph RAG + Source RAG
    general   -> Production Knowledge
    """
    text = (query or "").strip().lower()

    if any(term in text for term in DEVELOPER_QUERY_TERMS):
        return "developer"

    if any(term in text for term in SERVICE_QUERY_TERMS):
        return "service"

    return "general"

def hard_grounding_gate(
    query: str,
    query_domain: str,
    authority: dict[str, Any],
) -> dict[str, Any]:
    """
    Menentukan apakah Ollama boleh menghasilkan jawaban final.

    SERVICE:
        Hanya OFFICIAL / VERIFIED yang boleh menjadi dasar
        jawaban pelayanan.

    DEVELOPER:
        Graph/Source RAG boleh digunakan.

    GENERAL:
        Production Knowledge digunakan sebagai sumber utama.
    """

    official_count = int(
        authority.get("official_count", 0) or 0
    )

    verified_count = int(
        authority.get("verified_count", 0) or 0
    )

    authoritative_count = (
        official_count + verified_count
    )

    if query_domain == "service":

        if authoritative_count <= 0:
            return {
                "allowed": False,
                "reason": "no_authoritative_service_evidence",
                "message": (
                    "Informasi resmi atau sumber terverifikasi "
                    "untuk pertanyaan pelayanan belum ditemukan. "
                    "Jawaban tidak dibuat berdasarkan asumsi model."
                ),
            }

        return {
            "allowed": True,
            "reason": "authoritative_service_evidence_available",
            "message": None,
        }

    if query_domain == "developer":
        return {
            "allowed": True,
            "reason": "developer_query",
            "message": None,
        }

    if authoritative_count > 0:
        return {
            "allowed": True,
            "reason": "authoritative_general_evidence_available",
            "message": None,
        }

    return {
        "allowed": False,
        "reason": "no_authoritative_general_evidence",
        "message": (
            "Belum ditemukan sumber pengetahuan resmi atau "
            "terverifikasi yang cukup untuk menjawab pertanyaan."
        ),
    }


def grounding_guard(
    query: str,
    answer: str,
    authoritative_evidence: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    if not answer.strip():

        return {
            "status": "UNSUPPORTED",
            "supported": False,
            "score": 0.0,
            "reason": "Jawaban kosong.",
        }

    evidence_text = " ".join(
        str(
            item.get(
                "text",
                "",
            )
        )
        for item in authoritative_evidence
    )

    # Tidak ada sumber authoritative:
    # model tidak boleh dianggap grounded.
    if not evidence_text.strip():

        return {
            "status": "UNSUPPORTED",
            "supported": False,
            "score": 0.0,
            "reason": (
                "Tidak tersedia evidence "
                "official/verified."
            ),
        }

    evidence_tokens = content_tokens(
        evidence_text
    )

    answer_sentences = [
        sentence.strip()
        for sentence in re.split(
            r"[.!?\n]+",
            answer,
        )
        if sentence.strip()
    ]

    if not answer_sentences:

        return {
            "status": "UNSUPPORTED",
            "supported": False,
            "score": 0.0,
            "reason": "Tidak ada kalimat jawaban.",
        }

    scores: list[float] = []

    for sentence in answer_sentences:

        tokens = content_tokens(
            sentence
        )

        if not tokens:
            continue

        overlap = tokens.intersection(
            evidence_tokens
        )

        score = len(overlap) / max(
            len(tokens),
            1,
        )

        scores.append(score)

    if not scores:

        score = 0.0

    else:

        score = sum(scores) / len(
            scores
        )

    if score >= 0.35:

        status = "GROUNDED"
        supported = True

    elif score >= 0.15:

        status = "PARTIAL"
        supported = False

    else:

        status = "UNSUPPORTED"
        supported = False

    return {
        "status": status,
        "supported": supported,
        "score": round(
            score,
            4,
        ),
        "reason": (
            "Perbandingan token jawaban "
            "dengan authoritative evidence."
        ),
    }


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):

    input: str = Field(
        min_length=1,
    )

    model: str = DEFAULT_MODEL

    use_graph: bool = True

    use_source: bool = True

    use_production: bool = True


# ============================================================
# HEALTH
# ============================================================

@app.get("/v1/developer/health")
def developer_health():

    graph = load_graph()

    return {
        "status": "ok",
        "service": (
            "Nusantara Developer Core"
        ),
        "graph": {
            "nodes": len(
                graph["nodes"]
            ),
            "edges": len(
                graph["edges"]
            ),
            "graph_file": str(
                GRAPH_FILE
            ),
            "graph_exists": (
                GRAPH_FILE.exists()
            ),
        },
        "production_rag": (
            get_production_rag()
            is not None
        ),
        "ollama": OLLAMA_URL,
        "ollama_available": (
            ollama_available()
        ),
    }


# ============================================================
# GRAPH API
# ============================================================

@app.get("/v1/graph/summary")
def graph_summary():

    graph = load_graph()

    return {
        "nodes": len(
            graph["nodes"]
        ),
        "edges": len(
            graph["edges"]
        ),
        "graph_file": str(
            GRAPH_FILE
        ),
    }


@app.get("/v1/graph/search")
def graph_search_api(
    q: str = Query(...),
    limit: int = 12,
):

    return {
        "query": q,
        "results": search_graph(
            q,
            limit,
        ),
    }


# ============================================================
# RAG CONTEXT
# ============================================================

@app.get("/v1/rag/context")
def rag_context_api(
    q: str = Query(...),
):

    graph = search_graph(
        q,
        12,
    )

    source = search_source(
        q,
        6,
    )

    production = search_production_knowledge(
        q,
        5,
    )

    context, authority = (
        build_grounding_context(
            q,
            graph,
            source,
            production,
        )
    )

    return {
        "query": q,
        "graph": graph,
        "source": source,
        "production_knowledge": production,
        "authority": authority,
        "context": context,
    }


# ============================================================
# GROUNDED CHAT
# ============================================================

@app.post("/v1/chat")
def developer_chat(
    request: ChatRequest,
):

    query = request.input.strip()
    # ========================================================
    # QUERY DOMAIN
    # ========================================================
    # WAJIB dibuat setelah query tersedia.
    # Seluruh pipeline /v1/chat menggunakan nilai ini.
    query_domain = classify_query_domain(query)


    if not query:
        raise HTTPException(
            status_code=400,
            detail="Input kosong.",
        )

    # --------------------------------------------------------
    # RETRIEVAL
    # --------------------------------------------------------

    graph = []

    source = []

    production = []

    if request.use_graph:
        graph = search_graph(
            query,
            12,
        )

    if request.use_source:
        source = search_source(
            query,
            6,
        )

    if request.use_production:
        production = search_production_knowledge(
            query,
            5,
        )

    # --------------------------------------------------------
    # AUTHORITY
    # --------------------------------------------------------

    context, authority = (
        build_grounding_context(
            query,
            graph,
            source,
            production,
        )
    )

    groups = split_authority(
        production
    )

    authoritative = (
        groups["official"]
        + groups["verified"]
    )

    # --------------------------------------------------------
    # GROUNDED PROMPT
    # --------------------------------------------------------

    prompt = f"""
Anda adalah Nusantara Developer Core Engine.

Anda adalah AI engineering assistant lokal.

PERTANYAAN USER:
{query}

ATURAN UTAMA:

1. Gunakan evidence yang tersedia.
2. Jangan mengarang file, class, function,
   dependency, workflow, aturan, persyaratan,
   angka atau fakta yang tidak didukung evidence.
3. Production Knowledge dengan authority
   OFFICIAL atau VERIFIED adalah sumber
   authoritative.
4. TEST, UNKNOWN, PENDING dan EXPIRED
   bukan sumber authoritative.
5. Jika tidak ada authoritative evidence,
   katakan dengan jelas bahwa sumber resmi/
   terverifikasi tidak tersedia.
6. Graph RAG dan Source RAG digunakan untuk
   memahami struktur Developer Core.
7. Jangan mengubah evidence menjadi fakta
   resmi apabila evidence tersebut hanya
   merupakan data pengujian.
8. Jawab dalam Bahasa Indonesia.
9. Bedakan fakta yang didukung evidence
   dengan inferensi.
10. Jangan membuat jawaban hanya karena
    model mengetahui informasi umum dari
    training-nya. Prioritaskan evidence.

AUTHORITY SUMMARY:
{json.dumps(authority, ensure_ascii=False, indent=2)}

AUTHORITATIVE EVIDENCE:
{json.dumps(authoritative, ensure_ascii=False, indent=2)}

DEVELOPER CORE CONTEXT:
{context}

FORMAT JAWABAN:

Berikan jawaban langsung terhadap pertanyaan.

Jika authoritative evidence tersedia,
gunakan evidence tersebut.

Jika authoritative evidence tidak tersedia,
katakan bahwa informasi belum dapat
diverifikasi dari sumber authoritative
yang tersedia.

Jangan mengklaim sesuatu sebagai sumber
resmi jika evidence tidak menyatakannya.
"""

    # --------------------------------------------------------
    # HARD GROUNDING GATE
    # --------------------------------------------------------
    #
    # SERVICE QUERY:
    #   hanya OFFICIAL / VERIFIED yang boleh diteruskan
    #   ke Ollama.
    #
    # Jika tidak ada authoritative evidence:
    #   Ollama TIDAK dipanggil.
    #
    # DEVELOPER QUERY:
    #   tetap boleh menggunakan Graph RAG + Source RAG.
    # --------------------------------------------------------

    grounding_gate = hard_grounding_gate(
        query=query,
        query_domain=query_domain,
        authority=authority,
    )

    if not grounding_gate["allowed"]:
        return {
            "input": query,
            "model": request.model,
            "query_domain": query_domain,
            "answer": grounding_gate["message"],
            "response": grounding_gate["message"],
            "grounding_gate": grounding_gate,
            "authority": authority,
            "grounding_guard": {
                "status": "BLOCKED",
                "reason": grounding_gate["reason"],
            },
            "evidence": {
                "graph": graph,
                "source": source,
                "production": production,
            },
        }

    # --------------------------------------------------------
    # OLLAMA
    # --------------------------------------------------------

    try:

        answer = ollama_generate(
            prompt,
            request.model,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Ollama gagal memberikan jawaban: "
                + str(exc)
            ),
        )

    # --------------------------------------------------------
    # GROUNDING GUARD
    # --------------------------------------------------------

    guard = grounding_guard(
        query,
        answer,
        authoritative,
    )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "input": query,
        "model": request.model,

        "graph_enabled": (
            request.use_graph
        ),

        "source_enabled": (
            request.use_source
        ),

        "production_enabled": (
            request.use_production
        ),

        "authority": authority,

        "grounding_guard": guard,

        "evidence": {
            "graph": graph,
            "source": source,
            "production": production,
        },

        "context": context,

        "output": answer,
    }


# ============================================================
# SELF ANALYSIS
# ============================================================

@app.get("/v1/self-analysis")
def self_analysis():

    graph = load_graph()

    source_files = collect_source_files()

    production = get_production_rag()

    production_stats = None

    if production is not None:

        try:
            production_stats = (
                production.database_stats()
            )
        except Exception:
            production_stats = None

    return {
        "service": (
            "Nusantara Developer Core"
        ),
        "graph": {
            "nodes": len(
                graph["nodes"]
            ),
            "edges": len(
                graph["edges"]
            ),
        },
        "source_files": len(
            source_files
        ),
        "production_database": (
            production_stats
        ),
        "ollama": {
            "url": OLLAMA_URL,
            "available": (
                ollama_available()
            ),
        },
    }


# ============================================================
# WATCHER
# ============================================================

def watcher():

    previous_mtime = None

    while True:

        try:

            if GRAPH_FILE.exists():

                current_mtime = (
                    GRAPH_FILE.stat().st_mtime
                )

                if (
                    previous_mtime is not None
                    and current_mtime
                    != previous_mtime
                ):
                    global _GRAPH_CACHE
                    _GRAPH_CACHE = None

                    print(
                        "[Developer Core] "
                        "Graph berubah. Cache "
                        "dihapus."
                    )

                previous_mtime = (
                    current_mtime
                )

        except Exception as exc:

            print(
                "[Developer Core] "
                "Watcher error:",
                exc,
            )

        time.sleep(15)


# ============================================================
# STARTUP
# ============================================================

def startup():

    print("")
    print("=" * 64)
    print(" NUSANTARA DEVELOPER CORE ENGINE")
    print("=" * 64)
    print("Graph RAG              : ENABLED")
    print("Source RAG             : ENABLED")
    print("Production Knowledge   : ENABLED")
    print("Authority Engine       : ENABLED")
    print("Grounding Guard        : ENABLED")
    print("Grounded Chat         : ENABLED")
    print("Ollama                 : ENABLED")
    print("=" * 64)

    graph = load_graph()

    print(
        "[Developer Core] Graph nodes:",
        len(graph["nodes"]),
    )

    print(
        "[Developer Core] Graph edges:",
        len(graph["edges"]),
    )

    print(
        "[Developer Core] Production RAG:",
        get_production_rag()
        is not None,
    )

    print(
        "[Developer Core] Ollama:",
        OLLAMA_URL,
    )

    print(
        "[Developer Core] Watcher aktif "
        "setiap 15 detik."
    )

    thread = threading.Thread(
        target=watcher,
        daemon=True,
        name="developer-core-watcher",
    )

    thread.start()


startup()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8010,
        log_level="info",
    )


