from pathlib import Path

files = {}

files["app/developer_core/engine.py"] = r'''
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any


@dataclass
class DeveloperAnalysis:
    status: str
    graph_loaded: bool
    node_count: int
    edge_count: int
    gates: dict[str, Any] = field(default_factory=dict)
    engines: list[dict[str, Any]] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "graph_loaded": self.graph_loaded,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "gates": self.gates,
            "engines": self.engines,
            "risks": self.risks,
            "recommendations": self.recommendations,
        }


class DeveloperCoreEngine:
    """
    Gate 14 Developer Core.

    Tidak membuat graph baru.
    Mengonsumsi Graphify graph.json yang sudah ada.
    """

    VERSION = "14.0.0-graphify-native"

    GATES = {
        8: "Reasoning Engine",
        9: "Decision / Policy Engine",
        10: "Memory / Context Engine",
        11: "Tool / Action Engine",
        12: "Existing Tools",
        13: "Workflow / Orchestration",
        14: "Developer Core / Graph",
    }

    ENGINE_PATHS = {
        "Language Engine": "app/language",
        "Problem Engine": "app/problem",
        "Knowledge / RAG": "app/knowledge",
        "Reasoning Engine": "app/reasoning",
        "Policy Engine": "app/policy",
        "Memory Engine": "app/memory",
        "Action Engine": "app/action",
        "Orchestration Engine": "app/orchestration",
        "Developer Core": "app/developer_core",
    }

    def __init__(self, graph_path: str | Path = "graphify-out/graph.json"):
        self.graph_path = Path(graph_path)

    def _load_graph(self) -> dict[str, Any]:
        if not self.graph_path.exists():
            return {}

        try:
            data = json.loads(
                self.graph_path.read_text(encoding="utf-8")
            )
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _count_graph(data: dict[str, Any]) -> tuple[int, int]:
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        if not isinstance(nodes, list):
            nodes = []

        if not isinstance(edges, list):
            edges = []

        return len(nodes), len(edges)

    def _engine_inventory(self) -> list[dict[str, Any]]:
        result = []

        for name, path_text in self.ENGINE_PATHS.items():
            path = Path(path_text)

            if path.exists():
                py_files = list(path.rglob("*.py"))
                result.append(
                    {
                        "name": name,
                        "path": path_text,
                        "exists": True,
                        "python_files": len(py_files),
                        "status": "active" if py_files else "empty",
                    }
                )
            else:
                result.append(
                    {
                        "name": name,
                        "path": path_text,
                        "exists": False,
                        "python_files": 0,
                        "status": "missing",
                    }
                )

        return result

    def analyze(
        self,
        *,
        runtime_gates: dict[str, Any] | None = None,
    ) -> DeveloperAnalysis:
        graph = self._load_graph()
        nodes, edges = self._count_graph(graph)

        graph_loaded = bool(graph)

        engines = self._engine_inventory()

        gates = {
            str(gate): {
                "name": name,
                "status": (
                    runtime_gates.get(str(gate), {}).get("status", "known")
                    if runtime_gates
                    else "known"
                ),
            }
            for gate, name in self.GATES.items()
        }

        risks: list[dict[str, Any]] = []
        recommendations: list[str] = []

        if not graph_loaded:
            risks.append(
                {
                    "type": "graph_unavailable",
                    "severity": "high",
                    "message": "Graphify graph.json tidak tersedia atau tidak dapat dibaca.",
                }
            )
            recommendations.append(
                "Jalankan generator Graphify yang sudah ada sebelum self-analysis."
            )

        missing = [
            item["name"]
            for item in engines
            if not item["exists"]
        ]

        if missing:
            risks.append(
                {
                    "type": "missing_engine_path",
                    "severity": "medium",
                    "message": "Engine path berikut tidak ditemukan.",
                    "items": missing,
                }
            )

        if graph_loaded and nodes == 0:
            risks.append(
                {
                    "type": "empty_graph",
                    "severity": "high",
                    "message": "Graphify graph berhasil dibaca tetapi tidak memiliki node.",
                }
            )

        if graph_loaded:
            recommendations.append(
                "Gunakan graph dependency untuk impact analysis sebelum perubahan source."
            )
            recommendations.append(
                "Gunakan runtime gate status untuk menghubungkan kondisi runtime dengan source graph."
            )

        status = "ready" if graph_loaded and not any(
            r.get("severity") == "high" for r in risks
        ) else "degraded"

        return DeveloperAnalysis(
            status=status,
            graph_loaded=graph_loaded,
            node_count=nodes,
            edge_count=edges,
            gates=gates,
            engines=engines,
            risks=risks,
            recommendations=recommendations,
        )

    def self_analyze(
        self,
        *,
        runtime_gates: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        analysis = self.analyze(runtime_gates=runtime_gates)

        return {
            "developer_core": {
                "version": self.VERSION,
                "status": analysis.status,
            },
            "graphify": {
                "path": str(self.graph_path),
                "loaded": analysis.graph_loaded,
                "nodes": analysis.node_count,
                "edges": analysis.edge_count,
            },
            "gates": analysis.gates,
            "engines": analysis.engines,
            "risks": analysis.risks,
            "recommendations": analysis.recommendations,
        }
'''


files["app/developer_core/graph_bridge.py"] = r'''
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.developer_core.engine import DeveloperCoreEngine


class GraphifyBridge:
    """
    Adapter Gate 14 ke Graphify existing.

    Prinsip:
    - read-only terhadap graph.json
    - tidak mengganti schema Graphify
    - dapat menambahkan runtime metadata secara terpisah
    """

    VERSION = "14.0.0-graph-bridge"

    def __init__(
        self,
        graph_path: str | Path = "graphify-out/graph.json",
    ):
        self.graph_path = Path(graph_path)
        self.core = DeveloperCoreEngine(self.graph_path)

    def inspect(
        self,
        *,
        runtime_gates: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = self.core.self_analyze(
            runtime_gates=runtime_gates,
        )

        result["graph_bridge"] = {
            "version": self.VERSION,
            "mode": "read-only",
            "graph_path": str(self.graph_path),
        }

        return result

    def graph_exists(self) -> bool:
        return self.graph_path.exists()

    def summary(self) -> dict[str, Any]:
        analysis = self.core.analyze()

        return {
            "status": analysis.status,
            "graph_loaded": analysis.graph_loaded,
            "nodes": analysis.node_count,
            "edges": analysis.edge_count,
            "engine_count": len(analysis.engines),
            "risk_count": len(analysis.risks),
        }
'''


files["tests/test_gate14_developer_core.py"] = r'''
from pathlib import Path

from app.developer_core.engine import DeveloperCoreEngine
from app.developer_core.graph_bridge import GraphifyBridge


def test_gate14_engine_loads():
    engine = DeveloperCoreEngine()

    result = engine.self_analyze()

    assert "developer_core" in result
    assert result["developer_core"]["version"].startswith("14.")


def test_gate14_engine_inventory():
    engine = DeveloperCoreEngine()

    result = engine.self_analyze()

    names = {
        item["name"]
        for item in result["engines"]
    }

    assert "Reasoning Engine" in names
    assert "Policy Engine" in names
    assert "Memory Engine" in names
    assert "Action Engine" in names
    assert "Orchestration Engine" in names


def test_gate14_graph_bridge():
    bridge = GraphifyBridge()

    result = bridge.inspect()

    assert "graph_bridge" in result
    assert result["graph_bridge"]["mode"] == "read-only"


def test_gate14_existing_graphify():
    path = Path("graphify-out/graph.json")

    if not path.exists():
        return

    bridge = GraphifyBridge(path)

    result = bridge.inspect()

    assert result["graphify"]["loaded"] is True
    assert result["graphify"]["nodes"] > 0


def test_gate14_runtime_gate_mapping():
    engine = DeveloperCoreEngine()

    runtime = {
        "8": {"status": "grounded"},
        "9": {"status": "allow"},
        "10": {"status": "active"},
        "11": {"status": "ready"},
        "12": {"status": "preserved"},
        "13": {"status": "completed"},
        "14": {"status": "active"},
    }

    result = engine.self_analyze(
        runtime_gates=runtime
    )

    assert result["gates"]["8"]["status"] == "grounded"
    assert result["gates"]["9"]["status"] == "allow"
    assert result["gates"]["13"]["status"] == "completed"
'''


files["scripts/validate_gate14.py"] = r'''
from pathlib import Path
import json

from app.developer_core.engine import DeveloperCoreEngine
from app.developer_core.graph_bridge import GraphifyBridge


print("=" * 60)
print("NUSANTARA GATE 14 - DEVELOPER CORE / GRAPH")
print("=" * 60)

graph = Path("graphify-out/graph.json")

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

result = engine.self_analyze(
    runtime_gates=runtime
)

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
'''


files["app/developer_core/__init__.py"] = r'''
from .engine import DeveloperCoreEngine, DeveloperAnalysis
from .graph_bridge import GraphifyBridge

__all__ = [
    "DeveloperCoreEngine",
    "DeveloperAnalysis",
    "GraphifyBridge",
]
'''


for filename, content in files.items():
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")
    print("CREATED:", filename)

print("")
print("GATE 14 SOURCE BUILD : PASS")
