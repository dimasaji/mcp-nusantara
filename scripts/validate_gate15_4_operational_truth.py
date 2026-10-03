import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

FILES = {
    "health": OUT / "gate15_1_runtime_health_truth.json",
    "engines": OUT / "gate15_2_engine_runtime_truth.json",
    "graph": OUT / "gate15_3_graph_operational_truth.json",
    "gate14": OUT / "gate14_final_contract.json",
}


def load(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


health = load(FILES["health"])
engines = load(FILES["engines"])
graph = load(FILES["graph"])
gate14 = load(FILES["gate14"])

print("=" * 70)
print("NUSANTARA GATE 15.4 - OPERATIONAL SYNTHESIS")
print("=" * 70)

health_pass = health.get("status") == "PASS"
engine_pass = engines.get("status") == "PASS"
graph_pass = graph.get("status") == "PASS"
gate14_pass = gate14.get("status") == "PASS"

checks = {
    "runtime_health": health_pass,
    "engine_runtime": engine_pass,
    "graph_operational": graph_pass,
    "gate14_contract": gate14_pass,
}

passed = sum(checks.values())
total = len(checks)

status = "PASS" if passed == total else "FAIL"

components = (
    health
    .get("runtime", {})
    .get("detail", {})
    .get("components", {})
)

llm = (
    health
    .get("runtime", {})
    .get("detail", {})
    .get("llm", {})
)

engine_results = engines.get("engines", {})

operational_components = {}

for name, state in components.items():
    operational_components[name] = {
        "status": state,
        "available": state == "available",
    }

for name, item in engine_results.items():
    operational_components[name] = {
        "status": "available"
        if item.get("status") == "PASS"
        else "unavailable",
        "available": item.get("status") == "PASS",
        "module": item.get("module"),
        "class": item.get("class"),
        "file": item.get("file"),
    }

result = {
    "gate": "15.4",
    "name": "Operational Synthesis",
    "version": "15.4.0",
    "timestamp": datetime.now().isoformat(),

    "status": status,

    "checks": {
        "passed": passed,
        "total": total,
        "results": checks,
    },

    "operational_truth": {
        "system_status": "healthy" if status == "PASS" else "degraded",

        "api": {
            "status": "healthy"
            if health_pass
            else "unknown",
        },

        "llm": {
            "status": llm.get("status"),
            "available": llm.get("available"),
            "model": llm.get("model"),
            "latency_ms": llm.get("latency_ms"),
        },

        "components": operational_components,

        "graph": {
            "status": "healthy"
            if graph_pass
            else "unknown",
            "nodes": graph
            .get("graph", {})
            .get("nodes", 0),
            "links": graph
            .get("graph", {})
            .get("links", 0),
        },

        "developer_core": {
            "gate14_final": gate14_pass,
            "self_analysis": gate14
            .get("capabilities", {})
            .get("self_analysis", False),
            "impact_analysis": gate14
            .get("capabilities", {})
            .get("impact_analysis", False),
            "deterministic_change_query": gate14
            .get("capabilities", {})
            .get("deterministic_change_query", False),
        },
    },

    "source_of_truth": {
        "runtime_health": str(FILES["health"]),
        "engine_runtime": str(FILES["engines"]),
        "graph_operational": str(FILES["graph"]),
        "developer_core_contract": str(FILES["gate14"]),
        "llm_inference_required": False,
    },

    "contract": [
        "Operational truth must combine runtime health, engine runtime and graph truth.",
        "Developer Core Gate 14 must remain valid.",
        "Operational synthesis must be deterministic.",
        "Operational synthesis must not require LLM inference.",
        "Every operational status must be traceable to a validated source.",
    ],
}

output = OUT / "gate15_4_operational_truth.json"

output.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print()
print("Runtime Health      :", "PASS" if health_pass else "FAIL")
print("Engine Runtime      :", "PASS" if engine_pass else "FAIL")
print("Graph Operational   :", "PASS" if graph_pass else "FAIL")
print("Gate 14 Contract    :", "PASS" if gate14_pass else "FAIL")

print()
print("Checks              :", f"{passed} / {total}")
print("System Status       :", result["operational_truth"]["system_status"])
print("Graph Nodes         :", result["operational_truth"]["graph"]["nodes"])
print("Graph Links         :", result["operational_truth"]["graph"]["links"])
print("LLM                 :", llm.get("model"))
print()
print("GATE 15.4 STATUS    :", status)
print("Output              :", output)

if status != "PASS":
    raise SystemExit(1)
