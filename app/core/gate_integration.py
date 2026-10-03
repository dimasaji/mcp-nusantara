from __future__ import annotations
from typing import Any

from app.action.engine import ActionEngine
from app.memory.engine import MemoryEngine
from app.orchestration.engine import OrchestrationEngine
from app.policy.engine import PolicyEngine
from app.reasoning.engine import ReasoningEngine


class GateIntegration:
    VERSION = "8-13.1.0"

    def __init__(self, existing_tools: dict[str, Any] | None = None):
        self.reasoning = ReasoningEngine()
        self.policy = PolicyEngine()
        self.memory = MemoryEngine()
        self.actions = ActionEngine(existing_tools or {})
        self.orchestration = OrchestrationEngine()

    def process(
        self,
        *,
        session_id: str,
        user_input: str,
        evidence: list[Any] | None = None,
        intent_name: str = "",
        intent_confidence: float = 0.0,
        problem: Any = None,
    ) -> dict[str, Any]:

        evidence = list(evidence or [])

        self.memory.remember(
            session_id,
            "user",
            user_input,
        )

        reasoning = self.reasoning.analyze(
            user_input,
            evidence=evidence,
            intent_name=intent_name,
            intent_confidence=intent_confidence,
        )

        reasoning_data = (
            reasoning.to_dict()
            if hasattr(reasoning, "to_dict")
            else reasoning
        )

        status = reasoning_data.get(
            "status",
            "insufficient_evidence",
        )

        confidence = float(
            reasoning_data.get("confidence", 0.0) or 0.0
        )

        policy = self.policy.decide(
            action="answer",
            reasoning_status=status,
            confidence=confidence,
        )

        policy_data = (
            policy.to_dict()
            if hasattr(policy, "to_dict")
            else policy
        )

        workflow = self.orchestration.run(
            session_id=session_id,
            user_input=user_input,
            language={
                "intent": intent_name,
                "confidence": intent_confidence,
            },
            problem=problem,
            reasoning=reasoning_data,
            policy=policy_data,
            memory=self.memory.context(session_id),
        )

        return {
            "version": self.VERSION,
            "status": "processed",
            "reasoning": reasoning_data,
            "policy": policy_data,
            "memory": self.memory.context(session_id),
            "orchestration": workflow,
            "action": {
                "status": "not_executed",
                "reason": "No side-effect action requested.",
            },
        }

    def remember_response(
        self,
        *,
        session_id: str,
        response: str,
    ) -> None:
        self.memory.remember(
            session_id,
            "assistant",
            response,
        )
