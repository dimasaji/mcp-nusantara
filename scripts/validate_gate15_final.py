import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

def load(name):
    path = OUT / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))

gate14 = load("gate14_final_contract.json")
gate151 = load("gate15_1_runtime_health_truth.json")
gate152 = load("gate15_2_engine_runtime_truth.json")
gate153 = load("gate15_3_graph_operational_truth.json")
gate154 = load("gate15_4_operational_truth.json")

checks = {
    "gate14_final": gate14.get("status") == "PASS",
    "gate15_1_runtime_health": gate151.get("status") == "PASS",
    "gate15_2_engine_runtime": gate152.get("status") == "PASS",
    "gate15_3_graph_operational": gate153.get("status") == "PASS",
    "gate15_4_operational_synthesis": gate154.get("status") == "PASS",
}

passed = sum(checks.values())
total = len(checks)
status = "PASS" if passed == total else "FAIL"

graph = gate153.get("graph", {})
operational = gate154.get("operational_truth", {})

result = {
    "gate": "15",
    "name": "Nusantara Operational Intelligence",
    "version": "15.0.0-final",
    "timestamp": datetime.now().isoformat(),
    "status": status,

    "checks": {
        "passed": passed,
        "total": total,
        "results": checks,
    },

    "foundation": {
        "gate14": "PASS" if checks["gate14_final"] else "FAIL",
        "runtime_health": "PASS" if checks["gate15_1_runtime_health"] else "FAIL",
        "engine_runtime": "PASS" if checks["gate15_2_engine_runtime"] else "FAIL",
        "graph_operational": "PASS" if checks["gate15_3_graph_operational"] else "FAIL",
        "operational_synthesis": "PASS" if checks["gate15_4_operational_synthesis"] else "FAIL",
    },

    "system": {
        "status": operational.get("system_status"),
        "graph_nodes": graph.get("nodes", 0),
        "graph_links": graph.get("links", 0),
        "llm": operational.get("llm", {}),
    },

    "capabilities": {
        "runtime_health_truth": True,
        "engine_runtime_truth": True,
        "graph_operational_truth": True,
        "operational_synthesis": True,
        "developer_core": checks["gate14_final"],
        "self_analysis": True,
        "impact_analysis": True,
        "deterministic_change_query": True,
        "llm_required_for_validation": False,
    },

    "contract": {
        "gate14_must_remain_pass": True,
        "all_gate15_layers_must_pass": True,
        "operational_truth_must_be_deterministic": True,
        "validation_must_not_require_llm": True,
        "graph_schema": "nodes + links",
        "runtime_status_must_be_traceable": True,
    },
}

output = OUT / "gate15_final_contract.json"

output.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 70)
print("NUSANTARA GATE 15 - FINAL CONTRACT")
print("=" * 70)
print()

for name, value in checks.items():
    print(f"{name:<35}", "PASS" if value else "FAIL")

print()
print("Validation checks :", f"{passed} / {total}")
print("System status     :", operational.get("system_status"))
print("Graph nodes       :", graph.get("nodes", 0))
print("Graph links       :", graph.get("links", 0))
print("LLM               :", operational.get("llm", {}).get("model"))
print()
print("GATE 15 FINAL     :", status)
print("Output            :", output)

if status != "PASS":
    raise SystemExit(1)
