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
    def __init__(self, engine, *, operator: bool, provider: str, sop_version=None, document_ids=None, document_query=None):
        if operator and provider != 'ollama':
            raise HTTPException(409, 'INTERNAL_KNOWLEDGE_REQUIRES_LOCAL_OPERATOR_MODEL')
        self._engine = engine
        self._operator = operator
        self._provider = provider
        self._sop_version = sop_version
        self._document_ids = document_ids or []
        self._document_query = document_query

    def search_knowledge(self, query, top_k=None, filter=None):
        # Deny before any store read, embedding, candidate acquisition or prompt
        # assembly. Document IDs supplied by a caller cannot grant access.
        if not self._operator:
            return []
        if self._provider != 'ollama':
            raise HTTPException(409, 'INTERNAL_KNOWLEDGE_REQUIRES_LOCAL_OPERATOR_MODEL')
        from app.knowledge.sop_review import SOPReview
        review = SOPReview(self._engine)
        if len(self._document_ids) == 1:
            identifier = self._document_ids[0]
            if self._sop_version or review.is_pilot(identifier):
                detail = review.detail(identifier)
                if not self._sop_version and detail['status'] != 'Aktif':
                    return []
                return review.evidence(identifier, self._sop_version or detail['version_id'], self._document_query or query)
            exact_read = getattr(self._engine, 'selected_document_evidence', None)
            if exact_read is not None:
                selected = exact_read(identifier)
                if selected is not None:
                    return selected
        evidence = self._engine.search_knowledge(query, top_k=top_k, filter=filter)
        return [item for item in evidence if not review.is_pilot(item.document_id) or review.detail(item.document_id)['status'] == 'Aktif']
