"""
Retriever - Retrieve evidence dari knowledge base.
Mendukung multiple retrieval method: similarity, hybrid, semantic.
"""
from typing import List, Optional
from app.knowledge.schemas import (
    Evidence,
    EvidencePack,
    RetrievalResult,
    KnowledgeBaseConfig,
)
from app.knowledge.rag import MemoriaVectorStore
from app.knowledge.embeddings import EmbeddingProvider


class Retriever:
    """
    Retriever untuk mengambil evidence dari knowledge base.
    Mudah di-extend untuk multiple retrieval strategy.
    """

    def __init__(
        self,
        vector_store: MemoriaVectorStore,
        embedding_provider: Optional[EmbeddingProvider] = None,
        config: Optional[KnowledgeBaseConfig] = None,
    ):
        self._store = vector_store
        self._embedding = embedding_provider
        self._config = config or KnowledgeBaseConfig()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_by: Optional[dict] = None,
    ) -> RetrievalResult:
        """
        Retrieve evidence dari knowledge base.
        """
        top_k = top_k or self._config.retrieval_top_k

        # Embed query
        if self._embedding is None:
            # Gunakan store default embedding
            query_embedding = self._default_embedding(query)
        else:
            query_embedding = self._embedding.embed(query)

        # Search
        matched_chunks = self._store.search_similarity(query_embedding, top_k)

        # Apply filter jika ada
        if filter_by:
            matched_chunks = self._apply_filter(matched_chunks, filter_by)

        # Build evidence
        evidence_list = []
        seen_documents = set()

        for similarity, chunk in matched_chunks:
            doc_info = self._store._doc_info.get(chunk.document_id)
            evidence = Evidence(
                document_id=chunk.document_id,
                title=doc_info.title if doc_info else "",
                source=doc_info.source if doc_info else "",
                chunk=chunk.content,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata=chunk.metadata,
                score=float(similarity),
            )
            evidence_list.append(evidence)
            seen_documents.add(chunk.document_id)

        return RetrievalResult(
            query=query,
            evidence_pack=EvidencePack(
                query=query,
                total_chunks=len(evidence_list),
                total_documents=len(seen_documents),
                evidence=evidence_list,
                retrieval_method="similarity",
            ),
            chunks_retrieved=len(evidence_list),
            documents_retrieved=len(seen_documents),
        )

    def _default_embedding(self, text: str) -> List[float]:
        """Default embedding menggunakan hash."""
        import hashlib
        dim = self._config.embedding_dimension
        hash_bytes = hashlib.md5(text.encode()).digest()
        result = []
        for i in range(dim):
            if i < len(hash_bytes):
                result.append(float(hash_bytes[i]) / 255.0)
            else:
                result.append(0.0)
        return result

    def _apply_filter(
        self,
        chunks: List,
        filter_by: dict,
    ) -> List:
        """Apply filter pada chunks."""
        result = []
        for item in chunks:
            similarity, chunk = item
            doc_info = self._store._doc_info.get(chunk.document_id)
            if doc_info is None:
                continue

            # Check filter
            include = True
            if "source" in filter_by:
                if filter_by["source"] not in doc_info.source:
                    include = False
            if "document_id" in filter_by:
                if filter_by["document_id"] != chunk.document_id:
                    include = False
            if "content_type" in filter_by:
                if filter_by["content_type"] != doc_info.content_type:
                    include = False

            if include:
                result.append((similarity, chunk))
        return result

    def retrieve_by_document(self, document_id: str) -> List[Evidence]:
        """Retrieve semua evidence dari dokumen tertentu."""
        chunks = self._store.get_chunks_by_document(document_id)
        evidence_list = []

        for chunk in chunks:
            doc_info = self._store._doc_info.get(chunk.document_id)
            evidence = Evidence(
                document_id=chunk.document_id,
                title=doc_info.title if doc_info else "",
                source=doc_info.source if doc_info else "",
                chunk=chunk.content,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata=chunk.metadata,
                score=0.0,
            )
            evidence_list.append(evidence)

        return evidence_list

    def retrieve_all(self) -> List[Evidence]:
        """Retrieve semua evidence dari knowledge base."""
        all_evidence = []
        for doc_id in self._store._doc_info:
            evidence_list = self.retrieve_by_document(doc_id)
            all_evidence.extend(evidence_list)
        return all_evidence


def create_retriever(
    vector_store: MemoriaVectorStore,
    embedding_provider: Optional[EmbeddingProvider] = None,
    config: Optional[KnowledgeBaseConfig] = None,
) -> Retriever:
    """Factory untuk membuat retriever."""
    return Retriever(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        config=config,
    )






