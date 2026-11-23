from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    allowed: bool
    reason: str
    risk: str

    def to_dict(self):
        return {
            "decision": self.decision,
            "allowed": self.allowed,
            "reason": self.reason,
            "risk": self.risk,
        }


class PolicyEngine:

    VERSION = "9.0.0-safe-policy"

    SENSITIVE_ACTIONS = {
        "delete",
        "modify_record",
        "publish",
        "send_external",
        "financial_transaction",
    }

    def decide(
        self,
        *,
        action="answer",
        reasoning_status="insufficient_evidence",
        confidence=0.0,
    ):

        if reasoning_status != "grounded":
            return PolicyDecision(
                "block",
                False,
                "Reasoning is not grounded.",
                "medium",
            )

        if confidence < 0.60:
            return PolicyDecision(
                "block",
                False,
                "Reasoning confidence below threshold.",
                "medium",
            )

        if action in self.SENSITIVE_ACTIONS:
            return PolicyDecision(
                "block",
                False,
                "Sensitive action requires explicit authorization.",
                "high",
            )

        return PolicyDecision(
            "allow",
            True,
            "Policy requirements satisfied.",
            "low",
        )
