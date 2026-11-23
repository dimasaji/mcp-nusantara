from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.developer_core.engine import DeveloperCoreEngine
from app.developer_core.graph_bridge import GraphifyBridge


print("=" * 60)
print("NUSANTARA GATE 14 - DEVELOPER CORE / GRAPH")
print("=" * 60)

graph = ROOT / "graphify-out" / "graph.json"

print("Graphify:", graph)
print("Exists  :", graph.exists())

if graph.exists():
    try:
        data = json.loads(graph.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        print("Nodes   :", len(nodes) if isinstance(nodes, list) else 0)
        print("Edges   :", len(edges) if isinstance(edges, list) else 0)
    except Exception as exc:
        print("Graph JSON error:", exc)

engine = DeveloperCoreEngine(graph)

runtime = {
    "8": {"status": "grounded"},
    "9": {"status": "allow"},
    "10": {"status": "active"},
    "11": {"status": "ready"},
    "12": {"status": "preserved"},
    "13": {"status": "completed"},
    "14": {"status": "active"},
}

result = engine.self_analyze(runtime_gates=runtime)

print("")
print("Developer Core :", result["developer_core"]["status"])
print("Graph loaded   :", result["graphify"]["loaded"])
print("Node count     :", result["graphify"]["nodes"])
print("Edge count     :", result["graphify"]["edges"])
print("Engine count   :", len(result["engines"]))
print("Risk count     :", len(result["risks"]))

print("")
print("GATES:")
for gate, item in result["gates"].items():
    print(
        f"  GATE {gate:<2} "
        f"{item['name']:<30} "
        f"{item['status']}"
    )

print("")
print("BRIDGE:")
bridge = GraphifyBridge(graph)
print(bridge.summary())

print("")
if result["developer_core"]["status"] == "ready":
    print("GATE 14 : PASS")
else:
    print("GATE 14 : DEGRADED")

print("=" * 60)
