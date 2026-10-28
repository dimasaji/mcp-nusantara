"""Knowledge Engine facade used by the API and Hermes."""
from __future__ import annotations

from typing import Any, Optional

from .rag import RAG, create_rag
from app.core.nusantara_config import NusantaraConfig


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

    def search_knowledge(self, query: str, top_k: int = 5, filter: Optional[dict] = None):
        del filter  # reserved for vector-store filters in the persistent backend
        result = self.rag.query(query_text=query, top_k=top_k)
        return result.evidence_pack.evidence

    def search(self, query: str, top_k: int = 5):
        return self.search_knowledge(query, top_k=top_k)

    def list_documents(self):
        return self.rag.list_documents()
