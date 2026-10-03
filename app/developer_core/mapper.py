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
        edges = graph.get("links", graph.get("edges", []))

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
