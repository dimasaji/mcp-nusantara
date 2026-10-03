import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

FILES = {
    "graph": OUT / "graph.json",
    "impact_truth": OUT / "gate14_6_2_impact_truth.json",
    "self_analysis": OUT / "gate14_5_self_analysis_runtime.json",
    "consistency": OUT / "gate14_7_runtime_static_consistency.json",
    "change_query": OUT / "gate14_8_change_query_last.json",
}

def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

print("=" * 72)
print("NUSANTARA GATE 14 FINAL CONTRACT")
print("DEVELOPER CORE ENGINE")
print("=" * 72)

graph = load_json(FILES["graph"])
impact = load_json(FILES["impact_truth"])
self_analysis = load_json(FILES["self_analysis"])
consistency = load_json(FILES["consistency"])
change_query = load_json(FILES["change_query"])

nodes = graph.get("nodes", [])
links = graph.get("links", [])

checks = {}

# 1. Graph truth
checks["graph_truth"] = (
    FILES["graph"].exists()
    and len(nodes) > 0
    and len(links) > 0
)

# 2. Self-analysis
checks["self_analysis"] = (
    FILES["self_analysis"].exists()
    and str(self_analysis.get("status", "")).upper() == "PASS"
)

# 3. Impact analysis
checks["impact_analysis"] = (
    FILES["impact_truth"].exists()
    and str(impact.get("status", "")).upper() == "PASS"
)

# 4. Runtime/static consistency
checks["runtime_static_consistency"] = (
    FILES["consistency"].exists()
    and str(consistency.get("status", "")).upper() == "PASS"
)

# 5. Deterministic change query
query_source = change_query.get("source", {})

checks["deterministic_change_query"] = (
    FILES["change_query"].exists()
    and str(change_query.get("status", "")).upper() == "PASS"
    and query_source.get("deterministic") is True
    and query_source.get("llm_used") is False
)

# 6. Traceability
checks["traceability"] = (
    bool(query_source.get("graph"))
    and Path(query_source.get("graph", "")).resolve()
    == FILES["graph"].resolve()
)

print(
    "01 Graph Truth                  :",
    "PASS" if checks["graph_truth"] else "FAIL"
)

print(
    "02 Self Analysis                :",
    "PASS" if checks["self_analysis"] else "FAIL"
)

print(
    "03 Impact Analysis              :",
    "PASS" if checks["impact_analysis"] else "FAIL"
)

print(
    "04 Runtime <-> Static           :",
    "PASS" if checks["runtime_static_consistency"] else "FAIL"
)

print(
    "05 Deterministic Change Query   :",
    "PASS" if checks["deterministic_change_query"] else "FAIL"
)

print(
    "06 Evidence Traceability        :",
    "PASS" if checks["traceability"] else "FAIL"
)

passed = sum(checks.values())
total = len(checks)

status = "PASS" if passed == total else "FAIL"

contract = {
    "gate": "14-FINAL",
    "name": "Nusantara Developer Core Engine Contract",
    "version": "14.0-final",
    "status": status,

    "capabilities": {
        "self_analysis": checks["self_analysis"],
        "impact_analysis": checks["impact_analysis"],
        "deterministic_change_query":
            checks["deterministic_change_query"],
        "runtime_static_consistency":
            checks["runtime_static_consistency"],
        "graph_truth":
            checks["graph_truth"],
        "evidence_traceability":
            checks["traceability"],
    },

    "validation": {
        "passed": passed,
        "total": total,
        "checks": checks,
    },

    "graph": {
        "nodes": len(nodes),
        "links": len(links),
    },

    "last_change_query": {
        "query": change_query.get("query"),
        "target": change_query.get("target"),
        "impact_count": (
            change_query
            .get("analysis", {})
            .get("impact_count", 0)
        ),
        "deterministic":
            query_source.get("deterministic"),
        "llm_used":
            query_source.get("llm_used"),
    },

    "contract_rules": [
        "Developer Core uses runtime and static truth.",
        "Self-analysis is based on actual system structure.",
        "Impact analysis preserves SOURCE -> TARGET direction.",
        "Impact analysis uses approved dependency relations.",
        "Change queries are deterministic.",
        "Change queries do not require LLM inference.",
        "Results are traceable to graph.json.",
        "Runtime and static representations remain consistent.",
    ],
}

output = OUT / "gate14_final_contract.json"

output.write_text(
    json.dumps(contract, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print()
print("-" * 72)
print("VALIDATION CHECKS :", f"{passed} / {total}")
print("GRAPH NODES       :", len(nodes))
print("GRAPH LINKS       :", len(links))
print("LAST QUERY        :", change_query.get("query"))
print("IMPACT COUNT      :", contract["last_change_query"]["impact_count"])
print("LLM USED          :", query_source.get("llm_used"))
print()
print("GATE 14 FINAL     :", status)
print("OUTPUT            :", output)

if status != "PASS":
    raise SystemExit(1)
