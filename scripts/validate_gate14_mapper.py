from pathlib import Path
import json

from app.developer_core.mapper import RuntimeGraphMapper
from app.developer_core.impact import RuntimeImpactAnalyzer


print("=" * 64)
print("NUSANTARA GATE 14.2 - RUNTIME GRAPH MAPPING")
print("=" * 64)

graph = Path("graphify-out/graph.json")

print("Graphify :", graph)
print("Exists   :", graph.exists())

mapper = RuntimeGraphMapper(graph)

runtime_gates = {
    "language": {
        "status": "active",
        "confidence": 0.903062,
    },
    "problem": {
        "status": "active",
    },
    "knowledge": {
        "status": "grounded",
    },
    "reasoning": {
        "status": "grounded",
        "confidence": 0.755518,
    },
    "policy": {
        "status": "allow",
    },
    "memory": {
        "status": "active",
    },
    "action": {
        "status": "observed",
    },
    "orchestration": {
        "status": "completed",
    },
    "developer_core": {
        "status": "active",
    },
}

orchestration = {
    "stages": [
        "language",
        "problem",
        "reasoning",
        "policy",
        "memory",
    ]
}

mapping = mapper.map_runtime(
    gates=runtime_gates,
    orchestration=orchestration,
)

print("")
print("GRAPH")
print("  Loaded nodes       :", mapping["graph"]["total_nodes"])
print("  Loaded edges       :", mapping["graph"]["total_edges"])
print("  Matched nodes      :", mapping["graph"]["matched_nodes"])
print("  Related edges      :", mapping["graph"]["related_edges"])

print("")
print("ENGINE MAPPING")

for name, item in mapping["mappings"].items():
    print(
        f"  {name:<18} "
        f"{item['node_count']} node(s)"
    )

impact = RuntimeImpactAnalyzer(graph)
impact_result = impact.analyze_mapping(mapping)

print("")
print("IMPACT")
print(
    "  Dependencies       :",
    impact_result["dependency"]["count"],
)
print(
    "  Dependents         :",
    impact_result["dependents"]["count"],
)
print(
    "  Impact count       :",
    impact_result["risk"]["impact_count"],
)
print(
    "  Risk               :",
    impact_result["risk"]["level"],
)

print("")
print("MODE")
print("  Mapper             : read-only")
print("  Impact             : read-only")
print("  Existing graph     : preserved")

if mapping["mapper"]["graph_loaded"]:
    print("")
    print("GATE 14.2 : PASS")
else:
    print("")
    print("GATE 14.2 : DEGRADED")

print("=" * 64)
