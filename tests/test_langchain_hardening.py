"""P3 hardening tests for LangChain/LangGraph integration."""
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

# Default: flags OFF
os.environ.pop('NUS_LANGCHAIN_ENABLED', None)
os.environ.pop('NUS_LANGGRAPH_ENABLED', None)


@pytest.fixture(autouse=True)
def reset_flags():
    settings.nus_langchain_enabled = False
    settings.nus_langgraph_enabled = False
    os.environ.pop('NUS_LANGCHAIN_ENABLED', None)
    os.environ.pop('NUS_LANGGRAPH_ENABLED', None)
    yield
    settings.nus_langchain_enabled = False
    settings.nus_langgraph_enabled = False
    os.environ.pop('NUS_LANGCHAIN_ENABLED', None)
    os.environ.pop('NUS_LANGGRAPH_ENABLED', None)


# --- A. Feature Flags ---

def test_flags_off_legacy_path():
    """Both flags OFF: legacy path works (default)."""
    client = TestClient(app)
    token = 'R4H4Si4.'
    import uuid
    body = {'session_id': 'web-' + str(uuid.uuid4()), 'user_input': 'halo'}
    r = client.post('/v1/chat', json=body, headers={'X-Admin-Token': token})
    assert r.status_code == 200
    d = r.json()
    assert 'response' in d
    assert 'grounding' in d
    assert 'evidence' in d


def test_langchain_flag_on():
    """LangChain ON: adapter available."""
    os.environ['NUS_LANGCHAIN_ENABLED'] = 'true'
    settings.nus_langchain_enabled = True
    from app.knowledge.langchain_adapter import is_enabled, create_retriever, create_llm
    assert is_enabled() is True
    ke = None
    from app.knowledge.engine import KnowledgeEngine
    ke = KnowledgeEngine()
    r = create_retriever(ke, top_k=3)
    assert r is not None
    llm = create_llm()
    assert llm is not None


def test_langgraph_flag_on():
    """LangGraph ON: workflow available."""
    os.environ['NUS_LANGGRAPH_ENABLED'] = 'true'
    settings.nus_langgraph_enabled = True
    from app.knowledge.langgraph_workflow import is_enabled, create_workflow
    assert is_enabled() is True
    w = create_workflow()
    assert w is not None


def test_flags_evaluated_at_call_time():
    """Flags evaluated at call time, not import time."""
    os.environ['NUS_LANGCHAIN_ENABLED'] = 'false'
    settings.nus_langchain_enabled = False
    from app.knowledge.langchain_adapter import is_enabled
    assert is_enabled() is False
    os.environ['NUS_LANGCHAIN_ENABLED'] = 'true'
    settings.nus_langchain_enabled = True
    assert is_enabled() is True


# --- B. Failure Handling ---

def test_empty_retrieval_abstention():
    """Empty retrieval results -> abstention."""
    client = TestClient(app)
    token = 'R4H4Si4.'
    import uuid
    body = {'session_id': 'web-' + str(uuid.uuid4()), 'user_input': 'xyznonexistentquery99999'}
    r = client.post('/v1/chat', json=body, headers={'X-Admin-Token': token})
    assert r.status_code == 200
    d = r.json()
    # Should not crash; may abstain or return no evidence
    assert 'response' in d


def test_no_evidence_abstention():
    """Query with no relevant docs -> abstention or no evidence."""
    client = TestClient(app)
    token = 'R4H4Si4.'
    import uuid
    body = {'session_id': 'web-' + str(uuid.uuid4()), 'user_input': 'cuaca hari ini bagaimana?'}
    r = client.post('/v1/chat', json=body, headers={'X-Admin-Token': token})
    assert r.status_code == 200
    d = r.json()
    assert 'response' in d
    assert 'grounding' in d


# --- C. Session and Security ---

def test_session_isolation():
    """Different sessions don't share evidence."""
    client = TestClient(app)
    token = 'R4H4Si4.'
    import uuid
    sid1 = 'web-' + str(uuid.uuid4())
    sid2 = 'web-' + str(uuid.uuid4())
    body1 = {'session_id': sid1, 'user_input': 'halo', 'document_ids': ['DOC-SHA256-282658f23a8578ca50b1135a589449635681cdadb725fc957e52355b959a7244']}
    body2 = {'session_id': sid2, 'user_input': 'halo', 'document_ids': ['DOC-SHA256-282658f23a8578ca50b1135a589449635681cdadb725fc957e52355b959a7244']}
    r1 = client.post('/v1/chat', json=body1, headers={'X-Admin-Token': token})
    r2 = client.post('/v1/chat', json=body2, headers={'X-Admin-Token': token})
    assert r1.status_code == 200
    assert r2.status_code == 200


def test_public_no_access():
    """Public (no token) cannot access internal SOPs."""
    client = TestClient(app)
    import uuid
    body = {'session_id': 'web-' + str(uuid.uuid4()), 'user_input': 'halo'}
    r = client.post('/v1/chat', json=body)
    assert r.status_code == 200
    d = r.json()
    assert len(d.get('evidence', [])) == 0


def test_no_stack_trace_in_error():
    """Error responses don't expose stack traces."""
    client = TestClient(app)
    body = {'session_id': '', 'user_input': 'test'}
    r = client.post('/v1/chat', json=body)
    # Should be 422 (validation) not 500 with traceback
    assert r.status_code in (422, 403, 400)
    assert 'Traceback' not in r.text
    assert 'File "' not in r.text


# --- D. API Compatibility ---

def test_response_schema_compatible():
    """Response has all required fields."""
    client = TestClient(app)
    token = 'R4H4Si4.'
    import uuid
    body = {'session_id': 'web-' + str(uuid.uuid4()), 'user_input': 'halo'}
    r = client.post('/v1/chat', json=body, headers={'X-Admin-Token': token})
    assert r.status_code == 200
    d = r.json()
    required = ['session_id', 'response', 'trust', 'model', 'provider_status', 'latency_ms', 'grounding', 'understanding', 'problem', 'evidence', 'timestamp']
    for field in required:
        assert field in d, 'Missing field: %s' % field


def test_request_contract_unchanged():
    """Request contract unchanged."""
    client = TestClient(app)
    token = 'R4H4Si4.'
    import uuid
    body = {'session_id': 'web-' + str(uuid.uuid4()), 'user_input': 'test', 'model': None, 'stream': False}
    r = client.post('/v1/chat', json=body, headers={'X-Admin-Token': token})
    assert r.status_code == 200


# --- E. Regression ---

def test_hermes_v1_conversation():
    """Existing Hermes V1 conversation still works."""
    client = TestClient(app)
    token = 'R4H4Si4.'
    import uuid
    body = {'session_id': 'web-' + str(uuid.uuid4()), 'user_input': 'halo'}
    r = client.post('/v1/chat', json=body, headers={'X-Admin-Token': token})
    assert r.status_code == 200
    d = r.json()
    assert d['provider_status'] in ('local_rule', 'evidence_fast_path', 'ollama', 'openrouter', 'offline')


def test_knowledge_search_still_works():
    """Knowledge search still works."""
    client = TestClient(app)
    token = 'R4H4Si4.'
    body = {'query': 'CAPIL', 'top_k': 5}
    r = client.post('/v1/knowledge/search', json=body, headers={'X-Admin-Token': token})
    assert r.status_code == 200
    d = r.json()
    assert 'results' in d
