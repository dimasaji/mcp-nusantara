from pathlib import Path
import json
from collections import Counter, defaultdict, deque

ROOT = Path(r"C:\Users\dmaza\mcp-starter")
OUT = ROOT / "graphify-out"
GRAPH_FILE = OUT / "graph.json"

print()
print("==============================================")
print("     NUSANTARA GRAPH ANALYZER")
print("==============================================")
print()

print("Graph file:")
print(GRAPH_FILE)

if not GRAPH_FILE.exists():
    print()
    print("[ERROR] graph.json tidak ditemukan.")
    raise SystemExit(1)

with GRAPH_FILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

nodes_raw = data.get("nodes", [])
edges_raw = data.get("edges", [])

print()
print(f"NODES : {len(nodes_raw)}")
print(f"EDGES : {len(edges_raw)}")
print()

nodes = {}
for n in nodes_raw:
    node_id = str(n.get("id", ""))
    if not node_id:
        continue

    name = str(
        n.get("name")
        or n.get("label")
        or n.get("title")
        or node_id
    )

    path = str(
        n.get("path")
        or n.get("file")
        or n.get("filename")
        or ""
    )

    node_type = str(
        n.get("type")
        or n.get("kind")
        or "Other"
    )

    nodes[node_id] = {
        "id": node_id,
        "name": name,
        "path": path,
        "type": node_type,
        "raw": n,
    }

edges = []
invalid_edges = []

for e in edges_raw:
    source = str(
        e.get("source")
        or e.get("from")
        or ""
    )

    target = str(
        e.get("target")
        or e.get("to")
        or ""
    )

    if source in nodes and target in nodes:
        edges.append({
            "source": source,
            "target": target,
            "type": str(
                e.get("type")
                or e.get("kind")
                or "relationship"
            ),
        })
    else:
        invalid_edges.append({
            "source": source,
            "target": target,
            "raw": e,
        })

outgoing = defaultdict(list)
incoming = defaultdict(list)

for e in edges:
    outgoing[e["source"]].append(e["target"])
    incoming[e["target"]].append(e["source"])


def node_type(name):
    text = name.lower()

    if text.endswith(".py"):
        return "File"

    if "class " in text:
        return "Class"

    if "module" in text:
        return "Module"

    if "function" in text or "def " in text:
        return "Function"

    if "method" in text:
        return "Method"

    return "Other"


def engine_for(node):
    text = (
        node["name"]
        + " "
        + node["path"]
    ).lower()

    if any(x in text for x in [
        "routes.py",
        "fastapi",
        "api",
        "/v1/",
    ]):
        return "API"

    if any(x in text for x in [
        "knowledge",
        "rag",
        "retrieval",
        "embedding",
        "chunk",
        "vector",
    ]):
        return "Knowledge"

    if any(x in text for x in [
        "ollama",
        "llm",
        "model",
        "hermes",
        "prompt",
    ]):
        return "LLM"

    if any(x in text for x in [
        "workflow",
        "pipeline",
        "orchestration",
        "agent",
    ]):
        return "Workflow"

    if any(x in text for x in [
        "test",
        "pytest",
    ]):
        return "Testing"

    return "Core"


def role_for(node):
    text = (
        node["name"]
        + " "
        + node["path"]
    ).lower()

    if "route" in text or "api" in text:
        return "API"

    if "knowledge" in text or "rag" in text:
        return "Knowledge"

    if "workflow" in text:
        return "Workflow"

    if "test" in text:
        return "Testing"

    if "config" in text:
        return "Configuration"

    if "model" in text or "llm" in text:
        return "LLM"

    if "util" in text or "helper" in text:
        return "Utility"

    return "Core"


for node in nodes.values():
    node["detected_type"] = node_type(node["name"])
    node["engine"] = engine_for(node)
    node["role"] = role_for(node)
    node["in_degree"] = len(incoming[node["id"]])
    node["out_degree"] = len(outgoing[node["id"]])
    node["degree"] = (
        node["in_degree"]
        + node["out_degree"]
    )


def bfs(start, direction="out", limit=1000):
    result = []
    visited = {start}
    queue = deque([start])

    while queue and len(result) < limit:
        current = queue.popleft()

        neighbors = (
            outgoing[current]
            if direction == "out"
            else incoming[current]
        )

        for nxt in neighbors:
            if nxt in visited:
                continue

            visited.add(nxt)
            queue.append(nxt)
            result.append(nxt)

            if len(result) >= limit:
                break

    return result


def node_export(node):
    return {
        "id": node["id"],
        "name": node["name"],
        "path": node["path"],
        "type": node["type"],
        "detected_type": node["detected_type"],
        "engine": node["engine"],
        "role": node["role"],
        "in_degree": node["in_degree"],
        "out_degree": node["out_degree"],
        "degree": node["degree"],
    }


print("Menganalisis architecture...")

architecture = {
    "total_nodes": len(nodes),
    "total_edges": len(edges),
    "invalid_edges": len(invalid_edges),
    "node_types": dict(
        Counter(
            n["detected_type"]
            for n in nodes.values()
        )
    ),
    "engines": dict(
        Counter(
            n["engine"]
            for n in nodes.values()
        )
    ),
    "roles": dict(
        Counter(
            n["role"]
            for n in nodes.values()
        )
    ),
    "nodes": [
        node_export(n)
        for n in nodes.values()
    ],
}

print("Menganalisis dependency...")

dependency = {
    "total_nodes": len(nodes),
    "total_edges": len(edges),
    "nodes": [],
}

for node in nodes.values():
    dependency["nodes"].append({
        **node_export(node),
        "incoming": [
            node_export(nodes[x])
            for x in incoming[node["id"]]
        ],
        "outgoing": [
            node_export(nodes[x])
            for x in outgoing[node["id"]]
        ],
    })

print("Menganalisis workflow...")

workflow = {
    "entry_points": [],
    "stages": [],
}

entry_candidates = sorted(
    nodes.values(),
    key=lambda n: n["out_degree"],
    reverse=True,
)[:30]

for n in entry_candidates:
    if n["out_degree"] > 0:
        workflow["entry_points"].append({
            **node_export(n),
            "next_nodes": [
                node_export(nodes[x])
                for x in outgoing[n["id"]][:30]
            ],
        })

for engine in [
    "API",
    "Knowledge",
    "Workflow",
    "LLM",
    "Core",
]:
    engine_nodes = [
        node_export(n)
        for n in nodes.values()
        if n["engine"] == engine
    ]

    if engine_nodes:
        workflow["stages"].append({
            "stage": engine,
            "node_count": len(engine_nodes),
            "nodes": engine_nodes[:100],
        })

print("Menganalisis impact...")

top_hubs = sorted(
    nodes.values(),
    key=lambda n: n["degree"],
    reverse=True,
)[:100]

impact = {
    "top_hubs": [],
}

for n in top_hubs:
    downstream = bfs(n["id"], "out", 200)
    upstream = bfs(n["id"], "in", 200)

    impact["top_hubs"].append({
        **node_export(n),
        "downstream_count": len(downstream),
        "upstream_count": len(upstream),
        "downstream": [
            node_export(nodes[x])
            for x in downstream[:50]
        ],
        "upstream": [
            node_export(nodes[x])
            for x in upstream[:50]
        ],
    })

print("Menganalisis candidates...")

candidates = {
    "api": [],
    "knowledge": [],
    "workflow": [],
    "llm": [],
}

for n in nodes.values():
    item = node_export(n)

    if n["engine"] == "API":
        candidates["api"].append(item)

    if n["engine"] == "Knowledge":
        candidates["knowledge"].append(item)

    if n["engine"] == "Workflow":
        candidates["workflow"].append(item)

    if n["engine"] == "LLM":
        candidates["llm"].append(item)

print("Menganalisis engine summary...")

engine_edges = Counter()

for e in edges:
    source_engine = nodes[e["source"]]["engine"]
    target_engine = nodes[e["target"]]["engine"]

    engine_edges[
        f"{source_engine} -> {target_engine}"
    ] += 1

engine_summary = {
    "engines": dict(
        Counter(
            n["engine"]
            for n in nodes.values()
        )
    ),
    "relationships": dict(engine_edges),
}

print("Membuat graph report...")

graph_report = {
    "project": "Nusantara Core",
    "graph_file": str(GRAPH_FILE),
    "statistics": {
        "nodes": len(nodes),
        "edges": len(edges),
        "invalid_edges": len(invalid_edges),
    },
    "architecture": architecture,
    "engine_summary": engine_summary,
    "candidates": candidates,
    "top_hubs": [
        node_export(n)
        for n in top_hubs
    ],
}

files = {
    "architecture.json": architecture,
    "dependency.json": dependency,
    "workflow.json": workflow,
    "impact.json": impact,
    "candidates.json": candidates,
    "engine_summary.json": engine_summary,
    "graph_report.json": graph_report,
}

for filename, payload in files.items():
    target = OUT / filename

    with target.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            payload,
            f,
            ensure_ascii=False,
            indent=2,
        )

if invalid_edges:
    with (OUT / "invalid_edges.json").open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            invalid_edges,
            f,
            ensure_ascii=False,
            indent=2,
        )

print()
print("==============================================")
print(" ANALYSIS SELESAI")
print("==============================================")
print()
print(f"Nodes          : {len(nodes)}")
print(f"Edges          : {len(edges)}")
print(f"Invalid edges  : {len(invalid_edges)}")
print()
print("Output:")
for filename in files:
    print(f"  {OUT / filename}")

if invalid_edges:
    print(f"  {OUT / 'invalid_edges.json'}")

print()
print("Nusantara Graph Analyzer selesai.")
print()
