"""
Trust Engine - Validasi evidence, relevansi, unsupported claims.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.trust.schemas import TrustAssessment, RiskLevel


class TrustEngine:
    """
    Engine untuk menilai kepercayaan terhadap claim berdasarkan evidence.
    JANGAN samakan confidence model dengan kepastian fakta.
    """

    def __init__(self, min_evidence_threshold: float = 0.3):
        self.min_evidence_threshold = min_evidence_threshold

    def evaluate(
        self,
        evidence: List[Dict[str, Any]],
        claim: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TrustAssessment:
        """
        Evaluasi trust terhadap claim berdasarkan evidence yang tersedia.
        """
        if not evidence:
            return TrustAssessment(
                supports_claim=False,
                evidence_count=0,
                evidence_available=False,
                confidence=0.0,
                risk_level=RiskLevel.HIGH,
                requires_human=True,
                issues=["Tidak ada evidence yang tersedia"],
                details={},
            )

        # Hitung relevansi rata-rata evidence
        relevance_scores = []
        for ev in evidence:
            relevance = ev.get("relevance", 0.0)
            if not isinstance(relevance, (int, float)):
                relevance = 0.0
            relevance_scores.append(max(0.0, min(1.0, relevance)))

        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0

        # Hitung coverage: berapa evidence yang relevan
        relevant_count = sum(1 for r in relevance_scores if r >= self.min_evidence_threshold)
        coverage = relevant_count / len(evidence) if evidence else 0.0

        # Tentukan apakah claim didukung
        supports_claim = coverage >= 0.3 and avg_relevance >= 0.3

        # Tentukan risk level
        if not supports_claim:
            if coverage == 0.0:
                risk_level = RiskLevel.CRITICAL
                requires_human = True
                issues = ["Tidak ada evidence yang relevan"]
            else:
                risk_level = RiskLevel.HIGH
                requires_human = coverage < 0.5
                issues = ["Evidence tidak cukup untuk mendukung claim"]
        elif avg_relevance < 0.5:
            risk_level = RiskLevel.MEDIUM
            requires_human = False
            issues = ["Evidence ada tapi relevansi rendah"]
        elif coverage < 0.5:
            risk_level = RiskLevel.LOW
            requires_human = False
            issues = []
        else:
            risk_level = RiskLevel.LOW
            requires_human = False
            issues = []

        confidence = round(avg_relevance * coverage, 3)

        return TrustAssessment(
            supports_claim=supports_claim,
            evidence_count=len(evidence),
            evidence_available=True,
            confidence=confidence,
            risk_level=risk_level,
            requires_human=requires_human,
            issues=issues,
            details={
                "avg_relevance": round(avg_relevance, 3),
                "coverage": round(coverage, 3),
                "relevant_evidence_count": relevant_count,
                "total_evidence": len(evidence),
            },
        )

    def evaluate_batch(
        self,
        pairs: List[Dict[str, Any]],
    ) -> List[TrustAssessment]:
        """Evaluasi batch claim-evidence pairs."""
        results = []
        for item in pairs:
            result = self.evaluate(
                evidence=item.get("evidence", []),
                claim=item.get("claim", ""),
                context=item.get("context"),
            )
            results.append(result)
        return results

    def identify_unsupported_claims(
        self,
        claims: List[str],
        evidence: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Identifikasi claim yang tidak didukung evidence.
        """
        unsupported = []
        for claim in claims:
            assessment = self.evaluate(evidence=evidence, claim=claim)
            if not assessment.supports_claim:
                unsupported.append({
                    "claim": claim,
                    "risk_level": assessment.risk_level.value,
                    "issues": assessment.issues,
                    "confidence": assessment.confidence,
                })
        return unsupported


_default_engine = TrustEngine()


def create_trust_engine(min_evidence_threshold: float = 0.3) -> TrustEngine:
    """Buat trust engine baru."""
    return TrustEngine(min_evidence_threshold=min_evidence_threshold)


def evaluate_trust(
    evidence: List[Dict[str, Any]],
    claim: str,
) -> TrustAssessment:
    """Evaluasi trust (shortcut)."""
    return _default_engine.evaluate(evidence=evidence, claim=claim)
