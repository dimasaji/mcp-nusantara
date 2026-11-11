"""Unit tests for LangChain adapter."""
import os
import pytest

os.environ['NUS_LANGCHAIN_ENABLED'] = 'true'
from app.knowledge.langchain_adapter import create_retriever, create_llm, is_enabled
from app.knowledge.engine import KnowledgeEngine


def test_is_enabled():
    assert is_enabled() is True


def test_create_retriever():
    ke = KnowledgeEngine()
    r = create_retriever(ke, top_k=3)
    assert r is not None
    docs = r.invoke('permohonan data pribadi')
    assert len(docs) >= 1
    assert docs[0].metadata.get('document_id') is not None


def test_create_llm():
    llm = create_llm()
    assert llm is not None


def test_create_retriever_disabled():
    os.environ['NUS_LANGCHAIN_ENABLED'] = 'false'
    # Re-import to pick up new env
    import importlib
    import app.knowledge.langchain_adapter as mod
    importlib.reload(mod)
    r = mod.create_retriever(KnowledgeEngine(), top_k=3)
    assert r is None
    os.environ['NUS_LANGCHAIN_ENABLED'] = 'true'
