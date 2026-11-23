"""LangChain adapter for Nusantara V1.

Wraps existing HybridRAG retriever and Ollama provider as LangChain
components. Does NOT replace the Core Engine. Feature-flagged.
"""
from __future__ import annotations

import os
from typing import List, Optional, Any

# Feature flags (default OFF)
def _lc_enabled():
    return os.getenv('NUS_LANGCHAIN_ENABLED', 'false').lower() == 'true'

LANGCHAIN_ENABLED = _lc_enabled()
LANGGRAPH_ENABLED = os.getenv('NUS_LANGGRAPH_ENABLED', 'false').lower() == 'true'


def create_llm(model: str = 'llama3.2:1b', base_url: str = 'http://localhost:11434'):
    """Create a LangChain ChatOllama instance wrapping the existing Ollama."""
    if not _lc_enabled():
        return None
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, base_url=base_url, temperature=0.1)
    except Exception:
        return None


def create_retriever(knowledge_engine, top_k: int = 5):
    """Wrap existing KnowledgeEngine.search_knowledge as a LangChain retriever."""
    if not _lc_enabled():
        return None
    try:
        from langchain_core.retrievers import BaseRetriever
        from langchain_core.documents import Document
        from langchain_core.callbacks import CallbackManagerForRetrieverRun
        from typing import List

        class NusantaraRetriever(BaseRetriever):
            engine: Any = None
            top_k: int = 5

            def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None) -> List[Document]:
                try:
                    results = self.engine.search_knowledge(query, top_k=self.top_k)
                except Exception:
                    return []
                docs = []
                for r in (results or []):
                    did = getattr(r, 'document_id', None)
                    title = getattr(r, 'title', None) or did
                    chunk = getattr(r, 'chunk', '') or getattr(r, 'source', '') or ''
                    score = getattr(r, 'score', 0.0)
                    pages = getattr(r, 'metadata', {}).get('citation_pages', []) if hasattr(r, 'metadata') else []
                    docs.append(Document(
                        page_content=chunk,
                        metadata={'document_id': did, 'title': title, 'score': score, 'pages': pages},
                    ))
                return docs

        return NusantaraRetriever(engine=knowledge_engine, top_k=top_k)
    except Exception:
        return None


def create_chain(knowledge_engine, model: str = 'llama3.2:1b', base_url: str = 'http://localhost:11434'):
    """Create a LangChain RAG chain wrapping existing retriever + Ollama."""
    if not _lc_enabled():
        return None
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough

        llm = create_llm(model, base_url)
        retriever = create_retriever(knowledge_engine)
        if llm is None or retriever is None:
            return None

        prompt = ChatPromptTemplate.from_template(
            "Jawab berdasarkan konteks berikut:\n{context}\n\nPertanyaan: {question}"
        )

        def format_docs(docs):
            return "\n\n".join(d.page_content for d in docs)

        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        return chain
    except Exception:
        return None


def is_enabled() -> bool:
    return _lc_enabled()


def is_graph_enabled() -> bool:
    return LANGGRAPH_ENABLED
