from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Fact:
    subject: str
    predicate: str
    value: Any
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 0.0

    def to_dict(self):
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class Inference:
    conclusion: str
    confidence: float
    rule_name: str = ""

    def to_dict(self):
        return {
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "rule_name": self.rule_name,
        }


@dataclass
class ReasoningResult:
    status: str
    facts: list[Fact] = field(default_factory=list)
    inferences: list[Inference] = field(default_factory=list)
    confidence: float = 0.0
    explanation: str = ""
    blocked_reason: str | None = None

    def to_dict(self):
        return {
            "status": self.status,
            "facts": [x.to_dict() for x in self.facts],
            "inferences": [x.to_dict() for x in self.inferences],
            "confidence": self.confidence,
            "explanation": self.explanation,
            "blocked_reason": self.blocked_reason,
        }