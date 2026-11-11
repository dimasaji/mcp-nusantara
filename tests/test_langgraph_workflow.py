"""Unit tests for LangGraph workflow."""
import os
import pytest

os.environ['NUS_LANGGRAPH_ENABLED'] = 'true'
from app.knowledge.langgraph_workflow import create_workflow, is_enabled


def test_is_enabled():
    assert is_enabled() is True


def test_create_workflow():
    w = create_workflow()
    assert w is not None


def test_workflow_invoke():
    w = create_workflow()
    result = w.invoke({'pdf_path': 'E:/SOP/CAPIL_02.pdf', 'retry_count': 0, 'max_retries': 2})
    assert 'quality_check' in result
    assert 'error_category' in result


def test_workflow_disabled():
    os.environ['NUS_LANGGRAPH_ENABLED'] = 'false'
    import importlib
    import app.knowledge.langgraph_workflow as mod
    importlib.reload(mod)
    w = mod.create_workflow()
    assert w is None
    os.environ['NUS_LANGGRAPH_ENABLED'] = 'true'
