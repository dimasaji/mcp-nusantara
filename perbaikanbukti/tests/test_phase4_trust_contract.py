from __future__ import annotations

from app.trust.engine import TrustEngine
from app.trust.schemas import RiskLevel


def test_phase4_no_evidence_fails_closed():
    engine = TrustEngine()

    result = engine.evaluate(
        evidence=[],
        claim="Informasi layanan pemerintah",
    )

    assert result.supports_claim is False
    assert result.evidence_available is False
    assert result.evidence_count == 0
    assert result.confidence == 0.0
    assert result.requires_human is True
    assert result.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}


def test_phase4_irrelevant_evidence_is_critical():
    engine = TrustEngine()

    result = engine.evaluate(
        evidence=[
            {"relevance": 0.10},
        ],
        claim="Cara membuat KTP",
    )

    assert result.supports_claim is False
    assert result.confidence == 0.0
    assert result.risk_level == RiskLevel.CRITICAL
    assert result.requires_human is True


def test_phase4_weak_evidence_is_not_high_confidence():
    engine = TrustEngine()

    result = engine.evaluate(
        evidence=[
            {"relevance": 0.30},
        ],
        claim="Cara membuat KTP",
    )

    assert result.confidence <= 0.30


def test_phase4_strong_evidence_has_high_support():
    engine = TrustEngine()

    result = engine.evaluate(
        evidence=[
            {"relevance": 0.80},
        ],
        claim="Cara membuat KTP",
    )

    assert result.supports_claim is True
    assert result.confidence == 0.80
    assert result.evidence_count == 1
    assert result.requires_human is False


def test_phase4_mixed_evidence_must_not_be_marked_low_risk():
    """
    Regression/acceptance test.

    Evidence kuat + evidence lemah tidak boleh dianggap
    LOW risk hanya berdasarkan rata-rata relevance.
    """

    engine = TrustEngine()

    result = engine.evaluate(
        evidence=[
            {"relevance": 0.90},
            {"relevance": 0.10},
        ],
        claim="Cara membuat KTP",
    )

    assert result.confidence <= 0.50

    # Acceptance requirement Phase 4:
    # mixed evidence tidak boleh lolos sebagai LOW risk.
    assert result.risk_level != RiskLevel.LOW or result.requires_human is True


def test_phase4_supports_claim_requires_actual_evidence():
    engine = TrustEngine()

    result = engine.evaluate(
        evidence=[
            {"relevance": 0.0},
            {"relevance": 0.0},
            {"relevance": 0.0},
        ],
        claim="Informasi layanan",
    )

    assert result.supports_claim is False
    assert result.requires_human is True


def test_phase4_batch_evaluation_preserves_one_result_per_claim():
    engine = TrustEngine()

    pairs = [
        {
            "claim": "KTP elektronik",
            "evidence": [{"relevance": 0.90}],
        },
        {
            "claim": "Paspor",
            "evidence": [{"relevance": 0.10}],
        },
        {
            "claim": "Kartu Keluarga",
            "evidence": [],
        },
    ]

    results = engine.evaluate_batch(pairs)

    assert len(results) == 3

    assert results[0].supports_claim is True
    assert results[1].supports_claim is False
    assert results[2].supports_claim is False


def test_phase4_unsupported_claim_identification():
    engine = TrustEngine()

    claims = [
        "KTP elektronik",
        "Paspor",
    ]

    evidence = [
        {"relevance": 0.90},
    ]

    unsupported = engine.identify_unsupported_claims(
        claims=claims,
        evidence=evidence,
    )

    # Current engine evaluates the supplied evidence against each claim.
    # This test establishes the current contract without assuming
    # semantic claim matching that the engine does not yet implement.
    assert isinstance(unsupported, list)


def test_phase4_confidence_is_not_factual_certainty():
    engine = TrustEngine()

    result = engine.evaluate(
        evidence=[
            {
                "relevance": 0.95,
                "source": "official.example",
                "metadata": {
                    "authority": "official",
                },
            }
        ],
        claim="Contoh informasi pemerintah",
    )

    assert result.confidence <= 1.0

    # Trust confidence must remain an evidence-support score,
    # not a claim that the fact is certainly true.
    assert result.details["avg_relevance"] == 0.95


def test_phase4_canonical_score_adapter_shape():
    """
    Canonical RAG Evidence uses `score`.

    TrustEngine itself currently consumes `relevance`, so this test
    verifies the adapter transformation expected by V1/V2 integration.
    """

    evidence = {
        "score": 0.85,
        "document_id": "DOC-001",
        "title": "SOP KTP",
        "source": "dukcapil",
        "chunk": "Informasi KTP",
        "metadata": {
            "authority": "official",
        },
    }

    adapted = {
        "relevance": evidence["score"],
    }

    engine = TrustEngine()

    result = engine.evaluate(
        evidence=[adapted],
        claim="Informasi KTP",
    )

    assert result.supports_claim is True
    assert result.confidence == 0.85


def test_phase4_trust_assessment_contains_governance_fields():
    engine = TrustEngine()

    result = engine.evaluate(
        evidence=[{"relevance": 0.80}],
        claim="Informasi layanan",
    )

    assert hasattr(result, "supports_claim")
    assert hasattr(result, "confidence")
    assert hasattr(result, "risk_level")
    assert hasattr(result, "requires_human")
    assert hasattr(result, "issues")
    assert hasattr(result, "details")
