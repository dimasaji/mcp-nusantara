from pathlib import Path
from typing import Any

from app.developer_core.engine import DeveloperCoreEngine
from app.developer_core.runtime import DeveloperRuntime


class GraphifyBridge:

    VERSION = "14.1.0-runtime-bridge"

    def __init__(
        self,
        graph_path: str | Path = "graphify-out/graph.json",
    ):
        self.graph_path = Path(graph_path)
        self.core = DeveloperCoreEngine(self.graph_path)
        self.runtime = DeveloperRuntime()

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

    def runtime_snapshot(
        self,
        *,
        session_id: str,
        user_input: str,
        gate_pipeline: dict[str, Any] | None = None,
        provider_status: str = "",
        latency_ms: int | float = 0,
        grounded: bool = False,
    ) -> dict[str, Any]:

        return self.runtime.snapshot(
            session_id=session_id,
            user_input=user_input,
            gate_pipeline=gate_pipeline,
            provider_status=provider_status,
            latency_ms=latency_ms,
            grounded=grounded,
        )
