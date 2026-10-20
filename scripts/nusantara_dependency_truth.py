from pathlib import Path
import json
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "graphify-out" / "graph.json"
OUT = ROOT / "graphify-out" / "nusantara_dependency_truth.json"

CORE_NAMES = {
    "routes.py",
    "v2_routes.py",
    "core.py",
    "agent.py",
    "language/engine.py",
    "LanguageEngine",
    "problem/engine.py",
    "ProblemEngine",
    "rag.py",
    "RAG",
    "knowledge/engine.py",
    "KnowledgeEngine",
    "ProductionHybridRAG",
    "reasoning/engine.py",
    "ReasoningEngine",
    "developer_core_engine.py",
    "WorkflowEngine",
    "workflow_schema.py",
    "context.py",
}

NOISE = {
    "typing", "pathlib", "json", "dataclasses", "os", "sys",
    "re", "time", "datetime", "logging", "enum", "abc",
    "asyncio", "uuid", "math", "collections", "functools",
    "itertools", "FastAPI", "pydantic", "hmac"
}

def name_of(n):
    return str(n.get("name") or n.get("label") or n.get("id") or "")

def main():
    print("=" * 72)
    print("NUSANTARA DEPENDENCY TRUTH MAP")
    print("=" * 72)

    data = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    names = {}
    by_name = defaultdict(list)

    for n in nodes:
        node_id = str(n.get("id", ""))
        name = name_of(n)
        names[node_id] = name
        by_name[name].append(node_id)

    outgoing = defaultdict(set)
    incoming = defaultdict(set)

    for e in edges:
        src = str(e.get("source", ""))
        dst = str(e.get("target", ""))

        if src in names and dst in names:
            outgoing[src].add(dst)
            incoming[dst].add(src)

    core = []

    for wanted in CORE_NAMES:
        for node_id in by_name.get(wanted, []):
            deps = [
                names[x] for x in outgoing[node_id]
                if names[x] not in NOISE
            ]

            consumers = [
                names[x] for x in incoming[node_id]
                if names[x] not in NOISE
            ]

            core.append({
                "name": wanted,
                "id": node_id,
                "dependencies": sorted(set(deps)),
                "consumers": sorted(set(consumers)),
                "dependency_count": len(set(deps)),
                "consumer_count": len(set(consumers))
            })

    core.sort(
        key=lambda x: (
            x["consumer_count"],
            x["dependency_count"]
        ),
        reverse=True
    )

    runtime_layers = {
        "API": [
            "routes.py",
            "v2_routes.py"
        ],
        "CORE": [
            "core.py",
            "agent.py"
        ],
        "LANGUAGE": [
            "language/engine.py",
            "LanguageEngine"
        ],
        "PROBLEM": [
            "problem/engine.py",
            "ProblemEngine"
        ],
        "RAG": [
            "rag.py",
            "RAG",
            "ProductionHybridRAG"
        ],
        "KNOWLEDGE": [
            "knowledge/engine.py",
            "KnowledgeEngine"
        ],
        "REASONING": [
            "reasoning/engine.py",
            "ReasoningEngine"
        ],
        "DEVELOPER_CORE": [
            "developer_core_engine.py"
        ],
        "WORKFLOW": [
            "WorkflowEngine",
            "workflow_schema.py"
        ]
    }

    output = {
        "engine": "Nusantara Dependency Truth Map",
        "version": "1.0.0",
        "graph_nodes": len(nodes),
        "graph_edges": len(edges),
        "runtime_layers": runtime_layers,
        "core_components": core
    }

    OUT.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Graph nodes : {len(nodes)}")
    print(f"Graph edges : {len(edges)}")
    print(f"Core items  : {len(core)}")
    print(f"Output      : {OUT}")
    print()
    print("RUNTIME CORE")
    print("-" * 72)

    for item in core:
        if item["consumer_count"] or item["dependency_count"]:
            print(
                f"{item['name']:<32} "
                f"consumers={item['consumer_count']:<3} "
                f"dependencies={item['dependency_count']:<3}"
            )

    print()
    print("DEPENDENCY TRUTH MAP: COMPLETE")

if __name__ == "__main__":
    main()
