"""E2E test for LangChain adapter with real Ollama + retriever."""
import os
os.environ['NUS_LANGCHAIN_ENABLED'] = 'true'
os.environ['NUS_LANGGRAPH_ENABLED'] = 'true'

import pytest
from app.knowledge.engine import KnowledgeEngine
from app.knowledge.langchain_adapter import create_retriever, create_llm, create_chain


def test_retriever_e2e():
    ke = KnowledgeEngine()
    r = create_retriever(ke, top_k=5)
    assert r is not None
    docs = r.invoke('permohonan data pribadi')
    assert len(docs) >= 1
    assert any('permohonan' in d.page_content.lower() or 'data pribadi' in d.page_content.lower() for d in docs)
    print('PASS: retriever returned %d docs' % len(docs))


def test_llm_e2e():
    llm = create_llm()
    assert llm is not None
    resp = llm.invoke('Jawab singkat: apa itu KTP?')
    assert resp is not None
    assert len(str(resp.content)) > 0
    print('PASS: LLM responded: %s' % str(resp.content)[:80])


def test_chain_e2e():
    ke = KnowledgeEngine()
    chain = create_chain(ke)
    assert chain is not None
    answer = chain.invoke('Apa syarat permohonan data pribadi?')
    assert answer is not None
    assert len(str(answer)) > 0
    print('PASS: chain answered: %s' % str(answer)[:120])
