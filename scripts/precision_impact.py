from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "graphify-out" / "graph.json"
OUT = ROOT / "graphify-out" / "precision_impact.json"

def main():
    print("=" * 64)
    print("NUSANTARA PRECISION IMPACT ANALYZER")
    print("=" * 64)

    if not GRAPH.exists():
        raise FileNotFoundError(f"Graph tidak ditemukan: {GRAPH}")

    data = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    incoming = {}
    outgoing = {}

    for e in edges:
        src = e.get("source")
        dst = e.get("target")

        if src is None or dst is None:
            continue

        outgoing.setdefault(str(src), []).append(str(dst))
        incoming.setdefault(str(dst), []).append(str(src))

    results = []

    for n in nodes:
        node_id = str(n.get("id", ""))
        name = n.get("name") or n.get("label") or node_id

        ins = incoming.get(node_id, [])
        outs = outgoing.get(node_id, [])

        impact = len(ins) + len(outs)

        results.append({
            "id": node_id,
            "name": name,
            "incoming": len(ins),
            "outgoing": len(outs),
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
        "version": "1.0.0",
        "graph": str(GRAPH),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes_analyzed": len(results),
        "top_impact_nodes": results[:100]
    }

    OUT.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Nodes            : {len(nodes)}")
    print(f"Edges            : {len(edges)}")
    print(f"Analyzed         : {len(results)}")
    print(f"Output           : {OUT}")
    print()
    print("TOP IMPACT NODES")
    print("-" * 64)

    for i, item in enumerate(results[:20], 1):
        print(
            f"{i:02d}. {item['name']} | "
            f"impact={item['impact']} | "
            f"in={item['incoming']} | "
            f"out={item['outgoing']} | "
            f"{item['impact_level']}"
        )

    print()
    print("PRECISION IMPACT ANALYSIS: COMPLETE")

if __name__ == "__main__":
    main()
