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
