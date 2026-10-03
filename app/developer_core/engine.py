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
