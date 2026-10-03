import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

graph = json.loads((OUT / "graph.json").read_text(encoding="utf-8"))
truth = json.loads((OUT / "gate14_runtime_graph_truth.json").read_text(encoding="utf-8"))

nodes = graph.get("nodes", [])
links = graph.get("links", [])

runtime_files = set()

for module in truth.get("runtime", {}).get("modules", []):
    file_path = module.get("file")
    if file_path:
        runtime_files.add(Path(file_path).name)

def node_text(node):
    return " ".join(
        str(node.get(k, "") or "")
        for k in ("id", "name", "label", "path", "file", "module", "type")
    ).lower()

runtime_nodes = []

for node in nodes:
    text = node_text(node)

    if any(name.lower() in text for name in runtime_files):
        runtime_nodes.append(node)

node_ids = {
    str(n.get("id"))
    for n in runtime_nodes
    if n.get("id") is not None
}

connections = []

for link in links:
    source = str(link.get("source"))
    target = str(link.get("target"))

    if source in node_ids or target in node_ids:
        connections.append({
            "source": source,
            "target": target,
            "type": link.get("type") or link.get("relation") or "unknown"
        })

analysis = {
    "gate": "14.5",
    "engine": "Developer Core Self-Analysis",
    "version": "14.5.1",
    "timestamp": datetime.now().isoformat(),
    "source_of_truth": str(ROOT),
    "runtime": {
        "modules": len(truth.get("runtime", {}).get("modules", [])),
        "files": sorted(runtime_files),
    },
    "graph": {
        "nodes": len(nodes),
        "links": len(links),
    },
    "self_model": {
        "runtime_nodes_detected": len(runtime_nodes),
        "runtime_connections_detected": len(connections),
    },
    "runtime_nodes": [
        {
            "id": n.get("id"),
            "label": n.get("label"),
            "type": n.get("type"),
            "file": n.get("file"),
            "path": n.get("path"),
        }
        for n in runtime_nodes
    ],
    "connections": connections[:500],
    "status": "PASS"
    if runtime_nodes and connections
    else "PARTIAL",
}

output = OUT / "gate14_5_self_analysis_runtime.json"

output.write_text(
    json.dumps(analysis, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 64)
print("NUSANTARA GATE 14.5.1 - RUNTIME SELF ANALYSIS")
print("=" * 64)
print("Runtime modules          :", analysis["runtime"]["modules"])
print("Runtime files            :", len(runtime_files))
print("Graph nodes              :", len(nodes))
print("Graph links              :", len(links))
print("Runtime nodes detected   :", len(runtime_nodes))
print("Runtime connections      :", len(connections))
print("STATUS                   :", analysis["status"])
print("Output                   :", output)
