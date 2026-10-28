from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
import json
import os
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
    version: str = "14.2.0-read-only-analysis"
    project_root: str = ""
    timestamp: str = "1970-01-01T00:00:00+00:00"
    summary: dict[str, Any] = field(default_factory=dict)
    architecture: dict[str, Any] = field(default_factory=dict)
    dependencies: dict[str, Any] = field(default_factory=dict)
    workflows: dict[str, Any] = field(default_factory=dict)
    impact: dict[str, Any] = field(default_factory=dict)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    risk: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)

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
            "version": self.version,
            "project_root": self.project_root,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "architecture": self.architecture,
            "dependencies": self.dependencies,
            "workflows": self.workflows,
            "impact": self.impact,
            "candidates": self.candidates,
            "risk": self.risk,
            "evidence": self.evidence,
        }


class DeveloperCoreEngine:
    """
    Gate 14 Developer Core.

    Tidak membuat graph baru.
    Mengonsumsi Graphify graph.json yang sudah ada.
    """

    VERSION = "14.2.0-read-only-analysis"

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

    MAX_GRAPH_BYTES = 16 * 1024 * 1024
    MAX_GRAPH_NODES = 50000
    MAX_GRAPH_EDGES = 100000
    MAX_ENTRIES = 4000
    MAX_DEPTH = 12
    MAX_RELATIONSHIPS = 1000
    PROTECTED_NAMES = frozenset({
        ".git", ".env", ".aws", ".ssh", ".codex", ".agents", ".venv",
        "node_modules", "__pycache__", "data", "secrets", "credentials",
    })

    def __init__(
        self, graph_path: str | Path = "graphify-out/graph.json", *,
        project_root: str | Path | None = None,
    ):
        # Positional graph_path and legacy methods remain compatible. Root is
        # captured once: changing cwd later cannot redirect filesystem access.
        self.project_root = Path(project_root) if project_root is not None else Path.cwd()
        self.project_root = self.project_root.absolute()
        self.graph_path = Path(graph_path)
        self._issues: list[dict[str, Any]] = []
        self._timestamp = "1970-01-01T00:00:00+00:00"
        self._graph_hash = ""

    def _issue(self, kind: str, severity: str, message: str) -> None:
        item = {"type": kind, "severity": severity, "message": message}
        if item not in self._issues:
            self._issues.append(item)

    def _safe_path(self, path: Path) -> bool:
        """Reject protected components and links before reading; never follow links.

        This is a static snapshot boundary, not a filesystem race sandbox.
        The caller must use a workspace without concurrent adversarial changes.
        """
        try:
            absolute = path.absolute()
            relative = absolute.relative_to(self.project_root)
            if any(part in {"..", "."} for part in relative.parts):
                return False
            parts = [part.casefold() for part in relative.parts]
            if any(part in self.PROTECTED_NAMES or part.startswith(".env") for part in parts):
                return False
            # Deny protected roots too, including credential/config directories.
            root_parts = [part.casefold() for part in self.project_root.parts]
            if any(part in self.PROTECTED_NAMES or part.startswith(".env") or
                   part in {"windows", "program files", "program files (x86)"}
                   for part in root_parts):
                return False
            absolute.resolve().relative_to(self.project_root.resolve())
            for item in [self.project_root, *absolute.parents, absolute]:
                if item.is_symlink() or item.is_junction():
                    return False
            return True
        except (OSError, ValueError, RuntimeError):
            return False

    def _load_graph(self) -> dict[str, Any]:
        path = self.graph_path if self.graph_path.is_absolute() else self.project_root / self.graph_path
        if not self._safe_path(path):
            self._issue("graph_path_blocked", "high", "Graph path outside safe project boundary.")
            return {}
        try:
            if not path.is_file():
                self._issue("graph_unavailable", "high", "Graph file is absent or not a regular file.")
                return {}
            if path.stat().st_size > self.MAX_GRAPH_BYTES:
                self._issue("graph_limit", "high", "Graph exceeds byte limit.")
                return {}
            with path.open("rb") as stream:
                raw = stream.read(self.MAX_GRAPH_BYTES + 1)
            if len(raw) > self.MAX_GRAPH_BYTES:
                self._issue("graph_limit", "high", "Graph exceeds byte limit.")
                return {}
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Graph must be an object")
            nodes = data.get("nodes", [])
            edges = data.get("links", data.get("edges", []))
            if not isinstance(nodes, list) or not isinstance(edges, list):
                raise ValueError("Graph collections must be lists")
            if len(nodes) > self.MAX_GRAPH_NODES or len(edges) > self.MAX_GRAPH_EDGES:
                self._issue("graph_limit", "high", "Graph exceeds collection limits.")
                return {}
            import hashlib
            self._graph_hash = hashlib.sha256(raw).hexdigest()
            # A source snapshot timestamp, not wall clock: repeated analysis of
            # unchanged inputs (including graph mtime) produces identical output.
            self._timestamp = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
            return data
        except (OSError, UnicodeError, ValueError, RecursionError, OverflowError):
            self._issue("graph_invalid", "high", "Graph could not be read or validated.")
            return {}

    @staticmethod
    def _count_graph(data: dict[str, Any]) -> tuple[int, int]:
        nodes = data.get("nodes", [])
        edges = data.get("links", data.get("edges", []))
        return (len(nodes) if isinstance(nodes, list) else 0,
                len(edges) if isinstance(edges, list) else 0)

    def _engine_inventory(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        remaining = self.MAX_ENTRIES
        for name, path_text in self.ENGINE_PATHS.items():
            path = self.project_root / path_text
            safe = self._safe_path(path)
            exists = safe and path.is_dir()
            count = 0
            if not safe:
                self._issue("inventory_path_blocked", "high", "An engine path violates the read boundary.")
            stack = [(path, 0)] if exists else []
            while stack:
                directory, depth = stack.pop()
                if depth >= self.MAX_DEPTH:
                    self._issue("traversal_limit", "medium", "Inventory depth limit reached; counts may be partial.")
                    continue
                if remaining <= 0:
                    self._issue("traversal_limit", "medium", "Inventory entry limit reached; counts may be partial.")
                    break
                try:
                    # Never materialize an unbounded directory listing. On an
                    # oversized directory discard the partial listing so output
                    # does not depend on filesystem enumeration order.
                    entries = []
                    with os.scandir(directory) as iterator:
                        for entry in iterator:
                            entries.append(Path(entry.path))
                            if len(entries) > remaining:
                                break
                    if len(entries) > remaining:
                        remaining = 0
                        self._issue("traversal_limit", "medium", "Inventory entry limit reached; counts may be partial.")
                        break
                    remaining -= len(entries)
                    directories = []
                    for entry in sorted(entries, key=lambda item: (item.name.casefold(), item.name)):
                        if not self._safe_path(entry):
                            continue
                        if entry.is_dir():
                            directories.append((entry, depth + 1))
                        elif entry.is_file() and entry.suffix == ".py":
                            count += 1
                    stack.extend(reversed(directories))
                except OSError:
                    self._issue("inventory_unreadable", "medium", "An engine directory cannot be enumerated.")
            result.append({"name": name, "path": path_text, "exists": exists,
                           "python_files": count,
                           "status": "active" if count else "empty" if exists else "missing"})
        return result

    def _relationships(self, graph: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """Summarize existing graph evidence, without executing or trusting labels."""
        nodes: dict[str, dict[str, str]] = {}
        for item in graph.get("nodes", []):
            if not isinstance(item, dict):
                continue
            ident, source = item.get("id"), item.get("source_file", "")
            if not isinstance(ident, str) or not ident or len(ident) > 256:
                continue
            if not isinstance(source, str) or not source or len(source) > 512:
                continue
            if not self._safe_path(self.project_root / source):
                continue
            label = item.get("label", ident)
            label = label if isinstance(label, str) else ident
            node = {"id": ident, "label": label[:256], "source_file": source}
            # Duplicate IDs are resolved deterministically, independent of order.
            if ident not in nodes or tuple(node.values()) < tuple(nodes[ident].values()):
                nodes[ident] = node
        relationships: set[tuple[str, str, str]] = set()
        for item in graph.get("links", graph.get("edges", [])):
            if not isinstance(item, dict):
                continue
            source, target = item.get("source"), item.get("target")
            if not isinstance(source, str) or not isinstance(target, str):
                continue
            if source not in nodes or target not in nodes:
                continue
            relation = item.get("relation", item.get("type", "related"))
            if not isinstance(relation, str):
                relation = "related"
            relationships.add((source, target, relation[:128]))
        bounded = sorted(relationships)[:self.MAX_RELATIONSHIPS]
        if len(relationships) > self.MAX_RELATIONSHIPS:
            self._issue("relationship_limit", "medium", "Relationship summary is bounded and partial.")
        evidence = [nodes[key] for key in sorted(nodes)[:self.MAX_RELATIONSHIPS]]
        return ([{"source": a, "target": b, "relation": c} for a, b, c in bounded], evidence)

    def analyze(self, *, runtime_gates: dict[str, Any] | None = None) -> DeveloperAnalysis:
        self._issues = []
        self._timestamp = "1970-01-01T00:00:00+00:00"
        self._graph_hash = ""
        graph = self._load_graph()
        nodes, edges = self._count_graph(graph)
        engines = self._engine_inventory()
        relationships, evidence = self._relationships(graph)
        gates = {}
        for gate, name in self.GATES.items():
            supplied = runtime_gates.get(str(gate), {}) if isinstance(runtime_gates, dict) else {}
            status = supplied.get("status", "known") if isinstance(supplied, dict) else "known"
            gates[str(gate)] = {"name": name, "status": status if isinstance(status, str) else "known"}
        missing = [item["name"] for item in engines if not item["exists"]]
        if missing:
            self._issue("missing_engine_path", "medium", "Some engine directories are absent.")
        if graph and nodes == 0:
            self._issue("empty_graph", "high", "Existing graph contains no nodes.")
        risks = sorted(self._issues, key=lambda item: (item["type"], item["severity"]))
        recommendations = ["Use existing graph evidence to review impact before a separately approved source change."]
        if not graph:
            recommendations.append("Ask the owner to provide a valid existing graph inside the project boundary.")
        if missing:
            recommendations.append("Review missing engine directories against the architecture contract.")
        candidates = [{
            "candidate": item["type"], "reason": item["message"], "risk": item["severity"],
            "evidence": {"graph_loaded": bool(graph), "missing_engines": missing},
            "impact": "Analysis completeness or confidence may be reduced.",
            "rollback": "No engine writes occurred; withdraw the proposal if rejected.",
            "recommended_action": "Validate evidence and obtain human approval before any implementation.",
        } for item in risks]
        status = "ready" if graph and not any(item["severity"] == "high" for item in risks) else "degraded"
        risk = {"level": "high" if any(item["severity"] == "high" for item in risks) else
                "medium" if risks else "low", "findings": risks}
        affected = sorted({item[key] for item in relationships for key in ("source", "target")})
        return DeveloperAnalysis(
            status=status, graph_loaded=bool(graph), node_count=nodes, edge_count=edges,
            gates=gates, engines=engines, risks=risks, recommendations=recommendations,
            version=self.VERSION, project_root=str(self.project_root), timestamp=self._timestamp,
            summary={"mode": "READ_ANALYZE_RECOMMEND", "status": status,
                     "engine_count": len(engines), "missing_engines": missing,
                     "timestamp_basis": "graph_mtime_utc_or_epoch_when_unavailable",
                     "graph_sha256": self._graph_hash},
            architecture={"engines": engines, "basis": "directory_inventory_and_existing_graph"},
            dependencies={"relationships": relationships, "basis": "existing_graph_only",
                          "runtime_dependencies_verified": False},
            workflows={"gates": gates, "execution_enabled": False,
                       "basis": "known_gate_map_and_caller_supplied_status"},
            impact={"mode": "read-only", "related_node_ids": affected,
                    "change_specific_analysis": False, "complete": not bool(risks)},
            candidates=candidates, risk=risk,
            evidence=[{"kind": "graph_snapshot", "sha256": self._graph_hash,
                       "loaded": bool(graph)}, *evidence],
        )

    def self_analyze(self, *, runtime_gates: dict[str, Any] | None = None) -> dict[str, Any]:
        analysis = self.analyze(runtime_gates=runtime_gates)
        return {
            # Existing output keys preserved for GraphifyBridge and Gate 14.
            "developer_core": {"version": self.VERSION, "status": analysis.status},
            "graphify": {"path": str(self.graph_path), "loaded": analysis.graph_loaded,
                         "nodes": analysis.node_count, "edges": analysis.edge_count},
            "gates": analysis.gates, "engines": analysis.engines,
            "risks": analysis.risks, "recommendations": analysis.recommendations,
            "engine_version": self.VERSION, "engine_identity": "DeveloperCoreEngine",
            "engine_capabilities": ["bounded_inventory", "existing_graph_analysis", "recommendations", "self_analysis"],
            "engine_limitations": ["no_execution", "no_source_writes", "no_database_access", "no_deployment",
                                   "static_snapshot_not_race_sandbox", "graph_evidence_not_runtime_proof"],
            "self_analysis": analysis.to_dict(),
            "health": {"status": analysis.status, "graph_loaded": analysis.graph_loaded,
                       "findings": analysis.risks},
            "contracts": {"mode": "READ_ANALYZE_RECOMMEND", "human_approval_required": True,
                          "self_modifying": False, "execution_enabled": False},
            "improvement_candidates": analysis.candidates, "risk": analysis.risk,
        }
