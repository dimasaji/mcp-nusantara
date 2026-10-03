from pathlib import Path

FILES = {
    "app/developer_core/mapper.py": r'''
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re


class RuntimeGraphMapper:
    """
    Gate 14.2 Runtime -> Graphify Mapper.

    Membaca graphify-out/graph.json secara READ-ONLY.
    Tidak mengubah graph existing.
    """

    VERSION = "14.2.0-runtime-graph-mapper"

    ENGINE_ALIASES = {
        "language": [
            "language",
            "intent",
            "normalizer",
            "entity",
        ],
        "problem": [
            "problem",
            "classifier",
            "detector",
        ],
        "knowledge": [
            "knowledge",
            "rag",
            "retriev",
            "grounding",
            "embedding",
        ],
        "reasoning": [
            "reasoning",
        ],
        "policy": [
            "policy",
            "decision",
        ],
        "memory": [
            "memory",
            "context",
        ],
        "action": [
            "action",
            "tool",
        ],
        "orchestration": [
            "orchestration",
            "workflow",
        ],
        "developer_core": [
            "developer_core",
            "graph_bridge",
            "runtime",
            "mapper",
            "impact",
        ],
    }

    def __init__(
        self,
        graph_path: str | Path = "graphify-out/graph.json",
    ):
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
    def _node_text(node: dict[str, Any]) -> str:
        values = []

        for key in (
            "id",
            "name",
            "label",
            "title",
            "path",
            "file",
            "source",
            "type",
            "kind",
            "module",
        ):
            value = node.get(key)

            if value is not None:
                values.append(str(value))

        return " ".join(values).lower()

    @staticmethod
    def _node_id(node: dict[str, Any], fallback: int) -> str:
        value = node.get("id")

        if value is None:
            return str(fallback)

        return str(value)

    def _match_engine(
        self,
        node: dict[str, Any],
        engine: str,
    ) -> int:
        text = self._node_text(node)

        aliases = self.ENGINE_ALIASES.get(engine, [])

        score = 0

        for alias in aliases:
            if alias in text:
                score += 1

        # Stronger matching for exact application path.
        path_alias = f"app/{engine}"

        if path_alias in text:
            score += 3

        return score

    def _find_nodes(
        self,
        nodes: list[dict[str, Any]],
        engine: str,
        limit: int = 8,
    ) -> list[dict[str, Any]]:

        ranked = []

        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                continue

            score = self._match_engine(node, engine)

            if score <= 0:
                continue

            ranked.append(
                (
                    score,
                    self._node_id(node, index),
                    node,
                )
            )

        ranked.sort(
            key=lambda item: (-item[0], item[1])
        )

        result = []

        for score, node_id, node in ranked[:limit]:
            result.append(
                {
                    "id": node_id,
                    "score": score,
                    "label": node.get(
                        "label",
                        node.get(
                            "name",
                            node_id,
                        ),
                    ),
                    "path": node.get(
                        "path",
                        node.get(
                            "file",
                            node.get(
                                "source",
                                "",
                            ),
                        ),
                    ),
                    "type": node.get(
                        "type",
                        node.get(
                            "kind",
                            "",
                        ),
                    ),
                }
            )

        return result

    @staticmethod
    def _edge_endpoints(edge: dict[str, Any]) -> tuple[str, str]:
        source = (
            edge.get("source")
            or edge.get("from")
            or edge.get("src")
            or edge.get("source_id")
        )

        target = (
            edge.get("target")
            or edge.get("to")
            or edge.get("dst")
            or edge.get("target_id")
        )

        return str(source or ""), str(target or "")

    def _related_edges(
        self,
        edges: list[dict[str, Any]],
        node_ids: set[str],
        limit: int = 30,
    ) -> list[dict[str, Any]]:

        result = []

        for edge in edges:
            if not isinstance(edge, dict):
                continue

            source, target = self._edge_endpoints(edge)

            if source in node_ids or target in node_ids:
                result.append(
                    {
                        "source": source,
                        "target": target,
                        "type": edge.get(
                            "type",
                            edge.get(
                                "kind",
                                edge.get(
                                    "relation",
                                    "",
                                ),
                            ),
                        ),
                    }
                )

            if len(result) >= limit:
                break

        return result

    def map_runtime(
        self,
        *,
        gates: dict[str, Any] | None = None,
        orchestration: dict[str, Any] | None = None,
        limit_per_engine: int = 8,
    ) -> dict[str, Any]:

        graph = self._load_graph()

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not isinstance(nodes, list):
            nodes = []

        if not isinstance(edges, list):
            edges = []

        gates = gates or {}
        orchestration = orchestration or {}

        engine_names = [
            "language",
            "problem",
            "knowledge",
            "reasoning",
            "policy",
            "memory",
            "action",
            "orchestration",
            "developer_core",
        ]

        mappings = {}
        all_node_ids: set[str] = set()

        for engine in engine_names:
            matches = self._find_nodes(
                nodes,
                engine,
                limit=limit_per_engine,
            )

            mappings[engine] = {
                "runtime_status": (
                    gates.get(engine, {})
                    if isinstance(gates.get(engine), dict)
                    else {}
                ),
                "nodes": matches,
                "node_count": len(matches),
            }

            all_node_ids.update(
                item["id"]
                for item in matches
            )

        related_edges = self._related_edges(
            edges,
            all_node_ids,
        )

        stages = orchestration.get("stages", [])

        if not isinstance(stages, list):
            stages = []

        return {
            "mapper": {
                "version": self.VERSION,
                "mode": "read-only",
                "graph_path": str(self.graph_path),
                "graph_loaded": bool(graph),
            },
            "runtime": {
                "gates": gates,
                "orchestration_stages": stages,
            },
            "graph": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "matched_nodes": len(all_node_ids),
                "related_edges": len(related_edges),
            },
            "mappings": mappings,
            "edges": related_edges,
        }
''',

    "app/developer_core/impact.py": r'''
from __future__ import annotations

from pathlib import Path
from typing import Any
import json


class RuntimeImpactAnalyzer:
    """
    Gate 14.2 Runtime Impact Analyzer.

    Menghitung dependency/impact secara READ-ONLY
    berdasarkan node dan edge Graphify yang sudah ada.
    """

    VERSION = "14.2.0-runtime-impact"

    def __init__(
        self,
        graph_path: str | Path = "graphify-out/graph.json",
    ):
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
    def _endpoint(
        edge: dict[str, Any],
        side: str,
    ) -> str:

        if side == "source":
            value = (
                edge.get("source")
                or edge.get("from")
                or edge.get("src")
                or edge.get("source_id")
            )
        else:
            value = (
                edge.get("target")
                or edge.get("to")
                or edge.get("dst")
                or edge.get("target_id")
            )

        return str(value or "")

    def analyze(
        self,
        node_ids: list[str] | set[str] | None = None,
        *,
        max_items: int = 50,
    ) -> dict[str, Any]:

        graph = self._load_graph()

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not isinstance(nodes, list):
            nodes = []

        if not isinstance(edges, list):
            edges = []

        selected = {
            str(item)
            for item in (node_ids or [])
        }

        dependencies = []
        dependents = []

        for edge in edges:
            if not isinstance(edge, dict):
                continue

            source = self._endpoint(edge, "source")
            target = self._endpoint(edge, "target")

            if source in selected:
                dependents.append(
                    {
                        "source": source,
                        "target": target,
                        "type": edge.get(
                            "type",
                            edge.get(
                                "kind",
                                edge.get(
                                    "relation",
                                    "",
                                ),
                            ),
                        ),
                    }
                )

            if target in selected:
                dependencies.append(
                    {
                        "source": source,
                        "target": target,
                        "type": edge.get(
                            "type",
                            edge.get(
                                "kind",
                                edge.get(
                                    "relation",
                                    "",
                                ),
                            ),
                        ),
                    }
                )

        dependencies = dependencies[:max_items]
        dependents = dependents[:max_items]

        risk = "low"

        total_impact = (
            len(dependencies)
            + len(dependents)
        )

        if total_impact >= 20:
            risk = "high"
        elif total_impact >= 8:
            risk = "medium"

        return {
            "impact": {
                "version": self.VERSION,
                "graph_path": str(self.graph_path),
                "mode": "read-only",
            },
            "selection": {
                "node_ids": sorted(selected),
                "count": len(selected),
            },
            "dependency": {
                "count": len(dependencies),
                "items": dependencies,
            },
            "dependents": {
                "count": len(dependents),
                "items": dependents,
            },
            "risk": {
                "level": risk,
                "impact_count": total_impact,
            },
        }

    def analyze_mapping(
        self,
        mapping: dict[str, Any],
    ) -> dict[str, Any]:

        mappings = mapping.get(
            "mappings",
            {},
        )

        selected = set()

        if isinstance(mappings, dict):
            for item in mappings.values():
                if not isinstance(item, dict):
                    continue

                for node in item.get("nodes", []):
                    if isinstance(node, dict):
                        node_id = node.get("id")

                        if node_id is not None:
                            selected.add(str(node_id))

        return self.analyze(selected)
''',

    "app/developer_core/__init__.py": r'''
from .engine import DeveloperCoreEngine, DeveloperAnalysis
from .graph_bridge import GraphifyBridge
from .runtime import DeveloperRuntime
from .mapper import RuntimeGraphMapper
from .impact import RuntimeImpactAnalyzer

__all__ = [
    "DeveloperCoreEngine",
    "DeveloperAnalysis",
    "GraphifyBridge",
    "DeveloperRuntime",
    "RuntimeGraphMapper",
    "RuntimeImpactAnalyzer",
]
''',

    "tests/test_gate14_mapper_impact.py": r'''
from pathlib import Path

from app.developer_core.mapper import RuntimeGraphMapper
from app.developer_core.impact import RuntimeImpactAnalyzer


def test_mapper_loads_existing_graph():
    mapper = RuntimeGraphMapper()

    result = mapper.map_runtime(
        gates={
            "language": {"status": "active"},
            "reasoning": {"status": "grounded"},
        },
        orchestration={
            "stages": [
                "language",
                "problem",
                "reasoning",
            ]
        },
    )

    assert "mapper" in result
    assert "mappings" in result
    assert result["mapper"]["mode"] == "read-only"


def test_mapper_has_engine_mapping():
    mapper = RuntimeGraphMapper()

    result = mapper.map_runtime()

    assert "language" in result["mappings"]
    assert "reasoning" in result["mappings"]
    assert "developer_core" in result["mappings"]


def test_impact_analyzer():
    analyzer = RuntimeImpactAnalyzer()

    result = analyzer.analyze([])

    assert "impact" in result
    assert result["impact"]["mode"] == "read-only"


def test_mapping_to_impact():
    mapper = RuntimeGraphMapper()

    mapping = mapper.map_runtime()

    analyzer = RuntimeImpactAnalyzer()

    result = analyzer.analyze_mapping(mapping)

    assert "dependency" in result
    assert "dependents" in result
    assert "risk" in result


def test_existing_graph_not_required_for_import():
    path = Path("graphify-out/graph.json")

    mapper = RuntimeGraphMapper(path)

    result = mapper.map_runtime()

    assert "graph" in result
''',

    "scripts/validate_gate14_mapper.py": r'''
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
'''
}

for filename, content in FILES.items():
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print("CREATED:", filename)

print("")
print("=" * 64)
print("GATE 14.2 SOURCE BUILD : PASS")
print("=" * 64)
