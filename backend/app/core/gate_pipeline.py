from __future__ import annotations

from app.reasoning.engine import ReasoningEngine
from app.policy.engine import PolicyEngine
from app.memory.engine import MemoryEngine
from app.action.engine import ActionEngine


class GatePipeline:

    VERSION = "8-16-bridge-1.0.0"

    def __init__(self):

        self.reasoning = ReasoningEngine()
        self.policy = PolicyEngine()
        self.memory = MemoryEngine()
        self.actions = ActionEngine()

    def process(
        self,
        *,
        session_id,
        user_input,
        evidence=None,
        intent_name="",
        intent_confidence=0.0,
        action="answer",
    ):

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

        policy = self.policy.decide(
            action=action,
            reasoning_status=reasoning.status,
            confidence=reasoning.confidence,
        )

        return {
            "reasoning": reasoning.to_dict(),
            "policy": policy.to_dict(),
            "memory": self.memory.context(session_id),
        }