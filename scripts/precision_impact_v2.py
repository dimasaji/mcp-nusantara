from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "graphify-out" / "graph.json"
OUT = ROOT / "graphify-out" / "precision_impact_v2.json"

IGNORE = {
    "typing", "pathlib", "json", "dataclasses", "os", "sys",
    "re", "time", "datetime", "logging", "enum", "abc",
    "asyncio", "uuid", "math", "collections", "functools",
    "itertools", "typing_extensions"
}

def is_relevant(n):
    name = str(n.get("name") or n.get("label") or n.get("id") or "")
    low = name.lower()

    if low in IGNORE:
        return False

    if "developer_core_engine.before_" in low:
        return False

    if "backup" in low:
        return False

    if low.startswith("test_") or low.endswith("_test.py"):
        return False

    return (
        low.endswith(".py")
        or low.startswith("nusantara")
        or "engine" in low
        or "rag" in low
        or "retriev" in low
        or "graph" in low
        or "language" in low
        or "routes" in low
        or "knowledge" in low
        or "workflow" in low
    )

def main():
    print("=" * 70)
    print("NUSANTARA PRECISION IMPACT ANALYZER v2")
    print("=" * 70)

    if not GRAPH.exists():
        raise FileNotFoundError(GRAPH)

    data = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    relevant_ids = set()
    node_info = {}

    for n in nodes:
        node_id = str(n.get("id", ""))
        name = n.get("name") or n.get("label") or node_id

        if is_relevant(n):
            relevant_ids.add(node_id)
            node_info[node_id] = name

    incoming = {x: 0 for x in relevant_ids}
    outgoing = {x: 0 for x in relevant_ids}
    connected = {x: set() for x in relevant_ids}

    for e in edges:
        src = str(e.get("source", ""))
        dst = str(e.get("target", ""))

        if src in relevant_ids and dst in relevant_ids:
            outgoing[src] += 1
            incoming[dst] += 1
            connected[src].add(dst)
            connected[dst].add(src)

    results = []

    for node_id in relevant_ids:
        impact = incoming[node_id] + outgoing[node_id]

        results.append({
            "id": node_id,
            "name": node_info[node_id],
            "incoming": incoming[node_id],
            "outgoing": outgoing[node_id],
            "connections": len(connected[node_id]),
            "impact": impact,
            "impact_level": (
                "CRITICAL" if impact >= 20 else
                "HIGH" if impact >= 10 else
                "MEDIUM" if impact >= 5 else
                "LOW"
            )
        })

    results.sort(key=lambda x: x["impact"], reverse=True)

    output = {
        "engine": "Nusantara Precision Impact Analyzer",
        "version": "2.0.0",
        "source_graph": str(GRAPH),
        "graph_nodes": len(nodes),
        "graph_edges": len(edges),
        "relevant_nodes": len(relevant_ids),
        "filtered_nodes": len(nodes) - len(relevant_ids),
        "results": results,
        "top_impact_nodes": results[:100]
    }

    OUT.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Graph nodes       : {len(nodes)}")
    print(f"Graph edges       : {len(edges)}")
    print(f"Relevant nodes    : {len(relevant_ids)}")
    print(f"Filtered noise    : {len(nodes) - len(relevant_ids)}")
    print(f"Output            : {OUT}")
    print()
    print("TOP 30 RELEVANT IMPACT")
    print("-" * 70)

    for i, x in enumerate(results[:30], 1):
        print(
            f"{i:02d}. {x['name']} | "
            f"impact={x['impact']} | "
            f"in={x['incoming']} | "
            f"out={x['outgoing']} | "
            f"{x['impact_level']}"
        )

    print()
    print("PRECISION IMPACT v2: COMPLETE")

if __name__ == "__main__":
    main()
