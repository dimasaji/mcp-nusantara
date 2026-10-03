import json
from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

graph = json.loads((OUT / "graph.json").read_text(encoding="utf-8"))
truth = json.loads((OUT / "gate14_runtime_graph_truth.json").read_text(encoding="utf-8"))

nodes = graph.get("nodes", [])
links = graph.get("links", [])

node_map = {str(n.get("id")): n for n in nodes if n.get("id") is not None}

adj = defaultdict(list)

for link in links:
    source = str(link.get("source"))
    target = str(link.get("target"))

    adj[source].append({
        "node": target,
        "relation": link.get("type") or link.get("relation") or "unknown"
    })

    adj[target].append({
        "node": source,
        "relation": link.get("type") or link.get("relation") or "unknown"
    })

runtime_modules = truth.get("runtime", {}).get("modules", [])

targets = []

for module in runtime_modules:
    file_path = module.get("file")

    if not file_path:
        continue

    filename = Path(file_path).name

    matches = []

    for node_id, node in node_map.items():
        text = " ".join(
            str(node.get(k, "") or "")
            for k in ("id", "name", "label", "path", "file", "module")
        ).lower()

        if filename.lower() in text:
            matches.append(node_id)

    if matches:
        targets.append({
            "module": module.get("module"),
            "file": file_path,
            "filename": filename,
            "nodes": matches[:20]
        })

impact = []

for target in targets:
    for root in target["nodes"]:
        visited = {root}
        queue = deque([(root, 0)])

        while queue:
            current, depth = queue.popleft()

            if depth >= 3:
                continue

            for edge in adj.get(current, []):
                nxt = edge["node"]

                if nxt in visited:
                    continue

                visited.add(nxt)
                queue.append((nxt, depth + 1))

                node = node_map.get(nxt, {})

                impact.append({
                    "source_module": target["module"],
                    "source_file": target["filename"],
                    "source_node": root,
                    "affected_node": nxt,
                    "affected_label": node.get("label"),
                    "affected_type": node.get("type"),
                    "depth": depth + 1,
                    "relation": edge["relation"]
                })

unique = {}
for item in impact:
    key = (
        item["source_module"],
        item["affected_node"],
        item["depth"]
    )
    unique[key] = item

impact = list(unique.values())

summary = defaultdict(int)

for item in impact:
    summary[item["source_module"]] += 1

result = {
    "gate": "14.6",
    "engine": "Developer Core Change Intelligence",
    "version": "14.6.0",
    "timestamp": datetime.now().isoformat(),
    "source_of_truth": str(ROOT),
    "graph": {
        "nodes": len(nodes),
        "links": len(links)
    },
    "runtime": {
        "modules": len(runtime_modules)
    },
    "impact_analysis": {
        "max_depth": 3,
        "runtime_targets": len(targets),
        "affected_relationships": len(impact),
        "by_module": dict(summary)
    },
    "targets": targets,
    "impact": impact[:2000],
    "status": "PASS" if impact else "PARTIAL"
}

output = OUT / "gate14_6_change_intelligence.json"

output.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 64)
print("NUSANTARA GATE 14.6 - CHANGE INTELLIGENCE")
print("=" * 64)
print("Runtime modules       :", len(runtime_modules))
print("Graph nodes           :", len(nodes))
print("Graph links           :", len(links))
print("Runtime targets       :", len(targets))
print("Affected relations    :", len(impact))
print("Analysis depth        : 3 hops")
print("STATUS                :", result["status"])
print("Output                :", output)

print()
print("IMPACT BY MODULE")

for module, count in sorted(summary.items()):
    print(f"  {module:<40} {count}")
