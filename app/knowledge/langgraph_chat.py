"""LangGraph Chat workflow for Nusantara V1.

Orchestrates the existing Chat pipeline (scope, intent, retrieval, evidence
validation, generation, citation) via typed state and conditional edges.
Feature-flagged. Default OFF. Reuses existing services.
"""
from __future__ import annotations

import os
import asyncio
import concurrent.futures
from typing import TypedDict, Optional, Literal, List, Dict, Any

LANGGRAPH_ENABLED = os.getenv('NUS_LANGGRAPH_ENABLED', 'false').lower() == 'true'


class NusantaraChatState(TypedDict, total=False):
    request_id: str
    session_id: str
    query: str
    operator: bool
    effective_scope: dict
    conversation_context: list
    intent: str
    candidate_document_ids: list
    evidence: list
    answer: str
    citations: list
    grounded: bool
    retry_count: int
    status: Literal['running', 'answered', 'abstained', 'needs_attention', 'failed']
    error_code: str


def create_chat_workflow(knowledge_engine, language_engine, provider, grounding_guard, gates, trust_engine):
    """Create a LangGraph StateGraph for Chat. Returns None if disabled or services unavailable."""
    if not LANGGRAPH_ENABLED:
        return None
    try:
        from langgraph.graph import StateGraph, END

        def resolve_scope(state: NusantaraChatState) -> NusantaraChatState:
            return {**state, 'status': 'running'}

        def classify_intent(state: NusantaraChatState) -> NusantaraChatState:
            return {**state, 'intent': state.get('intent', 'unknown')}

        def retrieve(state: NusantaraChatState) -> NusantaraChatState:
            try:
                results = knowledge_engine.search_knowledge(state.get('query', ''), top_k=5)
                evidence = []
                for r in (results or []):
                    evidence.append({
                        'document_id': getattr(r, 'document_id', None),
                        'title': getattr(r, 'title', None),
                        'chunk': getattr(r, 'chunk', '') or getattr(r, 'source', ''),
                        'score': getattr(r, 'score', 0.0),
                        'pages': getattr(r, 'metadata', {}).get('citation_pages', []) if hasattr(r, 'metadata') else [],
                    })
                return {**state, 'evidence': evidence}
            except Exception as e:
                return {**state, 'evidence': [], 'error_code': str(e), 'status': 'failed'}

        def validate_evidence(state: NusantaraChatState) -> NusantaraChatState:
            evidence = state.get('evidence', [])
            if not evidence:
                return {**state, 'grounded': False, 'status': 'abstained'}
            try:
                result = grounding_guard.validate(
                    answer=state.get('answer', ''),
                    evidence=evidence,
                    intent_name=state.get('intent'),
                )
                return {**state, 'grounded': result.grounded}
            except Exception:
                return {**state, 'grounded': False}

        def generate_answer(state: NusantaraChatState) -> NusantaraChatState:
            try:
                evidence_text = '\n'.join(e.get('chunk', '') for e in state.get('evidence', []))
                prompt = "Jawab berdasarkan evidence berikut:\n%s\n\nPertanyaan: %s" % (evidence_text[:2000], state.get('query', ''))
                coro = provider.generate({'system': 'Jawab singkat dalam Bahasa Indonesia.', 'prompt': prompt, 'temperature': 0.1, 'max_tokens': 200})
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            result = pool.submit(asyncio.run, coro).result(timeout=60)
                    else:
                        result = loop.run_until_complete(coro)
                except RuntimeError:
                    result = asyncio.run(coro)
                answer = str(result.get('content', '')).strip()
                return {**state, 'answer': answer}
            except Exception as e:
                return {**state, 'answer': '', 'error_code': str(e), 'status': 'failed'}

        def verify_citations(state: NusantaraChatState) -> NusantaraChatState:
            evidence = state.get('evidence', [])
            citations = []
            for e in evidence:
                citations.append({
                    'document_id': e.get('document_id'),
                    'page': e.get('pages', [None])[0] if e.get('pages') else None,
                })
            return {**state, 'citations': citations, 'status': 'answered'}

        def route_evidence(state: NusantaraChatState) -> Literal['generate', 'abstain']:
            if not state.get('evidence'):
                return 'abstain'
            return 'generate'

        def abstain(state: NusantaraChatState) -> NusantaraChatState:
            return {**state, 'answer': 'Informasi tersebut belum tersedia dalam dokumen yang ada.', 'grounded': False, 'status': 'abstained'}

        graph = StateGraph(NusantaraChatState)
        graph.add_node('resolve_scope', resolve_scope)
        graph.add_node('classify_intent', classify_intent)
        graph.add_node('retrieve', retrieve)
        graph.add_node('validate_evidence', validate_evidence)
        graph.add_node('verify_grounding', validate_evidence)
        graph.add_node('generate', generate_answer)
        graph.add_node('verify_citations', verify_citations)
        graph.add_node('abstain', abstain)

        graph.set_entry_point('resolve_scope')
        graph.add_edge('resolve_scope', 'classify_intent')
        graph.add_edge('classify_intent', 'retrieve')
        graph.add_edge('retrieve', 'validate_evidence')
        graph.add_conditional_edges('validate_evidence', route_evidence, {
            'generate': 'generate',
            'abstain': 'abstain',
        })
        graph.add_edge('generate', 'verify_grounding')
        graph.add_edge('verify_grounding', 'verify_citations')
        graph.add_edge('verify_citations', END)
        graph.add_edge('abstain', END)

        return graph.compile()
    except Exception:
        return None


def is_enabled() -> bool:
    return LANGGRAPH_ENABLED
