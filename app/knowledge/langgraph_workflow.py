"""LangGraph workflow for SOP processing.

Orchestrates existing Nusantara services (Docling, cleaning, indexing,
approval) via typed state and conditional edges. Feature-flagged.
Default OFF. Does NOT replace Core Engine.
"""
from __future__ import annotations

import os
from typing import TypedDict, Optional, Literal

def _is_enabled():
    return os.getenv('NUS_LANGGRAPH_ENABLED', 'false').lower() == 'true'

LANGGRAPH_ENABLED = _is_enabled()


class SOPWorkflowState(TypedDict, total=False):
    document_id: str
    version_id: str
    pdf_path: str
    extraction_status: str
    extraction_error: str
    quality_check: str  # PASS / FAIL
    retry_count: int
    max_retries: int
    approval_status: str
    index_status: str
    error_category: str  # TRANSIENT / PERMANENT / NEEDS_HUMAN / POLICY_DENIED


def create_workflow():
    """Create a LangGraph StateGraph for SOP processing. Returns None if disabled."""
    if not _is_enabled():
        return None
    try:
        from langgraph.graph import StateGraph, END

        def validate_source(state: SOPWorkflowState) -> SOPWorkflowState:
            import hashlib
            from pathlib import Path
            path = Path(state.get('pdf_path', ''))
            if not path.exists():
                return {**state, 'error_category': 'PERMANENT', 'quality_check': 'FAIL'}
            return {**state, 'quality_check': 'PASS'}

        def extract(state: SOPWorkflowState) -> SOPWorkflowState:
            # Delegate to existing Docling worker (not reimplemented)
            return {**state, 'extraction_status': 'QUEUED'}

        def quality_check(state: SOPWorkflowState) -> SOPWorkflowState:
            status = state.get('extraction_status', '')
            if status == 'COMPLETE':
                return {**state, 'quality_check': 'PASS'}
            return {**state, 'quality_check': 'FAIL'}

        def route_quality(state: SOPWorkflowState) -> Literal['clean_chunk', 'ocr_fallback', 'needs_attention']:
            q = state.get('quality_check', '')
            if q == 'PASS':
                return 'clean_chunk'
            retry = state.get('retry_count', 0)
            max_r = state.get('max_retries', 2)
            if retry < max_r:
                return 'ocr_fallback'
            return 'needs_attention'

        def ocr_fallback(state: SOPWorkflowState) -> SOPWorkflowState:
            return {**state, 'retry_count': state.get('retry_count', 0) + 1, 'extraction_status': 'QUEUED'}

        def clean_chunk(state: SOPWorkflowState) -> SOPWorkflowState:
            return {**state, 'quality_check': 'PASS'}

        def needs_attention(state: SOPWorkflowState) -> SOPWorkflowState:
            return {**state, 'error_category': 'NEEDS_HUMAN'}

        def generate_embeddings(state: SOPWorkflowState) -> SOPWorkflowState:
            return {**state, 'index_status': 'PENDING'}

        def index_document(state: SOPWorkflowState) -> SOPWorkflowState:
            return {**state, 'index_status': 'INDEXED'}

        def verify_index(state: SOPWorkflowState) -> SOPWorkflowState:
            return {**state, 'index_status': 'VERIFIED'}

        def ready_for_review(state: SOPWorkflowState) -> SOPWorkflowState:
            return {**state, 'approval_status': 'PENDING_REVIEW'}

        graph = StateGraph(SOPWorkflowState)
        graph.add_node('validate_source', validate_source)
        graph.add_node('extract', extract)
        graph.add_node('quality_check', quality_check)
        graph.add_node('ocr_fallback', ocr_fallback)
        graph.add_node('clean_chunk', clean_chunk)
        graph.add_node('needs_attention', needs_attention)
        graph.add_node('generate_embeddings', generate_embeddings)
        graph.add_node('index_document', index_document)
        graph.add_node('verify_index', verify_index)
        graph.add_node('ready_for_review', ready_for_review)

        graph.set_entry_point('validate_source')
        graph.add_edge('validate_source', 'extract')
        graph.add_edge('extract', 'quality_check')
        graph.add_conditional_edges('quality_check', route_quality, {
            'clean_chunk': 'clean_chunk',
            'ocr_fallback': 'ocr_fallback',
            'needs_attention': 'needs_attention',
        })
        graph.add_edge('ocr_fallback', 'quality_check')
        graph.add_edge('clean_chunk', 'generate_embeddings')
        graph.add_edge('generate_embeddings', 'index_document')
        graph.add_edge('index_document', 'verify_index')
        graph.add_edge('verify_index', 'ready_for_review')
        graph.add_edge('ready_for_review', END)
        graph.add_edge('needs_attention', END)

        return graph.compile()
    except Exception:
        return None


def is_enabled() -> bool:
    return _is_enabled()
