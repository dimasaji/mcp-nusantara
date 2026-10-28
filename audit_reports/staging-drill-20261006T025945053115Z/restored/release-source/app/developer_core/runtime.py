from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DeveloperRuntime:

    VERSION = "14.1.0-runtime"

    def snapshot(
        self,
        *,
        session_id: str,
        user_input: str,
        gate_pipeline: dict[str, Any] | None = None,
        provider_status: str = "",
        latency_ms: int | float = 0,
        grounded: bool = False,
    ) -> dict[str, Any]:

        pipeline = gate_pipeline or {}

        reasoning = pipeline.get("reasoning", {})
        policy = pipeline.get("policy", {})
        memory = pipeline.get("memory", {})
        orchestration = pipeline.get("orchestration", {})

        return {
            "runtime": {
                "version": self.VERSION,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "provider_status": provider_status,
                "latency_ms": latency_ms,
                "grounded": grounded,
            },

            "request": {
                "input_length": len(user_input or ""),
                "has_input": bool(user_input),
            },

            "gates": {
                "8": {
                    "name": "Reasoning Engine",
                    "status": reasoning.get("status", "unknown"),
                    "confidence": reasoning.get("confidence", 0.0),
                },
                "9": {
                    "name": "Decision / Policy Engine",
                    "status": policy.get("decision", "unknown"),
                    "allowed": policy.get("allowed", False),
                    "risk": policy.get("risk", "unknown"),
                },
                "10": {
                    "name": "Memory / Context Engine",
                    "status": "active" if memory else "empty",
                },
                "11": {
                    "name": "Tool / Action Engine",
                    "status": "observed",
                },
                "12": {
                    "name": "Existing Tools",
                    "status": "preserved",
                },
                "13": {
                    "name": "Workflow / Orchestration",
                    "status": (
                        orchestration.get("status", "observed")
                        if isinstance(orchestration, dict)
                        else "observed"
                    ),
                },
                "14": {
                    "name": "Developer Core / Graph",
                    "status": "active",
                },
            },

            "orchestration": orchestration,

            "observability": {
                "reasoning_status": reasoning.get(
                    "status", "unknown"
                ),
                "reasoning_confidence": reasoning.get(
                    "confidence", 0.0
                ),
                "policy_decision": policy.get(
                    "decision", "unknown"
                ),
                "memory_items": (
                    len(memory)
                    if isinstance(memory, list)
                    else 0
                ),
            },
        }
