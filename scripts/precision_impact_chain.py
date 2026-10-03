from pathlib import Path
import json
from collections import defaultdict, deque

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "graphify-out" / "graph.json"
IMPACT = ROOT / "graphify-out" / "precision_impact_v2.json"
OUT = ROOT / "graphify-out" / "precision_impact_chain.json"

TARGETS = [
    "routes.py",
    "v2_routes.py",
    "ProductionHybridRAG",
    "language/engine.py",
    "agent.py",
    "rag.py",
    "core.py",
    "developer_core_engine.py",
    "knowledge/engine.py",
    "problem/engine.py",
    "reasoning/engine.py",
]

def main():
    print("=" * 72)
    print("NUSANTARA PRECISION IMPACT CHAIN")
    print("=" * 72)

    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    impact = json.loads(IMPACT.read_text(encoding="utf-8"))

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    names = {}
    for n in nodes:
        node_id = str(n.get("id", ""))
        name = str(n.get("name") or n.get("label") or node_id)
        names[node_id] = name

    by_name = defaultdict(list)
    for node_id, name in names.items():
        by_name[name].append(node_id)

    outgoing = defaultdict(list)
    incoming = defaultdict(list)

    for e in edges:
        src = str(e.get("source", ""))
        dst = str(e.get("target", ""))

        if src in names and dst in names:
            outgoing[src].append(dst)
            incoming[dst].append(src)

    results = []

    for target in TARGETS:
        ids = by_name.get(target, [])

        if not ids:
            print(f"[NOT FOUND] {target}")
            continue

        for node_id in ids:
            visited = {node_id}
            queue = deque([(node_id, 0)])
            chain = []

            while queue:
                current, depth = queue.popleft()

                if depth >= 3:
                    continue

                for nxt in outgoing.get(current, []):
                    if nxt in visited:
                        continue

                    visited.add(nxt)

                    chain.append({
                        "depth": depth + 1,
                        "id": nxt,
                        "name": names.get(nxt, nxt)
                    })

                    queue.append((nxt, depth + 1))

            upstream = []
            visited_up = {node_id}
            queue = deque([(node_id, 0)])

            while queue:
                current, depth = queue.popleft()

                if depth >= 3:
                    continue

                for prev in incoming.get(current, []):
                    if prev in visited_up:
                        continue

                    visited_up.add(prev)

                    upstream.append({
                        "depth": depth + 1,
                        "id": prev,
                        "name": names.get(prev, prev)
                    })

                    queue.append((prev, depth + 1))

            results.append({
                "target": target,
                "node_id": node_id,
                "downstream": chain,
                "upstream": upstream,
                "downstream_count": len(chain),
                "upstream_count": len(upstream)
            })

    output = {
        "engine": "Nusantara Precision Impact Chain",
        "version": "1.0.0",
        "graph_nodes": len(nodes),
        "graph_edges": len(edges),
        "targets": TARGETS,
        "chains": results
    }

    OUT.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print()
    print(f"Targets analyzed : {len(results)}")
    print(f"Output           : {OUT}")
    print()
    print("IMPACT CHAINS")
    print("-" * 72)

    for item in results:
        print()
        print(f"[TARGET] {item['target']}")
        print(f"  Downstream : {item['downstream_count']}")
        print(f"  Upstream   : {item['upstream_count']}")

        for x in item["downstream"][:12]:
            print(f"    -> [{x['depth']}] {x['name']}")

    print()
    print("PRECISION IMPACT CHAIN: COMPLETE")

if __name__ == "__main__":
    main()
