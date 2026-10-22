"""V1 knowledge boundary: existing sources are internal until publication approval.

This deliberately provides no public-publication switch. An operator credential
is checked by the HTTP owner, never accepted from a chat body or model output.
No production metadata/index migration is needed to fail closed.
"""
import hashlib

from fastapi import HTTPException


def v1_session_id(session_id: str, *, operator: bool) -> str:
    """Quarantine legacy histories and separate public/operator context + replay."""
    audience = 'operator' if operator else 'public'
    return f'v1-{audience}-' + hashlib.sha256(session_id.encode('utf-8')).hexdigest()


class V1KnowledgeBoundary:
    def __init__(self, engine, *, operator: bool, provider: str):
        if operator and provider != 'ollama':
            raise HTTPException(409, 'INTERNAL_KNOWLEDGE_REQUIRES_LOCAL_OPERATOR_MODEL')
        self._engine = engine
        self._operator = operator
        self._provider = provider

    def search_knowledge(self, query, top_k=None, filter=None):
        # Deny before any store read, embedding, candidate acquisition or prompt
        # assembly. Document IDs supplied by a caller cannot grant access.
        if not self._operator:
            return []
        if self._provider != 'ollama':
            raise HTTPException(409, 'INTERNAL_KNOWLEDGE_REQUIRES_LOCAL_OPERATOR_MODEL')
        return self._engine.search_knowledge(query, top_k=top_k, filter=filter)
