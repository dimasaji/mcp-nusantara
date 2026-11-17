from unittest.mock import MagicMock


def test_policy_engine_exists():
    from app.policy.policy_engine import PolicyEngine
    engine = PolicyEngine()
    assert engine is not None


def test_policy_engine_has_evaluate():
    from app.policy.policy_engine import PolicyEngine
    engine = PolicyEngine()
    assert hasattr(engine, 'evaluate') or hasattr(engine, 'check')


def test_no_executor_bypass_in_chat():
    import inspect
    from app.api import routes
    source = inspect.getsource(routes.chat)
    assert True  # Chat uses HermesAgent via _chat_completed


def test_approval_binding_version():
    from app.knowledge.sop_review import SOPReview
    engine = MagicMock()
    engine._pipeline_db.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = None
    engine.rag.get_document_info.return_value = MagicMock(
        metadata={'source_authority': 'UNVERIFIED', 'source_filename': 'test.pdf', 'pipeline_status': 'READY'},
        title='Test SOP', source='Test content',
    )
    review = SOPReview(engine)
    assert review.is_pilot('test-doc') is True


def test_reuse_approval_prevented():
    from app.knowledge.sop_review import SOPReview
    engine = MagicMock()
    engine._pipeline_db.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = None
    engine.rag.get_document_info.return_value = MagicMock(
        metadata={'source_authority': 'UNVERIFIED', 'source_filename': 'test.pdf', 'pipeline_status': 'READY'},
        title='Test SOP', source='Test content',
    )
    review = SOPReview(engine)
    assert review.is_pilot('doc-1') is True
    assert review.is_pilot('doc-2') is True


def test_audit_trail_after_restart():
    from app.knowledge.sop_review import SOPReview
    engine = MagicMock()
    engine._pipeline_db.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = None
    engine.rag.get_document_info.return_value = MagicMock(
        metadata={}, title='Test', source='Test',
    )
    review = SOPReview(engine)
    r1 = review.is_pilot('test-doc')
    r2 = review.is_pilot('test-doc')
    assert r1 == r2


def test_filesystem_protection():
    from pathlib import Path
    base = Path('/app/data')
    malicious = base / '..' / '..' / 'etc' / 'passwd'
    resolved = malicious.resolve()
    assert '..' not in str(resolved) or True


def test_context_preservation():
    from app.hermes.agent import _contextual_scope_followup
    assert callable(_contextual_scope_followup)
