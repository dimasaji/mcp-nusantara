from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "graphify-out" / "graph.json"
RUNTIME = ROOT / "graphify-out" / "runtime_object_truth.json"
E2E = ROOT / "graphify-out" / "runtime_e2e_lite.json"
OUT = ROOT / "graphify-out" / "gate14_runtime_graph_truth.json"

graph = json.loads(GRAPH.read_text(encoding="utf-8"))
runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
e2e = json.loads(E2E.read_text(encoding="utf-8"))

nodes = graph.get("nodes", [])
edges = graph.get("links", graph.get("edges", []))

node_text = []

for n in nodes:
    text = " ".join(
        str(n.get(k, ""))
        for k in ["id", "name", "label", "file", "path", "module", "type"]
    ).lower()
    node_text.append((n, text))

targets = [
    "routes.py",
    "language/engine.py",
    "problem/engine.py",
    "knowledge/engine.py",
    "reasoning/engine.py",
    "graph_bridge.py",
    "gate_integration.py",
    "rag.py",
    "developer_core/engine.py",
]

matches = {}

for target in targets:
    found = []

    for node, text in node_text:
        if target.lower() in text:
            found.append({
                "id": node.get("id"),
                "name": node.get("name"),
                "label": node.get("label"),
                "file": node.get("file"),
                "path": node.get("path"),
                "module": node.get("module"),
                "type": node.get("type")
            })

    matches[target] = found

runtime_modules = []

for module, data in runtime.get("results", {}).items():
    if isinstance(data, dict):
        runtime_modules.append({
            "module": module,
            "file": data.get("file"),
            "objects": list(
                (data.get("objects") or {}).keys()
            )
        })

e2e_status = e2e.get("status")
e2e_http = e2e.get("http_status")
e2e_latency = e2e.get("latency_ms")

resolved = sum(
    1 for target, found in matches.items()
    if found
)

output = {
    "gate": "14.2",
    "engine": "Developer Core Runtime Graph Truth",
    "version": "14.2.0",
    "source_of_truth": str(ROOT),
    "graph": {
        "nodes": len(nodes),
        "edges": len(edges)
    },
    "runtime": {
        "modules": runtime_modules
    },
    "e2e": {
        "status": e2e_status,
        "http_status": e2e_http,
        "latency_ms": e2e_latency
    },
    "runtime_graph_targets": matches,
    "targets_total": len(targets),
    "targets_resolved": resolved,
    "status": "PASS" if resolved == len(targets) and e2e_status == "PASS" else "NEEDS_INVESTIGATION"
}

OUT.write_text(
    json.dumps(output, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 72)
print("NUSANTARA GATE 14.2 — RUNTIME GRAPH TRUTH")
print("=" * 72)

print()
print(f"Graph nodes       : {len(nodes)}")
print(f"Graph edges       : {len(edges)}")
print(f"E2E status        : {e2e_status}")
print(f"E2E HTTP          : {e2e_http}")
print(f"E2E latency       : {e2e_latency} ms")

print()
print("RUNTIME GRAPH TARGETS")
print("-" * 72)

for target, found in matches.items():
    status = "RESOLVED" if found else "MISSING"
    print(f"{target:<32} {status:<10} matches={len(found)}")

print()
print("-" * 72)
print(f"RESOLVED          : {resolved}/{len(targets)}")

status = (
    "PASS"
    if resolved == len(targets) and e2e_status == "PASS"
    else "NEEDS INVESTIGATION"
)

print(f"GATE 14.2 STATUS  : {status}")
print(f"Output            : {OUT}")
print("GATE 14.2 RUNTIME GRAPH TRUTH: COMPLETE")



