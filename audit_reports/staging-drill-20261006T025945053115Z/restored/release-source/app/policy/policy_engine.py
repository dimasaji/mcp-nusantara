"""
Policy Engine - Decision: ALLOW, REQUIRE_CONFIRMATION, REQUIRE_HUMAN, DENY.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from app.policy.schemas import PolicyEvaluation, PolicyDecision, RiskLevel


class PolicyRule:
    """
    Aturan kebijakan sederhana.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        decision: PolicyDecision = PolicyDecision.ALLOW,
        conditions: Dict[str, Any] = None,
    ):
        self.name = name
        self.description = description
        self.decision = decision
        self.conditions = conditions or {}

    def evaluate(self, context: Dict[str, Any]) -> Optional[PolicyDecision]:
        """Evaluasi rule terhadap context."""
        for key, value in self.conditions.items():
            if key not in context:
                return None
            if context[key] != value:
                return None
        return self.decision


class PolicyEngine:
    """
    Engine untuk mengevaluasi kebijakan.
    """

    def __init__(self):
        self.rules: list[PolicyRule] = []
        self._load_default_rules()

    def _load_default_rules(self):
        """Muat aturan default."""
        # Rule 1: Public data + low risk -> ALLOW
        self.rules.append(PolicyRule(
            name="public_low_risk",
            description="Data publik dengan risiko rendah diizinkan",
            decision=PolicyDecision.ALLOW,
            conditions={"data_sensitivity": "public", "risk_level": "low"},
        ))

        # Rule 2: Internal data + low risk -> ALLOW
        self.rules.append(PolicyRule(
            name="internal_low_risk",
            description="Data internal dengan risiko rendah diizinkan",
            decision=PolicyDecision.ALLOW,
            conditions={"data_sensitivity": "internal", "risk_level": "low"},
        ))

        # Rule 3: Confidential data -> REQUIRE_CONFIRMATION
        self.rules.append(PolicyRule(
            name="confidential_require_confirmation",
            description="Data sensitif memerlukan konfirmasi",
            decision=PolicyDecision.REQUIRE_CONFIRMATION,
            conditions={"data_sensitivity": "confidential"},
        ))

        # Rule 4: Restricted data -> REQUIRE_HUMAN
        self.rules.append(PolicyRule(
            name="restricted_require_human",
            description="Data sangat sensitif butuh manusia",
            decision=PolicyDecision.REQUIRE_HUMAN,
            conditions={"data_sensitivity": "restricted"},
        ))

        # Rule 5: High risk -> REQUIRE_HUMAN
        self.rules.append(PolicyRule(
            name="high_risk_require_human",
            description="Risiko tinggi butuh manusia",
            decision=PolicyDecision.REQUIRE_HUMAN,
            conditions={"risk_level": "high"},
        ))

        # Rule 6: Critical risk -> DENY
        self.rules.append(PolicyRule(
            name="critical_deny",
            description="Risiko kritis ditolak",
            decision=PolicyDecision.DENY,
            conditions={"risk_level": "critical"},
        ))

        # Rule 7: Unknown action -> DENY
        self.rules.append(PolicyRule(
            name="unknown_action_deny",
            description="Aksi tidak dikenal ditolak",
            decision=PolicyDecision.DENY,
            conditions={"action": "unknown"},
        ))

    def evaluate(
        self,
        user_role: str = "user",
        action: str = "query",
        data_sensitivity: str = "internal",
        risk_level: str = "low",
        requires_confirmation: bool = False,
        extra_context: Dict[str, Any] = None,
    ) -> PolicyEvaluation:
        """
        Evaluasi kebijakan.
        """
        if action == "delete" and data_sensitivity in ("confidential", "restricted") and risk_level in ("high", "critical"):
            return PolicyEvaluation(decision=PolicyDecision.DENY, risk_level=RiskLevel(risk_level), requires_confirmation=False, requires_human=False, reason="Destructive action on sensitive data denied", matched_rules=[{"name":"sensitive_delete_deny","decision":"DENY"}])

        context = {
            "user_role": user_role,
            "action": action,
            "data_sensitivity": data_sensitivity,
            "risk_level": risk_level,
            "requires_confirmation": requires_confirmation,
            **(extra_context or {}),
        }

        # Cari rule yang cocok
        matched_rules = []
        for rule in self.rules:
            result = rule.evaluate(context)
            if result is not None:
                matched_rules.append((rule, result))

        if not matched_rules:
            return PolicyEvaluation(
                decision=PolicyDecision.DENY,
                risk_level=RiskLevel.MEDIUM,
                requires_confirmation=False,
                requires_human=False,
                reason="Tidak ada aturan yang cocok",
                matched_rules=[],
            )

        # Prioritaskan: DENY > REQUIRE_HUMAN > REQUIRE_CONFIRMATION > ALLOW
        decision_order = {
            PolicyDecision.DENY: 4,
            PolicyDecision.REQUIRE_HUMAN: 3,
            PolicyDecision.REQUIRE_CONFIRMATION: 2,
            PolicyDecision.ALLOW: 1,
        }

        best_rule, best_decision = max(
            matched_rules,
            key=lambda x: decision_order.get(x[1], 0),
        )

        return PolicyEvaluation(
            decision=best_decision,
            risk_level=RiskLevel(best_rule.conditions.get("risk_level", "low")),
            requires_confirmation=best_decision == PolicyDecision.REQUIRE_CONFIRMATION,
            requires_human=best_decision == PolicyDecision.REQUIRE_HUMAN,
            reason=best_rule.description,
            matched_rules=[{"name": r.name, "decision": d.value} for r, d in matched_rules],
        )


_default_policy_engine = PolicyEngine()


def create_policy_engine() -> PolicyEngine:
    """Buat policy engine baru."""
    return PolicyEngine()


def evaluate_policy(
    user_role: str = "user",
    action: str = "query",
    data_sensitivity: str = "internal",
    risk_level: str = "low",
) -> PolicyEvaluation:
    """Evaluasi kebijakan (shortcut)."""
    return _default_policy_engine.evaluate(
        user_role=user_role,
        action=action,
        data_sensitivity=data_sensitivity,
        risk_level=risk_level,
    )
