"""Exercise the real V1 policy/handoff services omitted by basic agent fixtures."""
import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.handoff.engine import HandoffEngine
from app.policy.policy_engine import PolicyEngine
from test_v1_langgraph import fixture


@pytest.mark.parametrize('question', ['Hallo', 'Apa itu KTP-el?'])
def test_chat_with_real_policy_returns_a_projectable_answer(question):
    parts = fixture(empty=True, answer='Halo, ada yang bisa saya bantu?')
    services = {**parts[2], 'policy': PolicyEngine(), 'handoff': HandoffEngine()}
    result = asyncio.run(parts[1].execute_v1(
        SimpleNamespace(user_input=question, session_id='policy-regression', model=None, stream=False),
        **services,
    ))
    public = parts[3](result.payload, intent_name=result.intent_name)
    assert public['response']


def test_no_evidence_handoff_uses_the_classified_intent():
    parts = fixture(empty=True)
    handoff = HandoffEngine()
    result = asyncio.run(parts[1].execute_v1(
        SimpleNamespace(user_input='Apa itu KTP-el?', session_id='handoff-regression', model=None, stream=False),
        **parts[2], handoff=handoff,
    ))
    assert result.payload
    assert len(handoff._requests) == 1
    request = next(iter(handoff._requests.values()))
    assert request.context['intent_name'] == 'ask_general_info'
    assert result.payload['handoff']['level'] == 'normal'
    assert result.payload['handoff']['created_at'] == request.created_at


@pytest.mark.parametrize('adapter_present', [False, True])
def test_startup_shares_worker_only_when_rag_has_an_embedding_adapter(adapter_present):
    source = Path('app/api/routes.py').read_text(encoding='utf-8-sig')
    tree = ast.parse(source)
    wiring = next(node for node in tree.body if isinstance(node, ast.If)
                  and '_language.semantic_intent_engine' in ast.unparse(node.test))
    client = object()
    adapter = SimpleNamespace(client=object()) if adapter_present else None
    namespace = {
        '_language': SimpleNamespace(semantic_intent_engine=SimpleNamespace(client=client)),
        '_knowledge': SimpleNamespace(rag=SimpleNamespace(_embedding_adapter=adapter)),
    }
    exec(compile(ast.Module(body=[wiring], type_ignores=[]), 'startup-worker-wiring', 'exec'), namespace)
    if adapter_present:
        assert adapter.client is client
    else:
        assert namespace['_knowledge'].rag._embedding_adapter is None
