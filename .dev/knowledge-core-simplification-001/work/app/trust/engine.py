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

    Batas tanggung jawab:
    - Trust Engine hanya menghasilkan assessment, BUKAN keputusan policy.
    - Confidence adalah skor dukungan retrieval, bukan verifikasi fakta.
    - Jika Grounding Guard menyatakan jawaban tidak grounded, Trust
      akan menurunkan confidence dan risk_level melalui parameter
      ``grounded`` (lihat ``evaluate``).
    """

    def __init__(self, min_evidence_threshold: float = 0.3):
        self.min_evidence_threshold = min_evidence_threshold

    def evaluate(
        self,
        evidence: List[Dict[str, Any]],
        claim: str,
        context: Optional[Dict[str, Any]] = None,
        grounded: Optional[bool] = None,
    ) -> TrustAssessment:
        """
        Evaluasi trust terhadap claim berdasarkan evidence yang tersedia.

        Parameters
        ----------
        evidence : list
            Daftar evidence. Setiap item minimal berisi ``relevance``
            (skor retrieval). Konten evidence (chunk/teks) TIDAK
            diterima oleh Trust Engine sesuai boundary Phase 4;
            validasi semantik adalah tanggung jawab Grounding Guard.
        claim : str
            Klaim yang akan dinilai.
        context : dict, optional
            Reserved untuk penggunaan masa depan.
        grounded : bool, optional
            Hasil akhir Grounding Guard. ``None`` berarti tidak
            dievaluasi. Jika ``False`` (jawaban tidak grounded),
            Trust akan menurunkan confidence dan meningkatkan
            risk_level agar tidak terjadi kontradiksi publik
            (``supports_claim=True`` padahal ``grounded=False``).
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
        elif coverage <= 0.5:
            risk_level = RiskLevel.MEDIUM
            requires_human = True
            issues = ["Evidence campuran: coverage belum cukup untuk keputusan otomatis"]
        else:
            risk_level = RiskLevel.LOW
            requires_human = False
            issues = []

        confidence = round(avg_relevance * coverage, 3)

        # ----- Grounding integration (optional) -----
        # Trust tidak memvalidasi konten evidence, tapi jika Grounding
        # Guard sudah menyatakan jawaban final TIDAK grounded, Trust
        # HARUS menurunkan confidence dan risk_level agar API publik
        # tidak menampilkan ``supports_claim=True`` bersamaan dengan
        # ``grounded=False``. ``requires_human=True`` dipertahankan
        # untuk general_knowledge_fallback (pengetahuan umum model
        # tidak diverifikasi knowledge base).
        if grounded is False and supports_claim:
            confidence = min(confidence, 0.20)
            if risk_level == RiskLevel.LOW:
                risk_level = RiskLevel.MEDIUM
            issues = list(issues) + [
                "Grounding menyatakan jawaban tidak didukung evidence",
            ]
            supports_claim = False
            if not requires_human:
                requires_human = True

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
                "grounding_informed": grounded is not None,
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
                grounded=item.get("grounded"),
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
