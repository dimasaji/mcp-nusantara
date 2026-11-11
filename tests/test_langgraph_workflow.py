"""Unit tests for LangGraph workflow."""
import os
import pytest

from app.knowledge.langgraph_workflow import create_workflow, is_enabled


def test_is_enabled(monkeypatch):
    monkeypatch.setenv('NUS_LANGGRAPH_ENABLED', 'true')
    assert is_enabled() is True


def test_create_workflow(monkeypatch):
    monkeypatch.setenv('NUS_LANGGRAPH_ENABLED', 'true')
    w = create_workflow()
    assert w is not None


def test_workflow_invoke(monkeypatch):
    monkeypatch.setenv('NUS_LANGGRAPH_ENABLED', 'true')
    w = create_workflow()
    result = w.invoke({'pdf_path': 'E:/SOP/CAPIL_02.pdf', 'retry_count': 0, 'max_retries': 2})
    assert 'quality_check' in result
    assert 'error_category' in result


def test_workflow_disabled(monkeypatch):
    monkeypatch.setenv('NUS_LANGGRAPH_ENABLED', 'false')
    w = create_workflow()
    assert w is None
