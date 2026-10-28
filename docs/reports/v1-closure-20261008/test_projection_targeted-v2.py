from copy import deepcopy
from types import SimpleNamespace
from typing import Literal
import json
import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError
class _PublicChatModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)

class _PublicChatTrust(_PublicChatModel):
    supports_claim: bool
    confidence: float = Field(ge=0, le=1)
    risk_level: Literal['low', 'medium', 'high', 'critical']
    requires_human: bool
    evidence_count: int = Field(ge=0)
    evidence_available: bool

class _PublicChatEvidence(_PublicChatModel):
    document_id: str = Field(max_length=256)
    title: str = Field(max_length=1024)
    chunk: str = Field(max_length=20000)
    score: float = Field(ge=0, le=1)

class _PublicChatGrounding(_PublicChatModel):
    enabled: bool
    grounded: bool
    reason: str = Field(max_length=128)

class _PublicChatUnderstanding(_PublicChatModel):
    intent: str = Field(max_length=128)

class _PublicChatProblem(_PublicChatModel):
    goal: str | None = Field(default=None, max_length=2000)

class _PublicChatResponse(_PublicChatModel):
    session_id: str = Field(min_length=1, max_length=128)
    response: str
    trust: _PublicChatTrust
    model: str = Field(max_length=256)
    provider_status: Literal['local_rule', 'evidence_fast_path', 'ollama', 'offline']
    latency_ms: int = Field(ge=0)
    grounding: _PublicChatGrounding
    understanding: _PublicChatUnderstanding
    problem: _PublicChatProblem
    evidence: list[_PublicChatEvidence] = Field(max_length=20)
    timestamp: str = Field(max_length=64)

def _project_v1_chat_response(payload: dict, *, intent_name: str) -> dict:
    """Build public data explicitly; never serialize internal context recursively.

    Trust values remain the existing assessment. Citation projection does not
    certify authority or implement knowledge access control.
    """
    trust = payload['trust']
    grounding = payload['grounding']
    public_reasons = {'empty_answer', 'no_evidence', 'grounded_abstention', 'requirement_evidence_missing', 'possible_unsupported_content', 'grounded', 'deterministic_response', 'not_evaluated'}
    reason = grounding.get('reason')
    if not isinstance(reason, str) or reason not in public_reasons:
        reason = 'not_evaluated'
    problem = payload.get('problem')
    goal = problem.get('goal') if isinstance(problem, dict) else None
    if not isinstance(goal, str):
        goal = None
    public = _PublicChatResponse(session_id=payload['session_id'], response=payload['response'], trust=_PublicChatTrust(supports_claim=trust['supports_claim'], confidence=trust['confidence'], risk_level=trust['risk_level'], requires_human=trust['requires_human'], evidence_count=trust['evidence_count'], evidence_available=trust['evidence_available']), model=payload['model'], provider_status=payload['provider_status'], latency_ms=payload['latency_ms'], grounding=_PublicChatGrounding(enabled=grounding['enabled'], grounded=grounding['grounded'], reason=reason), understanding=_PublicChatUnderstanding(intent=intent_name), problem=_PublicChatProblem(goal=goal), evidence=[_PublicChatEvidence(document_id=item['document_id'], title=item['title'], chunk=item['chunk'], score=item['score']) for item in payload['evidence']], timestamp=payload['timestamp'])
    return public.model_dump(mode='json')
routes = SimpleNamespace(_project_v1_chat_response=_project_v1_chat_response)
PRIVATE = 'INTERNAL_SENTINEL_7219'
ROOT_KEYS = {'session_id', 'response', 'trust', 'model', 'provider_status', 'latency_ms', 'grounding', 'understanding', 'problem', 'evidence', 'timestamp'}
TRUST_KEYS = {'supports_claim', 'confidence', 'risk_level', 'requires_human', 'evidence_count', 'evidence_available'}

def internal_context():
    state = {'reasoning': {'facts': [PRIVATE], 'inferences': [PRIVATE], 'explanation': PRIVATE}, 'policy': {'decision': PRIVATE, 'reason': PRIVATE}, 'memory': [{'content': PRIVATE, 'metadata': {'unrecognized': PRIVATE}}]}
    return {**deepcopy(state), 'orchestration': {'data': deepcopy(state)}, 'future_safe_looking_field': {'nested': PRIVATE}}

def sample_payload():
    return {'session_id': 'current-request', 'response': 'Public answer.', 'trust': {'supports_claim': True, 'confidence': 0.8, 'risk_level': 'low', 'requires_human': False, 'evidence_count': 1, 'evidence_available': True, 'issues': [PRIVATE], 'details': {'future': PRIVATE}}, 'model': 'fixture-model', 'provider_status': 'ollama', 'latency_ms': 12, 'grounding': {'enabled': True, 'grounded': True, 'reason': 'grounded', 'unsupported_sentences': [PRIVATE], 'future': PRIVATE}, 'understanding': {'input': PRIVATE, 'output': {'entities': [PRIVATE]}}, 'problem': {'goal': 'Public goal.', 'metadata': {'future': PRIVATE}}, 'evidence': [{'document_id': 'PUBLIC-1', 'title': 'Public citation', 'chunk': 'Public citation.', 'score': 0.9, 'source': PRIVATE, 'metadata': {'future': PRIVATE}}], 'timestamp': '2026-10-06T00:00:00+00:00', 'gate_pipeline': internal_context(), 'developer_core': {'orchestration': internal_context()['orchestration'], 'observability': {'policy_decision': PRIVATE}, 'gates': {'9': {'allowed': PRIVATE}}}, 'unknown_public_looking_metadata': {'unknown': PRIVATE}}

def assert_public(data):
    assert set(data) == ROOT_KEYS
    assert set(data['trust']) == TRUST_KEYS
    assert set(data['grounding']) == {'enabled', 'grounded', 'reason'}
    assert set(data['understanding']) == {'intent'}
    assert set(data['problem']) == {'goal'}
    for item in data['evidence']:
        assert set(item) == {'document_id', 'title', 'chunk', 'score'}
    assert PRIVATE not in json.dumps(data)

@pytest.mark.parametrize('context', [None, {}, {'policy': None, 'memory': PRIVATE}, internal_context()])
def test_projection_excludes_internal_mirrors_unknown_fields_and_never_mutates(context):
    payload = sample_payload()
    payload['gate_pipeline'] = context
    before = deepcopy(payload)
    projected = routes._project_v1_chat_response(payload, intent_name='ask_general_info')
    assert_public(projected)
    assert projected['response'] == 'Public answer.'
    assert projected['evidence'][0]['chunk'] == 'Public citation.'
    assert projected['trust']['confidence'] == payload['trust']['confidence']
    assert payload == before

def test_unknown_grounding_reason_and_non_scalar_goal_fail_closed_without_stringifying():
    payload = sample_payload()
    payload['grounding']['reason'] = {'internal': PRIVATE}
    payload['problem']['goal'] = {'description': PRIVATE}
    projected = routes._project_v1_chat_response(payload, intent_name='unknown')
    assert_public(projected)
    assert projected['problem']['goal'] is None
    assert projected['grounding']['reason'] == 'not_evaluated'

@pytest.mark.parametrize('bad_value', [float('nan'), float('inf'), -0.1, 1.1, '0.8'])
def test_malformed_public_assessment_is_not_silently_coerced(bad_value):
    payload = sample_payload()
    payload['trust']['confidence'] = bad_value
    with pytest.raises(ValidationError):
        routes._project_v1_chat_response(payload, intent_name='unknown')

def test_oversized_citation_is_not_returned_or_silently_truncated():
    payload = sample_payload()
    payload['evidence'][0]['chunk'] = 'x' * 20001
    with pytest.raises(ValidationError):
        routes._project_v1_chat_response(payload, intent_name='unknown')