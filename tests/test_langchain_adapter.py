"""Unit tests for LangChain adapter."""
from test_synthetic_rag_fixture import build_synthetic_engine

from app.knowledge.engine import KnowledgeEngine


def test_is_enabled(monkeypatch):
    monkeypatch.setenv('NUS_LANGCHAIN_ENABLED', 'true')
    from app.knowledge.langchain_adapter import is_enabled
    assert is_enabled() is True


def test_create_retriever(monkeypatch, tmp_path):
    monkeypatch.setenv('NUS_LANGCHAIN_ENABLED', 'true')
    from app.knowledge.langchain_adapter import create_retriever
    r = create_retriever(build_synthetic_engine(tmp_path), top_k=3)
    assert r is not None
    docs = r.invoke('Surat permohonan')
    assert len(docs) >= 1
    assert docs[0].metadata.get('document_id') == 'synthetic-sop-1'


def test_create_llm(monkeypatch):
    monkeypatch.setenv('NUS_LANGCHAIN_ENABLED', 'true')
    from app.knowledge.langchain_adapter import create_llm
    llm = create_llm()
    assert llm is not None


def test_create_retriever_disabled(monkeypatch):
    monkeypatch.setenv('NUS_LANGCHAIN_ENABLED', 'false')
    from app.knowledge.langchain_adapter import create_retriever
    r = create_retriever(KnowledgeEngine(), top_k=3)
    assert r is None
