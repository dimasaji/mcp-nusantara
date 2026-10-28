"""
Trust Engine Schemas - pakai dataclass agar tidak perlu pydantic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TrustAssessment:
    """Hasil evaluasi kepercayaan."""
    supports_claim: bool = field(default=False)
    evidence_count: int = field(default=0)
    evidence_available: bool = field(default=False)
    confidence: float = field(default=0.0)
    risk_level: RiskLevel = field(default=RiskLevel.LOW)
    requires_human: bool = field(default=False)
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
