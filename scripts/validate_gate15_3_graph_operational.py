import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

GRAPH_FILE = OUT / "graph.json"
ENGINE_FILE = OUT / "gate15_2_engine_runtime_truth.json"
HEALTH_FILE = OUT / "gate15_1_runtime_health_truth.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


print("=" * 68)
print("NUSANTARA GATE 15.3 - GRAPH OPERATIONAL TRUTH")
print("=" * 68)

graph = load(GRAPH_FILE)
engines = load(ENGINE_FILE)
health = load(HEALTH_FILE)

nodes = graph.get("nodes", [])
links = graph.get("links", [])

node_text = {}

for node in nodes:
    node_id = str(node.get("id", ""))
    node_text[node_id] = " ".join(
        str(node.get(k, "") or "")
        for k in (
            "id",
            "name",
            "label",
            "module",
            "path",
            "file",
        )
    ).lower()

results = {}

for name, engine in engines.get("engines", {}).items():

    module_name = engine.get("module", "")
    class_name = engine.get("class", "")

    candidates = [
        module_name.lower(),
        class_name.lower(),
        Path(
            engine.get("file", "")
        ).name.lower(),
    ]

    matches = []

    for node_id, text in node_text.items():
        if any(
            candidate
            and candidate in text
            for candidate in candidates
        ):
            matches.append(node_id)

    results[name] = {
        "module": module_name,
        "class": class_name,
        "graph_matches": matches[:20],
        "match_count": len(matches),
        "status": "PASS" if matches else "FAIL",
    }

    print(
        f"{results[name]['status']:<5} "
        f"{name:<24} "
        f"matches={len(matches)}"
    )

# Validate graph structure itself.
graph_truth = (
    isinstance(nodes, list)
    and isinstance(links, list)
    and len(nodes) > 0
    and len(links) > 0
)

print()
print(
    "Graph nodes          :",
    len(nodes)
)

print(
    "Graph links          :",
    len(links)
)

print(
    "Graph structure      :",
    "PASS" if graph_truth else "FAIL"
)

engine_pass = sum(
    1
    for item in results.values()
    if item["status"] == "PASS"
)

engine_total = len(results)

all_engines = engine_pass == engine_total

checks = {
    "graph_structure": graph_truth,
    "engine_representation": all_engines,
    "runtime_health": (
        health.get("status") == "PASS"
    ),
    "engine_runtime_truth": (
        engines.get("status") == "PASS"
    ),
}

passed = sum(
    1
    for value in checks.values()
    if value
)

total = len(checks)

status = "PASS" if passed == total else "FAIL"

result = {
    "gate": "15.3",
    "name": "Graph Operational Truth",
    "version": "15.3.0",
    "timestamp": datetime.now().isoformat(),
    "status": status,

    "checks": {
        "passed": passed,
        "total": total,
        "results": checks,
    },

    "graph": {
        "nodes": len(nodes),
        "links": len(links),
        "schema": "nodes + links",
    },

    "engines": results,

    "contract": {
        "graph_must_use_links": True,
        "graph_must_contain_nodes": True,
        "runtime_engines_must_have_graph_representation": True,
        "runtime_health_must_be_pass": True,
        "engine_runtime_truth_must_be_pass": True,
    },
}

output = OUT / "gate15_3_graph_operational_truth.json"

output.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print()
print("Validation checks   :", f"{passed} / {total}")
print("GATE 15.3 STATUS    :", status)
print("Output              :", output)

if status != "PASS":
    raise SystemExit(1)
