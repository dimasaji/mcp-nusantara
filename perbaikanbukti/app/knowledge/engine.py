"""Knowledge Engine facade used by the API and Hermes."""
from __future__ import annotations

from typing import Any, Optional

from .rag import RAG, create_rag
from app.core.nusantara_config import NusantaraConfig
from .schemas import RetrievalEvidenceList


class KnowledgeEngine:
    def __init__(self, rag: Optional[RAG] = None, *, nusantara_config: NusantaraConfig | None = None):
        self.configuration = nusantara_config
        self.rag = rag if rag is not None else (
            create_rag(nusantara_config=nusantara_config) if nusantara_config is not None else create_rag())

    def ingest_document(self, document: Any):
        # Accept the lightweight API Document model as well as the canonical
        # DocumentIngestRequest used by RAG.
        from .schemas import DocumentIngestRequest
        if isinstance(document, DocumentIngestRequest):
            return self.rag.ingest_document(document)
        request = DocumentIngestRequest(
            document_id=getattr(document, "id", None),
            title=document.title,
            source=document.content,
            content_type="text/plain",
            metadata=getattr(document, "metadata", {}) or {},
        )
        return self.rag.ingest_document(request)

    def search_knowledge(self, query: str, top_k: int | None = None, filter: Optional[dict] = None):
        if filter is not None and filter != {}:
            # No approved metadata/authority filter grammar exists in V1 yet.
            # Never let a requested restriction silently become unrestricted search.
            raise ValueError('KNOWLEDGE_FILTER_NOT_SUPPORTED')
        result = self.rag.query(query_text=query, top_k=top_k)
        return RetrievalEvidenceList(result.evidence_pack.evidence, getattr(result, 'effective_profile', None))

    def search(self, query: str, top_k: int | None = None):
        return self.search_knowledge(query, top_k=top_k)

    def list_documents(self):
        return self.rag.list_documents()
