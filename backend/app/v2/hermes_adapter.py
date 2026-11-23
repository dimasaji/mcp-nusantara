from __future__ import annotations

from typing import Any

from app.hermes.agent import HermesAgent


class HermesV2Adapter:
    """
    V2 runtime boundary for Hermes.

    V2 supplies retrieved evidence through context. Hermes remains the
    owner of Language -> Problem -> Reasoning inside this boundary.

    This adapter does not modify V1 engines.
    """

    VERSION = "1.0.0-v2-runtime"

    def __init__(self, agent: HermesAgent | None = None):
        self.agent = agent or HermesAgent()

    def run(
        self,
        user_input: str,
        session_id: str,
        evidence: list[Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = dict(context or {})
        runtime_context["knowledge_evidence"] = list(evidence or [])

        result = self.agent.run(
            user_input=user_input,
            session_id=session_id,
            context=runtime_context,
        )

        return {
            "engine": "hermes",
            "adapter_version": self.VERSION,
            "session_id": session_id,
            "understanding": result.get("understanding"),
            "problem": result.get("problem"),
            "reasoning": result.get("reasoning"),
        }
