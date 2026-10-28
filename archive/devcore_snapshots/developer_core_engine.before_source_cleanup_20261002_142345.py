from pathlib import Path
import json
import re
import subprocess
import sys
import time
import threading
import hashlib
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

try:
    from app.knowledge.production_hybrid_rag import ProductionHybridRAG
except Exception:
    ProductionHybridRAG = None


ROOT = Path(r"C:\Users\dmaza\mcp-starter")
GRAPH_DIR = ROOT / "graphify-out"
GRAPH_FILE = GRAPH_DIR / "graph.json"
SOURCE_DIRS = [
    ROOT / "app",
    ROOT / "config",
    ROOT / "scripts",
    ROOT / "tests",
]

ANALYSIS_FILES = {
    "architecture": GRAPH_DIR / "architecture.json",
    "dependency": GRAPH_DIR / "dependency.json",
    "workflow": GRAPH_DIR / "workflow.json",
    "impact": GRAPH_DIR / "impact.json",
    "candidates": GRAPH_DIR / "candidates.json",
    "engine_summary": GRAPH_DIR / "engine_summary.json",
    "report": GRAPH_DIR / "graph_report.json",
}

INDEX_FILE = GRAPH_DIR / "source_index.json"
STATE_FILE = GRAPH_DIR / "developer_core_state.json"

_lock = threading.RLock()
_cache = {}
_file_hashes = {}

# Production Knowledge RAG
_production_rag = None



def load_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def load_graph():
    with _lock:
        if "graph" not in _cache:
            _cache["graph"] = load_json(
                GRAPH_FILE,
                {"nodes": [], "edges": []}
            )
        return _cache["graph"]


def invalidate_cache():
    with _lock:
        _cache.clear()


def node_id(node):
    return str(
        node.get("id")
        or node.get("key")
        or node.get("name")
        or ""
    )


def node_name(node):
    return str(
        node.get("name")
        or node.get("label")
        or node.get("path")
        or node_id(node)
    )


def node_text(node):
    return " ".join(
        str(node.get(k, ""))
        for k in [
            "id",
            "name",
            "label",
            "path",
            "type",
            "engine",
            "role",
            "file",
            "module",
        ]
    ).lower()



def get_production_rag():
    """
    Lazy loader untuk Production Hybrid RAG.

    Tidak membuat Production RAG wajib tersedia agar
    Developer Core tetap dapat berjalan apabila dependency
    semantic retrieval belum siap.
    """
    global _production_rag

    if ProductionHybridRAG is None:
        return None

    if _production_rag is None:
        try:
            _production_rag = ProductionHybridRAG()
        except Exception:
            _production_rag = None

    return _production_rag


def search_production_knowledge(
    query: str,
    top_k: int = 5,
    intent_name: str | None = None,
):
    """
    Mengambil evidence dari Production Hybrid RAG.

    Output dibuat menjadi dictionary sederhana agar aman
    digabungkan dengan Graph RAG dan Source RAG.
    """

    rag = get_production_rag()

    if rag is None:
        return []

    try:
        if not rag.database_exists():
            return []

        pack = rag.retrieve_for_intent(
            query=query,
            intent_name=intent_name,
            top_k=top_k,
        )

        results = []

        evidence_items = getattr(
            pack,
            "evidence",
            None,
        )

        if evidence_items is None:
            evidence_items = getattr(
                pack,
                "items",
                [],
            )

        for item in evidence_items or []:

            if isinstance(item, dict):
                data = item
            else:
                data = {
                    "chunk_id": getattr(
                        item,
                        "chunk_id",
                        None,
                    ),
                    "document_id": getattr(
                        item,
                        "document_id",
                        None,
                    ),
                    "text": getattr(
                        item,
                        "text",
                        None,
                    ),
                    "chunk": getattr(
                        item,
                        "text",
                        None,
                    ),
                    "score": getattr(
                        item,
                        "score",
                        None,
                    ),
                    "semantic_score": getattr(
                        item,
                        "semantic_score",
                        None,
                    ),
                    "lexical_score": getattr(
                        item,
                        "lexical_score",
                        None,
                    ),
                    "source": getattr(
                        item,
                        "source",
                        None,
                    ),
                    "title": getattr(
                        item,
                        "title",
                        None,
                    ),
                    "authority": getattr(
                        item,
                        "authority",
                        None,
                    ),
                    "url": getattr(
                        item,
                        "url",
                        None,
                    ),
                    "content_type": getattr(
                        item,
                        "content_type",
                        None,
                    ),
                    "service": getattr(
                        item,
                        "service",
                        None,
                    ),
                    "source_status": getattr(
                        item,
                        "source_status",
                        None,
                    ),
                }

            text_value = (
                data.get("text")
                or data.get("chunk")
                or data.get("content")
                or ""
            )

            if not str(text_value).strip():
                continue

            results.append(
                {
                    "type": "production_knowledge",
                    "chunk_id": data.get("chunk_id"),
                    "document_id": data.get("document_id"),
                    "title": data.get("title"),
                    "text": str(text_value).strip(),
                    "chunk": str(text_value).strip(),
                    "score": data.get("score"),
                    "semantic_score": data.get(
                        "semantic_score"
                    ),
                    "lexical_score": data.get(
                        "lexical_score"
                    ),
                    "source": data.get("source"),
                    "authority": data.get("authority"),
                    "url": data.get("url"),
                    "content_type": data.get(
                        "content_type"
                    ),
                    "service": data.get("service"),
                    "source_status": data.get(
                        "source_status"
                    ),
                }
            )

        return results

    except Exception as exc:

        print(
            "[Production RAG] retrieval failed:",
            exc,
        )

        return []


def build_production_evidence_text(
    results,
) -> str:

    if not results:
        return ""

    lines = []

    for index, item in enumerate(
        results,
        start=1,
    ):

        lines.append(
            f"[PRODUCTION KNOWLEDGE {index}]"
        )

        if item.get("title"):
            lines.append(
                f"Title: {item['title']}"
            )

        if item.get("service"):
            lines.append(
                f"Service: {item['service']}"
            )

        if item.get("content_type"):
            lines.append(
                f"Content Type: {item['content_type']}"
            )

        if item.get("source_status"):
            lines.append(
                f"Source Status: {item['source_status']}"
            )

        if item.get("authority") is not None:
            lines.append(
                f"Authority: {item['authority']}"
            )

        if item.get("source"):
            lines.append(
                f"Source: {item['source']}"
            )

        if item.get("score") is not None:
            lines.append(
                f"Score: {item['score']}"
            )

        lines.append(
            f"Text: {item.get('text', '')}"
        )

        lines.append("")

    return "\n".join(lines).strip()


def graph_summary():
    graph = load_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    valid_nodes = {
        node_id(n)
        for n in nodes
        if node_id(n)
    }

    valid_edges = 0
    invalid_edges = 0

    for e in edges:
        s = str(e.get("source", e.get("from", "")))
        t = str(e.get("target", e.get("to", "")))

        if s in valid_nodes and t in valid_nodes:
            valid_edges += 1
        else:
            invalid_edges += 1

    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "valid_edges": valid_edges,
        "invalid_edges": invalid_edges,
        "graph_file": str(GRAPH_FILE),
        "graph_exists": GRAPH_FILE.exists(),
    }


def search_graph(query: str, limit: int = 10):
    """
    Graph RAG v2.

    Menggunakan:
    - Graphify nodes
    - Graphify edges
    - semantic token matching sederhana
    - 1-hop relationship traversal

    Output dinormalisasi agar dapat digunakan oleh
    build_graph_context().
    """

    import json
    import re

    graph_path = ROOT / "graphify-out" / "graph.json"

    if not graph_path.exists():
        return []

    try:
        data = json.loads(
            graph_path.read_text(encoding="utf-8")
        )
    except Exception:
        return []

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    blocked_tokens = {
        "any",
        "path",
        "dict",
        "list",
        "tuple",
        "set",
        "str",
        "int",
        "float",
        "bool",
        "object",
        "typing",
        "datetime",
        "json",
        "os",
        "sys",
        "re",
        "fastapi",
        "pydantic",
    }

    blocked_path_tokens = {
        "backup",
        "before_openrouter",
        "after_openrouter",
        "__pycache__",
        ".venv",
        "research",
        "archive",
        "quarantine",
        "benchmark",
    }

    def blocked_path(path):
        p = str(path or "").lower()

        return any(
            token in p
            for token in blocked_path_tokens
        )

    def tokenize(value):
        return {
            token
            for token in re.findall(
                r"[a-zA-Z0-9_]+",
                str(value or "").lower()
            )
            if len(token) >= 3
        }

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    node_map = {}

    for node in nodes:

        node_id = str(
            node.get("id") or ""
        )

        if not node_id:
            continue

        source_file = str(
            node.get("source_file") or ""
        )

        label = str(
            node.get("label") or ""
        )

        if blocked_path(source_file):
            continue

        if label.lower() in blocked_tokens:
            continue

        node_map[node_id] = node

    candidates = []

    for node_id, node in node_map.items():

        label = str(
            node.get("label") or ""
        )

        source_file = str(
            node.get("source_file") or ""
        )

        source_location = str(
            node.get("source_location") or ""
        )

        file_type = str(
            node.get("file_type") or ""
        )

        searchable = " ".join(
            [
                label,
                source_file,
                source_location,
                node_id,
            ]
        ).lower()

        node_tokens = tokenize(searchable)

        overlap = query_tokens.intersection(
            node_tokens
        )

        if not overlap:
            continue

        score = (
            len(overlap) * 100
        )

        if label.lower() in query_tokens:
            score += 300

        if source_file.lower().startswith("app/"):
            score += 50

        if file_type == "code":
            score += 20

        if file_type == "rationale":
            score += 5

        candidates.append(
            {
                "id": node_id,
                "name": label,
                "label": label,
                "path": source_file,
                "source_file": source_file,
                "source_location": source_location,
                "type": file_type,
                "origin": str(
                    node.get("_origin") or ""
                ),
                "score": score,
            }
        )

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    candidates = candidates[:limit]

    candidate_ids = {
        item["id"]
        for item in candidates
    }

    relationships = []

    for edge in edges:

        source = str(
            edge.get("source") or ""
        )

        target = str(
            edge.get("target") or ""
        )

        if (
            source not in node_map
            and source not in candidate_ids
        ):
            continue

        if (
            target not in node_map
            and target not in candidate_ids
        ):
            continue

        if (
            source in candidate_ids
            or target in candidate_ids
        ):

            relation = str(
                edge.get("relation") or ""
            )

            source_node = node_map.get(source, {})
            target_node = node_map.get(target, {})

            relationships.append(
                {
                    "source": source,
                    "target": target,
                    "source_name": str(
                        source_node.get("label") or source
                    ),
                    "target_name": str(
                        target_node.get("label") or target
                    ),
                    "source_file": str(
                        source_node.get("source_file") or
                        edge.get("source_file") or ""
                    ),
                    "target_file": str(
                        target_node.get("source_file") or ""
                    ),
                    "relation": relation,
                    "context": str(
                        edge.get("context") or ""
                    ),
                    "source_location": str(
                        edge.get("source_location") or
                        edge.get("source_location") or ""
                    ),
                    "weight": edge.get("weight", 1.0),
                }
            )

    relationship_seen = set()
    clean_relationships = []

    for item in relationships:

        key = (
            item["source"],
            item["target"],
            item["relation"],
        )

        if key in relationship_seen:
            continue

        relationship_seen.add(key)
        clean_relationships.append(item)

    clean_relationships.sort(
        key=lambda x: (
            x["source_name"],
            x["relation"],
            x["target_name"],
        )
    )

    result = []

    for item in candidates:
        result.append(item)

    for rel in clean_relationships[:30]:

        result.append(
            {
                "id": (
                    f"edge:"
                    f"{rel['source']}:"
                    f"{rel['target']}:"
                    f"{rel['relation']}"
                ),
                "name": (
                    f"{rel['source_name']} "
                    f"--{rel['relation']}--> "
                    f"{rel['target_name']}"
                ),
                "label": rel["relation"],
                "path": rel["source_file"],
                "source_file": rel["source_file"],
                "source_location": rel["source_location"],
                "type": "relationship",
                "origin": "graphify",
                "score": 50,
                "relation": rel["relation"],
                "source_node": rel["source"],
                "target_node": rel["target"],
                "target_file": rel["target_file"],
            }
        )

    return result[: max(limit, 10) + 30]



def get_node(node_identifier: str):
    graph = load_graph()

    for n in graph.get("nodes", []):
        if node_id(n) == node_identifier:
            return n

    return None


def node_dependencies(node_identifier: str):
    graph = load_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_map = {
        node_id(n): n
        for n in nodes
        if node_id(n)
    }

    incoming = []
    outgoing = []

    for e in edges:
        s = str(e.get("source", e.get("from", "")))
        t = str(e.get("target", e.get("to", "")))

        if s == node_identifier and t in node_map:
            outgoing.append({
                "id": t,
                "name": node_name(node_map[t]),
                "type": node_map[t].get("type"),
                "engine": node_map[t].get("engine"),
                "relationship": e.get("type") or e.get("label"),
            })

        if t == node_identifier and s in node_map:
            incoming.append({
                "id": s,
                "name": node_name(node_map[s]),
                "type": node_map[s].get("type"),
                "engine": node_map[s].get("engine"),
                "relationship": e.get("type") or e.get("label"),
            })

    return {
        "node": node_map.get(node_identifier),
        "incoming": incoming,
        "outgoing": outgoing,
        "incoming_count": len(incoming),
        "outgoing_count": len(outgoing),
    }


def impact(node_identifier: str, depth: int = 3):
    graph = load_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_map = {
        node_id(n): n
        for n in nodes
        if node_id(n)
    }

    adjacency = {}

    for e in edges:
        s = str(e.get("source", e.get("from", "")))
        t = str(e.get("target", e.get("to", "")))

        if s in node_map and t in node_map:
            adjacency.setdefault(s, []).append(t)

    visited = {node_identifier}
    queue = [(node_identifier, 0)]
    impacted = []

    while queue:
        current, current_depth = queue.pop(0)

        if current_depth >= depth:
            continue

        for target in adjacency.get(current, []):
            if target in visited:
                continue

            visited.add(target)

            if target in node_map:
                impacted.append({
                    "id": target,
                    "name": node_name(node_map[target]),
                    "type": node_map[target].get("type"),
                    "engine": node_map[target].get("engine"),
                    "depth": current_depth + 1,
                })

            queue.append((target, current_depth + 1))

    return {
        "root": node_map.get(node_identifier),
        "depth": depth,
        "count": len(impacted),
        "nodes": impacted,
    }


def read_analysis(name: str):
    path = ANALYSIS_FILES.get(name)

    if not path:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown analysis: {name}"
        )

    return load_json(path, {})


def collect_source_files():
    """
    Mengambil source production yang relevan untuk Developer Core.

    Mengeluarkan:
    - backup
    - app_backup_*
    - *_backup
    - before_*
    - after_*
    - research
    - archive
    - quarantine
    - benchmark
    - cache
    - virtual environment
    """

    files = []

    excluded_exact_dirs = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "backup",
        "backups",
        "research",
        "archive",
        "archives",
        "quarantine",
        "benchmark",
        "node_modules",
        "graphify-out",
    }

    excluded_name_tokens = {
        ".bak",
        ".backup",
        "backup_",
        "_backup",
        "before_",
        "after_",
    }

    allowed_extensions = {
        ".py",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".md",
    }

    def is_blocked_part(part: str) -> bool:
        p = part.lower().strip()

        if not p:
            return False

        if p in excluded_exact_dirs:
            return True

        # Contoh:
        # app_backup_before_openrouter
        # backup_old
        # old_backup
        # before_openrouter
        # after_patch
        if p.startswith("app_backup_"):
            return True

        if p.startswith("backup_"):
            return True

        if p.endswith("_backup"):
            return True

        if p.startswith("before_"):
            return True

        if p.startswith("after_"):
            return True

        if p.startswith("backup-"):
            return True

        if p.endswith("-backup"):
            return True

        return False

    for path in ROOT.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in allowed_extensions:
            continue

        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            continue

        # Periksa SEMUA komponen folder.
        blocked = False

        for part in relative.parts[:-1]:
            if is_blocked_part(part):
                blocked = True
                break

        if blocked:
            continue

        # Periksa nama file.
        name_lower = path.name.lower()

        if any(
            token in name_lower
            for token in excluded_name_tokens
        ):
            continue

        files.append(path)

    files.sort(
        key=lambda p: str(p).lower()
    )

    return files

def build_source_index():
    documents = []

    for p in collect_source_files():
        try:
            text = p.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            relative = str(p.relative_to(ROOT))

            documents.append({
                "path": relative,
                "extension": p.suffix.lower(),
                "size": len(text),
                "lines": text.count("\n") + 1,
                "sha256": hashlib.sha256(
                    text.encode("utf-8", errors="ignore")
                ).hexdigest(),
                "content": text,
            })

        except Exception:
            pass

    data = {
        "generated_at": time.strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),
        "root": str(ROOT),
        "documents": documents,
        "document_count": len(documents),
    }

    save_json(INDEX_FILE, data)

    return data


def search_source(query: str, limit: int = 8):
    """
    Source RAG production-only search.

    Backup, archive, research, quarantine dan hasil eksperimen
    tidak boleh menjadi evidence utama.
    """

    q = (query or "").strip().lower()

    if not q:
        return []

    terms = [
        token
        for token in re.findall(r"[a-zA-Z0-9_]+", q)
        if len(token) >= 2
    ]

    priority_tokens = {
        "routes.py": 35,
        "engine.py": 20,
        "rag.py": 20,
        "workflow": 15,
        "hermes": 15,
        "ollama": 15,
        "knowledge": 20,
        "developer_core": 30,
    }

    blocked_tokens = {
        "backup",
        "backups",
        "before_openrouter",
        "after_openrouter",
        "research",
        "archive",
        "archives",
        "quarantine",
        "benchmark",
        "__pycache__",
        ".venv",
        "node_modules",
    }

    results = []

    for path in collect_source_files():

        try:
            relative = str(path.relative_to(ROOT))
        except ValueError:
            continue

        path_lower = relative.lower()

        if any(token in path_lower for token in blocked_tokens):
            continue

        try:
            content = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        content_lower = content.lower()

        score = 0

        if q in path_lower:
            score += 150

        for term in terms:

            if term in path_lower:
                score += 50

            occurrences = content_lower.count(term)

            if occurrences:
                score += min(occurrences, 8) * 5

        if (
            path_lower.startswith("app/")
            or path_lower.startswith("app\\")
        ):
            score += 25

        for token, weight in priority_tokens.items():
            if token in path_lower:
                score += weight

        if score <= 0:
            continue

        results.append({
            "path": relative,
            "score": score,
            "content": content,
        })

    results.sort(
        key=lambda item: (
            -item["score"],
            item["path"].lower(),
        )
    )

    deduped = []
    seen = set()

    for item in results:

        key = item["path"].lower()

        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

        if len(deduped) >= limit:
            break

    return deduped

def build_graph_context(query: str):
    """
    Membentuk context ringkas dari Graph RAG + Source RAG.
    """

    graph_results = search_graph(query, limit=15)
    source_results = search_source(query, limit=5)

    lines = []

    lines.append("=== DEVELOPER CORE EVIDENCE ===")
    lines.append("")

    lines.append("GRAPH RESULTS:")

    if graph_results:
        for item in graph_results:
            lines.append(
                f"- {item.get('name')} | "
                f"path={item.get('path')} | "
                f"type={item.get('type')} | "
                f"score={item.get('score')}"
            )
    else:
        lines.append("- Tidak ada graph result yang relevan.")

    lines.append("")
    lines.append("SOURCE RESULTS:")

    if source_results:
        for item in source_results:
            content = item.get("content", "")
            snippet = content[:3500]

            lines.append(
                f"\n--- {item.get('path')} "
                f"(score={item.get('score')}) ---"
            )
            lines.append(snippet)
    else:
        lines.append("- Tidak ada source result yang relevan.")

    return "\n".join(lines)

def graph_rag(query: str):
    return {
        "query": query,
        "graph": search_graph(query, 12),
        "source": search_source(query, 6),
        "context": build_graph_context(query),
    }


def ollama_generate(
    prompt: str,
    model: str = "llama3.2:1b"
):
    try:
        import urllib.request

        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
        }).encode("utf-8")

        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=180
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

            return data.get(
                "response",
                ""
            )

    except Exception as exc:
        return (
            "[OLLAMA_ERROR] "
            + str(exc)
        )


def self_analysis():
    summary = graph_summary()

    report = read_analysis("report")
    architecture = read_analysis("architecture")
    engine_summary = read_analysis(
        "engine_summary"
    )

    return {
        "developer_core": {
            "root": str(ROOT),
            "graph": summary,
        },
        "architecture": architecture,
        "engine_summary": engine_summary,
        "report": report,
        "source_index": {
            "exists": INDEX_FILE.exists(),
            "documents": len(
                load_json(
                    INDEX_FILE,
                    {"documents": []}
                ).get("documents", [])
            ),
        },
        "components": {
            "graphify": GRAPH_FILE.exists(),
            "graph_analyzer": all(
                p.exists()
                for p in ANALYSIS_FILES.values()
            ),
            "source_rag": INDEX_FILE.exists(),
            "ollama": True,
        },
    }


def run_graphify():
    command = [
        "graphify",
        "extract",
        str(ROOT),
        "--code-only",
        "--no-cluster",
        "--force",
    ]

    try:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-5000:],
            "stderr": result.stderr[-5000:],
        }

    except Exception as exc:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
        }


def run_analyzer():
    analyzer = GRAPH_DIR / "graph_analyzer.py"

    if not analyzer.exists():
        return {
            "returncode": -1,
            "error": "graph_analyzer.py tidak ditemukan"
        }

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(analyzer)
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-5000:],
            "stderr": result.stderr[-5000:],
        }

    except Exception as exc:
        return {
            "returncode": -1,
            "error": str(exc)
        }


def reindex():
    started = time.time()

    graphify_result = run_graphify()

    if graphify_result.get("returncode") != 0:
        return {
            "success": False,
            "stage": "graphify",
            "graphify": graphify_result,
        }

    invalidate_cache()

    analyzer_result = run_analyzer()

    source_index = build_source_index()

    invalidate_cache()

    result = {
        "success": (
            analyzer_result.get("returncode") == 0
        ),
        "duration_seconds": round(
            time.time() - started,
            2
        ),
        "graphify": graphify_result,
        "analyzer": analyzer_result,
        "source_documents": source_index[
            "document_count"
        ],
        "summary": graph_summary(),
    }

    save_json(
        STATE_FILE,
        {
            "last_reindex": time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "result": result,
        }
    )

    return result


def source_signature():
    values = []

    for p in collect_source_files():
        try:
            stat = p.stat()

            values.append(
                (
                    str(p),
                    stat.st_size,
                    stat.st_mtime_ns,
                )
            )
        except Exception:
            pass

    return hashlib.sha256(
        repr(values).encode()
    ).hexdigest()


def watcher():
    previous = None

    while True:
        try:
            current = source_signature()

            if previous is None:
                previous = current

            elif current != previous:
                previous = current

                print(
                    "\n[Developer Core] "
                    "Source change detected."
                )

                result = reindex()

                print(
                    "[Developer Core] "
                    f"Re-index complete: "
                    f"{result.get('success')}"
                )

        except Exception as exc:
            print(
                "[Developer Core Watcher]",
                exc
            )

        time.sleep(15)


app = FastAPI(
    title="Nusantara Developer Core Engine",
    version="1.0.0",
    description=(
        "Local Graph RAG + Source RAG + "
        "Ollama Developer Core"
    ),
)


class ChatRequest(BaseModel):
    input: str
    model: str = "llama3.2:1b"
    use_graph: bool = True
    use_source: bool = True


@app.get("/v1/developer/health")
def developer_health():
    return {
        "status": "ok",
        "service": "Nusantara Developer Core",
        "graph": graph_summary(),
        "source_index": INDEX_FILE.exists(),
        "ollama": "http://127.0.0.1:11434",
    }


@app.get("/v1/graph/summary")
def graph_summary_api():
    return graph_summary()


@app.get("/v1/graph/search")
def graph_search_api(
    q: str = Query(...),
    limit: int = Query(30, ge=1, le=200),
):
    return {
        "query": q,
        "results": search_graph(q, limit),
    }


@app.get("/v1/graph/node/{node_id}")
def graph_node_api(node_id: str):
    node = get_node(node_id)

    if node is None:
        raise HTTPException(
            status_code=404,
            detail="Node tidak ditemukan"
        )

    return node


@app.get("/v1/graph/dependency/{node_id}")
def graph_dependency_api(node_id: str):
    return node_dependencies(node_id)


@app.get("/v1/graph/impact/{node_id}")
def graph_impact_api(
    node_id: str,
    depth: int = Query(
        3,
        ge=1,
        le=10
    ),
):
    return impact(node_id, depth)


@app.get("/v1/graph/{analysis}")
def graph_analysis_api(
    analysis: str
):
    return read_analysis(analysis)


@app.get("/v1/source/search")
def source_search_api(
    q: str = Query(...),
    limit: int = Query(8, ge=1, le=50),
):
    return {
        "query": q,
        "results": search_source(
            q,
            limit
        ),
    }


@app.get("/v1/rag/context")
def rag_context_api(
    q: str = Query(...),
):
    return graph_rag(q)


@app.get("/v1/self-analysis")
def self_analysis_api():
    return self_analysis()


@app.post("/v1/reindex")
def reindex_api():
    return reindex()


@app.post("/v1/chat")
def developer_chat(request: ChatRequest):
    query = request.input

    context = ""

    if request.use_graph or request.use_source:
        context = build_graph_context(query)

    prompt = f"""
Anda adalah Nusantara Developer Core Engine.

Anda membantu menganalisis source code aplikasi
berdasarkan Graph Knowledge dan Source Code Knowledge.

ATURAN:
1. Gunakan konteks yang diberikan.
2. Jangan mengarang file, dependency, class,
   function atau workflow.
3. Jika informasi tidak tersedia, katakan
   bahwa informasi tidak ditemukan.
4. Bedakan fakta dari inferensi.
5. Jawab dalam Bahasa Indonesia.
6. Fokus pada struktur dan engineering.

PERTANYAAN USER:
{query}

KONTEKS DEVELOPER CORE:
{context}

Berikan jawaban teknis yang ringkas tetapi konkret.
"""

    answer = ollama_generate(
        prompt,
        request.model
    )

    return {
        "input": query,
        "model": request.model,
        "graph_enabled": request.use_graph,
        "source_enabled": request.use_source,
        "context": context,
        "output": answer,
    }


def startup():
    print("")
    print("=" * 60)
    print(" NUSANTARA DEVELOPER CORE ENGINE")
    print("=" * 60)
    print("Graph API       : ENABLED")
    print("Graph RAG       : ENABLED")
    print("Source RAG      : ENABLED")
    print("Self Analysis   : ENABLED")
    print("Auto Re-index   : ENABLED")
    print("Ollama          : ENABLED")
    print("=" * 60)

    if not INDEX_FILE.exists():
        print(
            "[Developer Core] "
            "Membuat source index..."
        )

        build_source_index()

    thread = threading.Thread(
        target=watcher,
        daemon=True,
        name="developer-core-watcher",
    )

    thread.start()

    print(
        "[Developer Core] "
        "Watcher aktif setiap 15 detik."
    )


startup()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8010,
        log_level="info",
    )
