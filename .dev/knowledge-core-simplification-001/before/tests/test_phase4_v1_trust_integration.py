from __future__ import annotations

from app.trust.engine import TrustEngine
from app.trust.schemas import RiskLevel


def test_phase4_v1_trust_receives_canonical_score_evidence():
    """
    V1 RAG menggunakan canonical Evidence.score.
    Trust integration harus menerima score tersebut tanpa
    mengubah object Evidence.
    """
    evidence = [
        {
            "document_id": "DOC-KTP-001",
            "title": "SOP KTP",
            "source": "dukcapil",
            "chunk": "KTP elektronik diterbitkan sesuai prosedur.",
            "chunk_id": "DOC-KTP-001-0",
            "chunk_index": 0,
            "start_char": 0,
            "end_char": 50,
            "score": 0.85,
            "metadata": {
                "authority": "official",
            },
        }
    ]

    trust_input = [
        {
            "relevance": item["score"],
        }
        for item in evidence
    ]

    result = TrustEngine().evaluate(
        evidence=trust_input,
        claim="Informasi tentang KTP elektronik",
    )

    assert result.supports_claim is True
    assert result.confidence == 0.85
    assert result.evidence_count == 1
    assert result.requires_human is False


def test_phase4_v1_trust_rejects_weak_evidence():
    """
    Evidence yang terlalu lemah tidak boleh otomatis dianggap
    cukup terpercaya.
    """
    evidence = [
        {
            "score": 0.10,
            "document_id": "DOC-WEAK-001",
            "source": "unknown",
        }
    ]

    trust_input = [
        {
            "relevance": item["score"],
        }
        for item in evidence
    ]

    result = TrustEngine().evaluate(
        evidence=trust_input,
        claim="Informasi layanan pemerintah",
    )

    assert result.supports_claim is False
    assert result.requires_human is True
    assert result.risk_level == RiskLevel.CRITICAL


def test_phase4_v1_trust_flags_mixed_evidence():
    """
    Evidence kuat + lemah tidak boleh dianggap aman hanya
    berdasarkan rata-rata relevance.
    """
    evidence = [
        {"score": 0.90},
        {"score": 0.10},
    ]

    trust_input = [
        {
            "relevance": item["score"],
        }
        for item in evidence
    ]

    result = TrustEngine().evaluate(
        evidence=trust_input,
        claim="Informasi layanan pemerintah",
    )

    assert result.supports_claim is True
    assert result.confidence == 0.25
    assert result.risk_level == RiskLevel.MEDIUM
    assert result.requires_human is True


def test_phase4_v1_trust_is_not_policy():
    """
    Trust hanya menghasilkan assessment.
    Trust tidak boleh menghasilkan keputusan ALLOW/BLOCK.
    """
    evidence = [{"score": 0.90}]

    trust_input = [
        {
            "relevance": item["score"],
        }
        for item in evidence
    ]

    result = TrustEngine().evaluate(
        evidence=trust_input,
        claim="Informasi layanan",
    )

    assert hasattr(result, "supports_claim")
    assert hasattr(result, "confidence")
    assert hasattr(result, "risk_level")
    assert not hasattr(result, "decision")


def test_phase4_v1_trust_preserves_provenance_outside_scoring():
    """
    Provenance tetap tersedia pada canonical evidence.
    Trust tidak boleh menghapus/mengubah evidence.
    """
    evidence = [
        {
            "document_id": "DOC-OFFICIAL-001",
            "title": "SOP Pelayanan",
            "source": "sop.tangerangkota.go.id",
            "chunk": "Prosedur pelayanan.",
            "score": 0.90,
            "metadata": {
                "authority": "official",
            },
        }
    ]

    original = dict(evidence[0])

    trust_input = [
        {
            "relevance": item["score"],
        }
        for item in evidence
    ]

    TrustEngine().evaluate(
        evidence=trust_input,
        claim="Prosedur pelayanan",
    )

    assert evidence[0] == original
    assert evidence[0]["source"] == "sop.tangerangkota.go.id"
    assert evidence[0]["metadata"]["authority"] == "official"
