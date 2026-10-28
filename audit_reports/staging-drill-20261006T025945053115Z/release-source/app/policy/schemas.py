"""
Policy Engine Schemas - pakai dataclass agar tidak perlu pydantic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    REQUIRE_HUMAN = "REQUIRE_HUMAN"
    DENY = "DENY"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PolicyEvaluation:
    """Hasil evaluasi kebijakan."""
    decision: PolicyDecision = field(default=PolicyDecision.ALLOW)
    risk_level: RiskLevel = field(default=RiskLevel.LOW)
    requires_confirmation: bool = field(default=False)
    requires_human: bool = field(default=False)
    reason: str = field(default="")
    matched_rules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PolicyRule:
    """Aturan kebijakan."""
    name: str = ""
    description: str = ""
    decision: PolicyDecision = field(default=PolicyDecision.ALLOW)
    conditions: Dict[str, Any] = field(default_factory=dict)
