from pathlib import Path
import json
from collections import defaultdict, deque

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "graphify-out" / "graph.json"
OUT = ROOT / "graphify-out" / "nusantara_runtime_architecture.json"

TARGETS = {
    "API": ["routes.py", "v2_routes.py"],
    "CORE": ["core.py", "agent.py"],
    "LANGUAGE": ["language/engine.py", "LanguageEngine"],
    "PROBLEM": ["problem/engine.py", "ProblemEngine"],
    "RAG": ["rag.py", "RAG", "ProductionHybridRAG"],
    "KNOWLEDGE": ["knowledge/engine.py", "KnowledgeEngine"],
    "REASONING": ["reasoning/engine.py", "ReasoningEngine"],
    "WORKFLOW": ["WorkflowEngine", "workflow_schema.py"],
    "DEVELOPER_CORE": ["developer_core_engine.py"],
}

def main():
    print("=" * 72)
    print("NUSANTARA RUNTIME ARCHITECTURE MAP")
    print("=" * 72)

    data = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    names = {}
    by_name = defaultdict(list)

    for n in nodes:
        node_id = str(n.get("id", ""))
        name = str(n.get("name") or n.get("label") or node_id)
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

    layer_nodes = {}

    for layer, wanted_names in TARGETS.items():
        ids = set()

        for wanted in wanted_names:
            ids.update(by_name.get(wanted, []))

        layer_nodes[layer] = ids

    def layer_of(node_id):
        for layer, ids in layer_nodes.items():
            if node_id in ids:
                return layer
        return None

    layer_edges = defaultdict(set)

    for src in names:
        src_layer = layer_of(src)

        if not src_layer:
            continue

        for dst in outgoing[src]:
            dst_layer = layer_of(dst)

            if dst_layer and src_layer != dst_layer:
                layer_edges[src_layer].add(dst_layer)

    architecture = []

    for layer, ids in layer_nodes.items():
        components = []

        for node_id in ids:
            consumers = [
                names[x] for x in incoming[node_id]
                if x in names
            ]

            dependencies = [
                names[x] for x in outgoing[node_id]
                if x in names
            ]

            components.append({
                "id": node_id,
                "name": names[node_id],
                "consumer_count": len(consumers),
                "dependency_count": len(dependencies)
            })

        components.sort(
            key=lambda x: (
                x["consumer_count"],
                x["dependency_count"]
            ),
            reverse=True
        )

        architecture.append({
            "layer": layer,
            "component_count": len(components),
            "components": components
        })

    output = {
        "engine": "Nusantara Runtime Architecture Map",
        "version": "1.0.0",
        "graph_nodes": len(nodes),
        "graph_edges": len(edges),
        "layers": architecture,
        "layer_connections": {
            src: sorted(list(dst))
            for src, dst in layer_edges.items()
        }
    }

    OUT.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Graph nodes : {len(nodes)}")
    print(f"Graph edges : {len(edges)}")
    print(f"Output      : {OUT}")
    print()
    print("RUNTIME LAYERS")
    print("-" * 72)

    for item in architecture:
        print(
            f"{item['layer']:<16} "
            f"components={item['component_count']}"
        )

    print()
    print("LAYER CONNECTIONS")
    print("-" * 72)

    for src, dsts in layer_edges.items():
        print(f"{src} -> {', '.join(sorted(dsts))}")

    print()
    print("CORE COMPONENTS")
    print("-" * 72)

    for item in architecture:
        for component in item["components"][:5]:
            print(
                f"{item['layer']:<16} "
                f"{component['name']:<35} "
                f"consumers={component['consumer_count']:<3} "
                f"deps={component['dependency_count']}"
            )

    print()
    print("RUNTIME ARCHITECTURE MAP: COMPLETE")

if __name__ == "__main__":
    main()
