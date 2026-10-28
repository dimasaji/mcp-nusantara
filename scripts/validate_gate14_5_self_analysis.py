import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

graph = json.loads((OUT / "graph.json").read_text(encoding="utf-8"))
truth = json.loads((OUT / "gate14_runtime_graph_truth.json").read_text(encoding="utf-8"))
connectivity = json.loads((OUT / "gate14_3_runtime_graph_connectivity.json").read_text(encoding="utf-8"))
manifest = json.loads((OUT / "gate14_4_runtime_graph_manifest.json").read_text(encoding="utf-8"))

nodes = graph.get("nodes", [])
links = graph.get("links", [])

runtime_targets = truth.get("runtime_graph_targets", {})
runtime_modules = truth.get("runtime", {}).get("modules", [])

analysis = {
    "gate": "14.5",
    "engine": "Developer Core Self-Analysis",
    "version": "14.5.0",
    "timestamp": datetime.now().isoformat(),
    "source_of_truth": str(ROOT),
    "graph": {
        "nodes": len(nodes),
        "links": len(links),
    },
    "runtime": {
        "module_count": len(runtime_modules),
        "target_groups": len(runtime_targets),
        "target_entries": sum(len(v) for v in runtime_targets.values()),
    },
    "connectivity": {
        "status": connectivity.get("status", "UNKNOWN"),
        "checks": connectivity.get("checks_passed", connectivity.get("checks", 3)),
    },
    "manifest": {
        "status": "AVAILABLE",
        "gate": manifest.get("gate"),
    },
    "self_analysis": {
        "runtime_known": len(runtime_modules) > 0,
        "graph_known": len(nodes) > 0 and len(links) > 0,
        "connectivity_known": connectivity.get("status") == "PASS",
        "manifest_known": manifest.get("gate") == "14.4",
    },
}

checks = [
    analysis["self_analysis"]["runtime_known"],
    analysis["self_analysis"]["graph_known"],
    analysis["self_analysis"]["connectivity_known"],
    analysis["self_analysis"]["manifest_known"],
]

analysis["checks"] = {
    "passed": sum(checks),
    "total": len(checks),
}

analysis["status"] = "PASS" if all(checks) else "FAIL"

output = OUT / "gate14_5_self_analysis.json"
output.write_text(
    json.dumps(analysis, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 64)
print("NUSANTARA GATE 14.5 - DEVELOPER CORE SELF-ANALYSIS")
print("=" * 64)
print(f"Runtime modules    : {len(runtime_modules)}")
print(f"Runtime target     : {sum(len(v) for v in runtime_targets.values())}")
print(f"Graph nodes        : {len(nodes)}")
print(f"Graph links        : {len(links)}")
print(f"Connectivity       : {connectivity.get('status', 'UNKNOWN')}")
print(f"Manifest           : {manifest.get('gate', 'UNKNOWN')}")
print(f"Checks             : {sum(checks)}/{len(checks)}")
print(f"GATE 14.5 STATUS   : {analysis['status']}")
print(f"Output             : {output}")
