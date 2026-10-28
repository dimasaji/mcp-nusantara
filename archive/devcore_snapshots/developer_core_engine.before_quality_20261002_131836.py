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


def search_graph(q: str, limit: int = 30):
    graph = load_graph()
    q = q.lower().strip()

    if not q:
        return []

    results = []

    for n in graph.get("nodes", []):
        text = node_text(n)

        if q in text:
            results.append({
                "id": node_id(n),
                "name": node_name(n),
                "type": n.get("type"),
                "engine": n.get("engine"),
                "role": n.get("role"),
                "path": n.get("path") or n.get("file"),
            })

            if len(results) >= limit:
                break

    return results


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
    files = []

    for base in SOURCE_DIRS:
        if not base.exists():
            continue

        for p in base.rglob("*"):
            if not p.is_file():
                continue

            if p.suffix.lower() not in {
                ".py",
                ".md",
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".txt",
            }:
                continue

            if "__pycache__" in p.parts:
                continue

            if ".venv" in p.parts:
                continue

            files.append(p)

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
    index = load_json(INDEX_FILE, {"documents": []})

    query = query.lower().strip()

    if not query:
        return []

    terms = [
        x for x in re.split(
            r"\s+",
            query
        )
        if x
    ]

    results = []

    for doc in index.get("documents", []):
        content = doc.get("content", "")
        low = content.lower()

        score = 0

        for term in terms:
            score += low.count(term)

        if query in low:
            score += 10

        if score <= 0:
            continue

        position = low.find(terms[0]) if terms else 0

        start = max(0, position - 500)
        end = min(
            len(content),
            position + 1500
        )

        results.append({
            "path": doc["path"],
            "score": score,
            "lines": doc["lines"],
            "snippet": content[start:end],
        })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:limit]


def build_graph_context(query: str):
    graph_results = search_graph(query, 12)
    source_results = search_source(query, 6)

    context = []

    if graph_results:
        context.append("=== GRAPH KNOWLEDGE ===")

        for item in graph_results:
            context.append(
                f"- {item.get('name')} "
                f"[type={item.get('type')}, "
                f"engine={item.get('engine')}, "
                f"role={item.get('role')}, "
                f"path={item.get('path')}]"
            )

    if source_results:
        context.append("=== SOURCE CODE KNOWLEDGE ===")

        for item in source_results:
            snippet = item.get(
                "snippet",
                ""
            )

            context.append(
                f"\nFILE: {item['path']}\n"
                f"{snippet}"
            )

    if not context:
        return "Tidak ditemukan konteks Graph/Source yang relevan."

    return "\n".join(context)


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
