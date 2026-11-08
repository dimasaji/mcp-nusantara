"""V1 knowledge boundary: existing sources are internal until publication approval.

This deliberately provides no public-publication switch. An operator credential
is checked by the HTTP owner, never accepted from a chat body or model output.
No production metadata/index migration is needed to fail closed.
"""
import hashlib
import json
import re

from fastapi import HTTPException

CHAT_SESSION_PATTERN = r'^web-[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$'


def valid_chat_session(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch(CHAT_SESSION_PATTERN, value) is not None


def v1_session_id(session_id: str, *, operator: bool) -> str:
    """Quarantine legacy histories and separate public/operator context + replay."""
    audience = 'operator' if operator else 'public'
    return f'v1-{audience}-' + hashlib.sha256(session_id.encode('utf-8')).hexdigest()


class V1KnowledgeBoundary:
    def __init__(self, engine, *, operator: bool, provider: str, sop_version=None, document_ids=None, document_query=None, review_trial=False):
        if operator and provider != 'ollama':
            raise HTTPException(409, 'INTERNAL_KNOWLEDGE_REQUIRES_LOCAL_OPERATOR_MODEL')
        self._engine = engine
        self._operator = operator
        self._provider = provider
        self._sop_version = sop_version
        self._document_ids = document_ids or []
        self._document_query = document_query
        self._review_trial = review_trial
        self._versions = {}

    @staticmethod
    def _legacy_version(document):
        return hashlib.sha256(json.dumps([document.title, document.source, document.metadata],
                                         sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def _remember(self, evidence, review):
        for item in evidence:
            if review.is_pilot(item.document_id):
                version = item.metadata.get('version_id')
                if not version:
                    raise HTTPException(409, 'CHAT_SOURCE_VERSION_UNAVAILABLE')
            else:
                document = self._engine.rag.get_document_info(item.document_id)
                if document is None:
                    raise HTTPException(409, 'CHAT_SOURCE_VERSION_UNAVAILABLE')
                version = self._legacy_version(document)
            self._versions[item.document_id] = version
        return evidence

    def source_versions(self, answer):
        """Private retrieval-time bindings; never add these to public citations."""
        return {item['document_id']: self._versions[item['document_id']]
                for item in answer.get('evidence', [])}

    def document_answer_facts(self, question, evidence):
        """Approved document chat invokes the same registered core skill."""
        if self._review_trial:
            from app.knowledge.document_answers import document_answer_facts
            return document_answer_facts(question, evidence)
        if not self._operator or len(evidence) != 1:
            return None
        item = evidence[0]
        version = item.metadata.get('version_id')
        if not version:
            return None
        from app.skills.composition import OPERATOR_PERMISSIONS
        result = self._engine.skills.execute('sop.facts',
            {'document_id': item.document_id, 'version_id': version, 'question': question},
            role='operator', permissions=set(OPERATOR_PERMISSIONS), requested_by='operator-chat')
        if result.status != 'executed':
            raise HTTPException(503, 'SOP_SKILL_UNAVAILABLE')
        return result.output.get('facts')

    def validate_response(self, answer, source_versions=None):
        if not isinstance(answer, dict):
            raise HTTPException(409, 'CHAT_SOURCE_VERSION_UNAVAILABLE')
        citations = answer.get('evidence', [])
        if not citations:
            return
        if not self._operator or self._provider != 'ollama':
            raise HTTPException(409, 'CHAT_SOURCE_ACCESS_CHANGED')
        from app.knowledge.sop_review import SOPReview
        review = SOPReview(self._engine)
        versions = self._versions if source_versions is None else source_versions
        for citation in citations:
            identifier = citation['document_id']
            if not isinstance(versions, dict) or identifier not in versions:
                raise HTTPException(409, 'CHAT_SOURCE_VERSION_UNAVAILABLE')
            if review.is_pilot(identifier):
                detail = review.detail(identifier)
                if self._review_trial:
                    if self._sop_version != detail['version_id']:
                        raise HTTPException(409, 'CHAT_SOURCE_APPROVAL_OR_VERSION_CHANGED')
                elif detail['status'] != 'Aktif':
                    raise HTTPException(409, 'CHAT_SOURCE_APPROVAL_OR_VERSION_CHANGED')
                current = detail['version_id']
            else:
                document = self._engine.rag.get_document_info(identifier)
                if document is None:
                    raise HTTPException(409, 'CHAT_SOURCE_APPROVAL_OR_VERSION_CHANGED')
                current = self._legacy_version(document)
            if current != versions[identifier]:
                raise HTTPException(409, 'CHAT_SOURCE_APPROVAL_OR_VERSION_CHANGED')

    def search_documents(self, query, *, limit=10, domain=None, filter=None):
        """Catalog search: authorization/domain precede document-level ranking.

        Unlike answer retrieval this returns cards, not budgeted PDF contexts.
        Choosing a result never grants access or bypasses a fresh version check.
        """
        if not self._operator:
            return []
        if type(limit) is not int or not 1 <= limit <= 20 or domain not in (None, 'sop'):
            raise ValueError('KNOWLEDGE_CATALOG_ARGUMENT_INVALID')
        from app.knowledge.engine import KnowledgeEngine
        from app.knowledge.sop_review import SOPReview
        review = SOPReview(self._engine)
        scope = KnowledgeEngine.document_scope(filter)
        if scope is None and self._document_ids:
            scope = self._document_ids
        eligible, versions, titles = [], {}, {}
        for document in self._engine.list_documents().documents:
            identifier = document.document_id
            if scope is not None and identifier not in scope:
                continue
            controlled = review.is_pilot(identifier)
            detail = review.detail(identifier) if controlled else None
            if detail and detail['status'] != 'Aktif':
                continue
            info = self._engine.rag.get_document_info(identifier)
            if domain == 'sop':
                if detail is None:
                    continue  # Source markers cannot grant publication approval.
                metadata = info.metadata
                kind = metadata.get('document_kind')
                official = (detail or {}).get('official_metadata') or {}
                number = (official.get('sop_number') or {}).get('value')
                heading = (official.get('official_title') or {}).get('value', '') + '\n' + metadata.get('final_index', {}).get('source', info.source)[:2000]
                # Explicit kind wins; otherwise use source-backed SOP markers.
                if kind != 'sop' and (kind is not None or not (number or re.search(
                        r'(?:^|\n)\s*(?:S\.?O\.?P\.?\b|STANDAR(?:D)? OPERASIONAL PROSEDUR\b)|\bNAMA\s+S\.?O\.?P\.?\b',
                        heading, re.I))):
                    continue
            eligible.append(identifier)
            versions[identifier] = detail['version_id'] if detail else self._legacy_version(info)
            titles[identifier] = detail['title'] if detail else info.title
        if not eligible:
            return []
        for identifier in eligible:
            self._engine.ensure_final_document_index(identifier)
        evidence = self._engine.search_authorized_documents(query, eligible, top_k=limit, distinct_documents=True)
        cards = []
        for item in evidence:
            identifier = item.document_id
            info = self._engine.rag.get_document_info(identifier)
            if review.is_pilot(identifier):
                detail = review.detail(identifier)
                if (detail['status'] != 'Aktif' or detail['version_id'] != versions[identifier]
                        or detail['source_type'] == '.pdf' and item.metadata.get('final_index_version') != detail['version_id']):
                    raise HTTPException(409, 'CHAT_SOURCE_APPROVAL_OR_VERSION_CHANGED')
            elif info is None or self._legacy_version(info) != versions[identifier]:
                raise HTTPException(409, 'CHAT_SOURCE_APPROVAL_OR_VERSION_CHANGED')
            cards.append({'document_id': identifier, 'title': titles[identifier]})
        return cards

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
                if not self._review_trial and detail['status'] != 'Aktif':
                    return []
                if not self._review_trial:
                    self._engine.ensure_final_document_index(identifier)
                return self._remember(review.evidence(identifier, self._sop_version or detail['version_id'], self._document_query or query), review)
            exact_read = getattr(self._engine, 'selected_document_evidence', None)
            if exact_read is not None:
                selected = exact_read(identifier)
                if selected is not None:
                    return self._remember(selected, review)
        from app.knowledge.engine import KnowledgeEngine
        scope = KnowledgeEngine.document_scope(filter)
        if scope is None and self._document_ids:
            scope = self._document_ids
        eligible = [doc.document_id for doc in self._engine.list_documents().documents
                    if (scope is None or doc.document_id in scope)
                    and (not review.is_pilot(doc.document_id)
                         or review.detail(doc.document_id)['status'] == 'Aktif')]
        if not eligible:
            return []
        for identifier in eligible:
            self._engine.ensure_final_document_index(identifier)
        limit = top_k or self._engine.retrieval_top_k
        # Authorization precedes a single query over the complete eligible
        # corpus; public request filter limits are not widened.
        evidence = self._engine.search_authorized_documents(query, eligible, top_k=limit)
        result, hydrated = [], set()
        for item in evidence:
            if not review.is_pilot(item.document_id):
                result.append(item)
                continue
            if item.document_id in hydrated:
                continue
            hydrated.add(item.document_id)
            detail = review.detail(item.document_id)
            if detail['status'] != 'Aktif':
                raise HTTPException(409, 'CHAT_SOURCE_APPROVAL_OR_VERSION_CHANGED')
            if (detail['source_type'] == '.pdf'
                    and item.metadata.get('final_index_version') != detail['version_id']):
                raise HTTPException(409, 'CHAT_SOURCE_APPROVAL_OR_VERSION_CHANGED')
            if detail['status'] == 'Aktif':
                extracted = review.evidence(item.document_id, detail['version_id'], self._document_query or query)
                for citation in extracted:
                    citation.score = item.score
                result.extend(extracted)
        return self._remember(result, review)

