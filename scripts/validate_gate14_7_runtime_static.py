import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

graph = json.loads((OUT / "graph.json").read_text(encoding="utf-8"))
truth = json.loads((OUT / "gate14_runtime_graph_truth.json").read_text(encoding="utf-8"))

nodes = graph.get("nodes", [])
node_map = {
    str(n.get("id")): n
    for n in nodes
    if n.get("id") is not None
}

runtime_modules = truth.get("runtime", {}).get("modules", [])

results = []

for module in runtime_modules:
    module_name = module.get("module", "")
    file_path = module.get("file", "")

    filename = Path(file_path).name if file_path else ""

    matches = []

    for node_id, node in node_map.items():
        text = " ".join(
            str(node.get(k, "") or "")
            for k in (
                "id",
                "name",
                "label",
                "path",
                "file",
                "module"
            )
        ).lower()

        if (
            module_name.lower() in text
            or filename.lower() in text
        ):
            matches.append({
                "id": node_id,
                "label": node.get("label"),
                "type": node.get("type")
            })

    status = "PASS" if matches else "FAIL"

    results.append({
        "runtime_module": module_name,
        "runtime_file": file_path,
        "graph_matches": matches[:20],
        "match_count": len(matches),
        "status": status
    })

passed = sum(
    1 for r in results
    if r["status"] == "PASS"
)

total = len(results)

result = {
    "gate": "14.7",
    "engine": "Runtime Static Consistency",
    "version": "14.7.0",
    "timestamp": datetime.now().isoformat(),
    "source_of_truth": str(ROOT),

    "graph": {
        "nodes": len(nodes),
        "links": len(graph.get("links", []))
    },

    "runtime": {
        "modules": total
    },

    "consistency": {
        "passed": passed,
        "total": total,
        "results": results
    },

    "status": "PASS" if passed == total else "FAIL"
}

output = OUT / "gate14_7_runtime_static_consistency.json"

output.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 64)
print("NUSANTARA GATE 14.7 - RUNTIME <-> STATIC CONSISTENCY")
print("=" * 64)
print("Graph nodes          :", len(nodes))
print("Graph links          :", len(graph.get("links", [])))
print("Runtime modules      :", total)
print("Consistency          :", passed, "/", total)

print()

for item in results:
    print(
        f"{item['status']:<5} "
        f"{item['runtime_module']:<42} "
        f"matches={item['match_count']}"
    )

print()
print("GATE 14.7 STATUS     :", result["status"])
print("Output               :", output)
