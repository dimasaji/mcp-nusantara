from unittest.mock import MagicMock
import re


def test_unverified_pipeline_document_is_review_gated():
    from app.knowledge.sop_review import SOPReview
    engine = MagicMock()
    engine._pipeline_db.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = None
    engine.rag.get_document_info.return_value = MagicMock(
        metadata={'source_authority': 'UNVERIFIED', 'source_status': '', 'source_filename': 'test.txt', 'pipeline_status': 'READY'},
        title='Test Document', source='Test content',
    )
    review = SOPReview(engine)
    assert review.is_pilot('test-doc') is True


def test_pdf_document_gated():
    from app.knowledge.sop_review import SOPReview
    engine = MagicMock()
    engine._pipeline_db.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = None
    engine.rag.get_document_info.return_value = MagicMock(
        metadata={'source_authority': 'UNVERIFIED', 'source_filename': 'test.pdf', 'pipeline_status': 'READY'},
        title='Test SOP', source='Test content',
    )
    review = SOPReview(engine)
    assert review.is_pilot('test-pdf') is True


def test_legacy_verified_document_gated():
    from app.knowledge.sop_review import SOPReview
    engine = MagicMock()
    engine._pipeline_db.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = None
    engine.rag.get_document_info.return_value = MagicMock(
        metadata={'source_authority': 'VERIFIED', 'source_status': 'active'},
        title='Legacy Doc', source='Test content',
    )
    review = SOPReview(engine)
    assert review.is_pilot('legacy-doc') is True


def test_sop_title_gated():
    from app.knowledge.sop_review import SOPReview
    engine = MagicMock()
    engine._pipeline_db.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = None
    engine.rag.get_document_info.return_value = MagicMock(
        metadata={}, title='SOP Penerbitan KTP', source='Test content',
    )
    review = SOPReview(engine)
    assert review.is_pilot('sop-doc') is True


def test_chat_session_pattern_restricted():
    from app.security.v1_knowledge import CHAT_SESSION_PATTERN
    assert re.fullmatch(CHAT_SESSION_PATTERN, 'web-11111111-1111-4111-8111-111111111111')
    assert not re.fullmatch(CHAT_SESSION_PATTERN, 'web')
    assert not re.fullmatch(CHAT_SESSION_PATTERN, 'web-abc123')
    assert not re.fullmatch(CHAT_SESSION_PATTERN, 'session_1')
    assert not re.fullmatch(CHAT_SESSION_PATTERN, 'a')
    assert not re.fullmatch(CHAT_SESSION_PATTERN, '../etc/passwd')
    assert not re.fullmatch(CHAT_SESSION_PATTERN, 'session with spaces')


def test_rate_limiting():
    from app.api.routes import _check_rate_limit
    assert _check_rate_limit('test-session-rl-3') is True


def test_error_taxonomy_categories():
    from app.core.error_taxonomy import ErrorCategory
    assert hasattr(ErrorCategory, 'TRANSIENT')
    assert hasattr(ErrorCategory, 'PERMANENT')
    assert hasattr(ErrorCategory, 'NEEDS_HUMAN')
    assert hasattr(ErrorCategory, 'POLICY_DENIED')


def test_grounding_negation_mismatch():
    from app.knowledge.grounding import EvidenceGroundingGuard
    guard = EvidenceGroundingGuard()
    result = guard.validate(
        answer="Pemohon tidak dipungut biaya.",
        evidence=[{'chunk': 'Pemohon dipungut biaya.', 'score': 0.9}],
        intent_name='ask_document_requirements',
    )
    assert result.grounded is False


def test_grounding_subset_token():
    from app.knowledge.grounding import EvidenceGroundingGuard
    guard = EvidenceGroundingGuard()
    result = guard.validate(
        answer="Surat Permohonan.",
        evidence=[{'chunk': 'Persyaratan layanan fixture adalah Surat Permohonan.', 'score': 0.9}],
        intent_name='ask_document_requirements',
    )
    assert result.grounded is True or result.reason in ('grounded', 'not_evaluated')
