"""Offline V1 boundary checks; never import the application startup module."""
import ast
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.memory.engine import MemoryEngine
from test_v1_langgraph import projection_and_helpers


# Reuse the existing privacy assertions against the actual source projector,
# without importing routes/main (which construct active application services).
_tree = ast.parse(Path('tests/test_v1_response_projection.py').read_text(encoding='utf-8-sig'))
_pure_names = {
    'internal_context', 'sample_payload', 'assert_public',
    'test_projection_excludes_internal_mirrors_unknown_fields_and_never_mutates',
    'test_unknown_grounding_reason_and_non_scalar_goal_fail_closed_without_stringifying',
    'test_malformed_public_assessment_is_not_silently_coerced',
    'test_oversized_citation_is_removed_without_mutating_source',
}
_nodes = [n for n in _tree.body if (
    isinstance(n, ast.FunctionDef) and n.name in _pure_names
) or (isinstance(n, ast.Assign) and any(
    isinstance(t, ast.Name) and t.id in {'PRIVATE', 'ROOT_KEYS', 'TRUST_KEYS'} for t in n.targets
))]
routes = SimpleNamespace(_project_v1_chat_response=projection_and_helpers()[0])
exec(compile(ast.Module(body=_nodes, type_ignores=[]), 'existing-v1-privacy-assertions', 'exec'), globals())


def test_memory_zero_limit_returns_no_history():
    memory = MemoryEngine()
    memory.remember('first', 'user', 'private question')
    memory.remember('first', 'assistant', 'private answer')
    assert memory.context('first', limit=0) == []
    assert len(memory.context('first', limit=2)) == 2


def test_memory_bounded_context_and_session_isolation():
    memory = MemoryEngine(max_items_per_session=2)
    for text in ('old', 'recent', 'latest'):
        memory.remember('first', 'user', text)
    assert [i['content'] for i in memory.context('first', limit=1)] == ['latest']
    assert [i['content'] for i in memory.context('first', limit=2)] == ['recent', 'latest']
    assert memory.context('second') == []
    memory.remember('second', 'user', 'separate')
    memory.clear('first')
    assert memory.context('first') == []
    assert memory.context('second')[0]['content'] == 'separate'
