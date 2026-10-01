"""
RAG - Retrieval Augmented Generation orchestration.
Pipeline: Document â†’ Parser â†’ Chunker â†’ Embedding â†’ Vector Store â†’ Retriever â†’ Reranker â†’ Evidence Pack.
"""
import hashlib
import logging
import os
from typing import Any, Dict, List, Optional, Union
from app.knowledge.schemas import (
    DocumentMetadata,
    TextChunk,
    StoredChunk,
    Evidence,
    EvidencePack,
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentInfo,
    DocumentListResponse,
    KnowledgeBaseConfig,
    KnowledgeStore,
    QueryResult,
    RetrievalResult,
)
from app.knowledge.chunker import (
    Chunker,
    SentenceChunker,
    ParagraphChunker,
    get_chunker,
)
from app.knowledge.parser import (
    TextParser,
    MarkdownParser,
    PdfParser,
    DocumentParser,
    Parser,
    get_parser,
)


logger = logging.getLogger(__name__)
from app.knowledge.indobert_embedding import IndoBERTEmbeddingAdapter
from app.knowledge.store import SQLiteVectorStore


class MemoriaVectorStore:
    """
    Vector store sederhana di-memory (fallback jika ChromaDB/Qdrant tidak tersedia).
    Mendukung similarity search dengan cosine similarity.
    """

    def __init__(self):
        self._chunks: Dict[str, StoredChunk] = {}
        self._doc_chunks: Dict[str, List[str]] = {}
        self._doc_info: Dict[str, DocumentInfo] = {}

    def store_chunk(self, chunk: StoredChunk) -> None:
        """Simpan chunk ke store."""
        self._chunks[chunk.chunk_id] = chunk
        doc_id = chunk.document_id
        if doc_id not in self._doc_chunks:
            self._doc_chunks[doc_id] = []
        self._doc_chunks[doc_id].append(chunk.chunk_id)

    def store_document_info(self, info: DocumentInfo) -> None:
        """Simpan info dokumen."""
        self._doc_info[info.document_id] = info

    def get_chunk(self, chunk_id: str) -> Optional[StoredChunk]:
        """Get chunk by ID."""
        return self._chunks.get(chunk_id)

    def get_chunks_by_document(self, document_id: str) -> List[StoredChunk]:
        """Get semua chunk dari dokumen."""
        chunk_ids = self._doc_chunks.get(document_id, [])
        return [self._chunks[cid] for cid in chunk_ids if cid in self._chunks]

    def search_similarity(
        self,
        embedding: List[float],
        top_k: int = 5,
    ) -> List[tuple[float, StoredChunk]]:
        """
        Search chunk dengan cosine similarity terhadap embedding query.
        """
        if not self._chunks:
            return []

        best_chunks = []
        for chunk in self._chunks.values():
            if chunk.embedding is None:
                continue
            similarity = self._cosine_similarity(
                embedding, chunk.embedding.vector
            )
            best_chunks.append((similarity, chunk))

        best_chunks.sort(key=lambda x: x[0], reverse=True)
        return best_chunks[:top_k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Hitung cosine similarity."""
        if len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = (sum(x * x for x in a)) ** 0.5
        norm_b = (sum(x * x for x in b)) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def delete_document(self, document_id: str) -> bool:
        """Hapus dokumen dan semua chunk-nya."""
        chunk_ids = self._doc_chunks.get(document_id, [])
        for cid in chunk_ids:
            if cid in self._chunks:
                del self._chunks[cid]
        if document_id in self._doc_chunks:
            del self._doc_chunks[document_id]
        if document_id in self._doc_info:
            del self._doc_info[document_id]
        return True

    def list_documents(self) -> List[DocumentInfo]:
        """List semua dokumen."""
        return list(self._doc_info.values())


class DocParser:
    """
    DocParser - Parser dokumen ke teks.
    Mendukung TXT, MD, PDF.
    """

    def __init__(self, parsers: Optional[Dict[str, Parser]] = None):
        self._parsers = parsers or {}
        self._default_parser = TextParser()

    def add_parser(self, content_type: str, parser: Parser) -> None:
        """Registrasi parser untuk content type."""
        self._parsers[content_type] = parser

    def parse(self, source: str, content_type: str = "text/plain") -> str:
        """Parse dokumen ke teks."""
        parser = self._parsers.get(content_type, self._default_parser)
        return parser.parse(source)


class ChunkProcessor:
    """
    ChunkProcessor - Proses chunk teks.
    Mengelola chunking, embedding, dan penyimpanan.
    """

    def __init__(
        self,
        chunker: Optional[Chunker] = None,
        embedding_func=None,
        vector_store: Optional[MemoriaVectorStore] = None,
        config: Optional[KnowledgeBaseConfig] = None,
    ):
        self._chunker = chunker or SentenceChunker()
        self._embedding_func = embedding_func or self._default_embedding
        self._store = vector_store or SQLiteVectorStore()
        self._config = config or KnowledgeBaseConfig()

    def default_embedding(self, text: str) -> List[float]:
        """Embedding default (placeholder - nanti diganti dengan model nyata)."""
        # Placeholder: hash-based embedding (bukan semantic)
        # Diimplementasi nanti dengan model embedding nyata
        return self._hash_embedding(text)

    def _hash_embedding(self, text: str) -> List[float]:
        """Generate pseudo-embedding dari hash (untuk testing tanpa model)."""
        import hashlib
        import struct

        hash_bytes = hashlib.md5(text.encode()).digest()
        return [float(b) / 255.0 for b in hash_bytes[:384]]

    def set_embedding_func(self, func) -> None:
        """Set fungsi embedding custom."""
        self._embedding_func = func

    def get_store(self) -> MemoriaVectorStore:
        """Get vector store."""
        return self._store

    def set_store(self, store: MemoriaVectorStore) -> None:
        """Set vector store custom."""
        self._store = store


class RAG:
    """
    RAG - Retrieval Augmented Generation orchestrator.
    Pipeline lengkap dari ingest document sampai retrieval.
    """

    def __init__(
        self,
        config: Optional[KnowledgeBaseConfig] = None,
        vector_store: Optional[MemoriaVectorStore] = None,
        parser: Optional[DocParser] = None,
        chunker: Optional[Chunker] = None,
        embedding_func=None,
    ):
        self._config = config or KnowledgeBaseConfig()
        self._store = vector_store or SQLiteVectorStore()
        self._parser = parser or DocParser()
        self._chunker = chunker or SentenceChunker()
        # Gunakan IndoBERT 768D sebagai default embedding RAG.
        # Jika embedding_func diberikan dari luar, tetap gunakan custom embedding.
        self._embedding_adapter = None
        if embedding_func is not None:
            self._embedding = embedding_func
        else:
            self._embedding_adapter = IndoBERTEmbeddingAdapter()
            self._embedding = self._embedding_adapter
        self._chunk_processor = None

    def _default_embedding(self, text: str) -> List[float]:
        """Default embedding (placeholder)."""
        import hashlib

        # Simple hash-based embedding untuk testing
        hash_bytes = hashlib.md5(text.encode()).digest()
        return [float(b) / 255.0 for b in hash_bytes[:self._config.embedding_dimension]]

    def set_embedding_func(self, func) -> None:
        """Set fungsi embedding custom."""
        self._embedding = func

    def ingest_document(
        self,
        request: DocumentIngestRequest,
    ) -> DocumentIngestResponse:
        """
        Ingest dokumen ke knowledge base.
        Pipeline: Parser â†’ Chunker â†’ Embedding â†’ Store.
        """
        import time

        start_time = time.time()
        error = None

        try:
            # 1. Parse dokumen ke teks
            content_type = request.content_type or "text/plain"
            source = request.source or ""

            parser = DocumentParser()

            text_content = parser.parse(
                source,
                content_type=content_type,
                filename=source if isinstance(source, str) else None,
            )

            if not isinstance(text_content, str):
                text_content = str(text_content)

            text_content = text_content.strip()

            if not text_content:
                raise ValueError(
                    f"Dokumen '{request.title}' tidak menghasilkan teks."
                )

            # 2. Generate metadata
            doc_id = request.document_id or self._generate_doc_id(request.title, request.source)
            checksum = self._compute_checksum(text_content)

            metadata = DocumentMetadata(
                document_id=doc_id,
                title=request.title,
                source=request.source,
                content_type=content_type,
                size_bytes=len(text_content.encode()),
                checksum=checksum,
                custom_metadata=request.metadata or {},
            )

            # 3. Chunking
            chunk_size = request.chunk_size or self._config.chunk_size
            chunk_overlap = request.chunk_overlap or self._config.chunk_overlap

            # Chunker implementations own their configured size/overlap.
            # Recreate the chunker when request-level settings differ.
            if chunk_size != self._chunker.chunk_size or chunk_overlap != self._chunker.overlap:
                chunker = type(self._chunker)(chunk_size, chunk_overlap)
            else:
                chunker = self._chunker
            raw_chunks = chunker.chunk(text_content)
            chunks = []
            cursor = 0
            for i, raw_chunk in enumerate(raw_chunks):
                content = raw_chunk.content if isinstance(raw_chunk, TextChunk) else str(raw_chunk)
                start_char = cursor
                end_char = cursor + len(content)
                chunks.append(
                    raw_chunk if isinstance(raw_chunk, TextChunk) else TextChunk(
                        chunk_id=f"{doc_id}-{i}",
                        document_id=doc_id,
                        chunk_index=i,
                        content=content,
                        start_char=start_char,
                        end_char=end_char,
                    )
                )
                cursor = end_char
            if not chunks:
                chunks = [TextChunk(
                    chunk_id=f"{doc_id}-0",
                    document_id=doc_id,
                    chunk_index=0,
                    content=text_content,
                    start_char=0,
                    end_char=len(text_content),
                )]

            # 4. Simpan info dokumen terlebih dahulu agar Foreign Key SQLite valid
            doc_info = DocumentInfo(
                document_id=doc_id,
                title=request.title,
                source=request.source,
                content_type=content_type,
                chunks_count=0,
                size_bytes=len(text_content.encode()),
                created_at=metadata.created_at,
                updated_at=metadata.created_at,
                metadata=request.metadata or {},
            )
            self._store.store_document_info(doc_info)

            # 5. Embedding dan simpan chunk
            chunks_stored = 0
            for i, chunk in enumerate(chunks):
                # TextChunk is an immutable Pydantic model; keep embedding data in
                # the StoredChunk instead of mutating the source chunk.
                embedding_vector = self._embedding(chunk.content)
                embedding_data = {
                    "vector": embedding_vector,
                    "dimension": len(embedding_vector),
                    "model": self._config.embedding_model,
                }

                stored_chunk = StoredChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    tokens_estimate=chunk.tokens_estimate,
                    metadata=chunk.metadata,
                    embedding=embedding_data,
                    stored_at=metadata.created_at,
                    store_id=chunk.chunk_id,
                )

                self._store.store_chunk(stored_chunk)
                chunks_stored += 1

            self._store.update_document_chunks_count(
                doc_id,
                chunks_stored,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            return DocumentIngestResponse(
                success=True,
                document_id=doc_id,
                title=request.title,
                chunks_created=len(chunks),
                chunks_stored=chunks_stored,
                total_time_ms=elapsed_ms,
                error=None,
            )

        except Exception as e:
            error = str(e)
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Gagal ingest dokumen: {error}")
            return DocumentIngestResponse(
                success=False,
                document_id=None,
                title=request.title,
                chunks_created=0,
                chunks_stored=0,
                total_time_ms=elapsed_ms,
                error=error,
            )

    def _generate_doc_id(self, title: str, source: str) -> str:
        """Generate ID dokumen dari title dan source."""
        import uuid
        base = hashlib.md5(f"{title}:{source}".encode()).hexdigest()[:8]
        return f"DOC-{base.upper()}-{uuid.uuid4().hex[:4]}"

    def _compute_checksum(self, content: str) -> str:
        """Compute checksum dari konten."""
        return hashlib.md5(content.encode()).hexdigest()

    def query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        rerank: bool = False,
    ) -> RetrievalResult:
        """
        Query knowledge base menggunakan Hybrid Retrieval.

        Pipeline:
        Semantic (IndoBERT) + Lexical Search
        -> Candidate Fusion
        -> Hybrid Score
        -> Top-K
        -> Evidence Pack
        """
        import time

        start_time = time.time()

        top_k = top_k or self._config.retrieval_top_k

        # Ambil candidate lebih banyak sebelum fusion.
        candidate_k = max(top_k * 4, 20)

        # ============================================================
        # 1. SEMANTIC RETRIEVAL
        # ============================================================
        query_embedding = self._embedding(query_text)

        semantic_candidates = self._store.search_similarity(
            query_embedding,
            candidate_k,
        )

        # ============================================================
        # 2. LEXICAL RETRIEVAL
        # ============================================================
        lexical_candidates = self._store.search_lexical(
            query_text,
            candidate_k,
        )

        # ============================================================
        # 3. FUSION
        # Semantic 70% + Lexical 30%
        # Bobot ini masih eksperimen dan akan divalidasi benchmark.
        # ============================================================
        candidates = {}

        for chunk, score in semantic_candidates:
            candidates[chunk.chunk_id] = {
                "chunk": chunk,
                "semantic_score": float(score),
                "lexical_score": 0.0,
            }

        for chunk, score in lexical_candidates:
            if chunk.chunk_id not in candidates:
                candidates[chunk.chunk_id] = {
                    "chunk": chunk,
                    "semantic_score": 0.0,
                    "lexical_score": float(score),
                }
            else:
                candidates[chunk.chunk_id]["lexical_score"] = float(score)

        fused = []

        for item in candidates.values():
            semantic_score = item["semantic_score"]
            lexical_score = item["lexical_score"]

            hybrid_score = (
                0.70 * semantic_score
                + 0.30 * lexical_score
            )

            fused.append(
                (
                    item["chunk"],
                    hybrid_score,
                    semantic_score,
                    lexical_score,
                )
            )

        fused.sort(key=lambda item: item[1], reverse=True)

        # ============================================================
        # 4. BUILD EVIDENCE
        # ============================================================
        evidence_list = []
        seen_documents = set()

        for (
            chunk,
            hybrid_score,
            semantic_score,
            lexical_score,
        ) in fused[:top_k]:

            doc_info = self._store.get_document_info(
                chunk.document_id
            )

            metadata = dict(chunk.metadata or {})

            metadata["semantic_score"] = round(
                semantic_score, 6
            )
            metadata["lexical_score"] = round(
                lexical_score, 6
            )
            metadata["hybrid_score"] = round(
                hybrid_score, 6
            )

            evidence = Evidence(
                document_id=chunk.document_id,
                title=doc_info.title if doc_info else "",
                source=doc_info.source if doc_info else "",
                chunk=chunk.content,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata=metadata,
                score=float(hybrid_score),
            )

            evidence_list.append(evidence)
            seen_documents.add(chunk.document_id)

        # ============================================================
        # 5. OPTIONAL RERANK
        # ============================================================
        if rerank and self._config.reranker_enabled:
            evidence_list = self._simple_rerank(
                evidence_list,
                query_text,
            )

        elapsed_ms = int(
            (time.time() - start_time) * 1000
        )

        evidence_pack = EvidencePack(
            query=query_text,
            total_chunks=len(evidence_list),
            total_documents=len(seen_documents),
            evidence=evidence_list,
            reranked=rerank and self._config.reranker_enabled,
            reranker_model=(
                self._config.reranker_model
                if rerank else None
            ),
            retrieval_method="hybrid",
            metadata={
                "semantic_weight": 0.70,
                "lexical_weight": 0.30,
                "candidate_k": candidate_k,
            },
        )

        return RetrievalResult(
            query=query_text,
            evidence_pack=evidence_pack,
            total_time_ms=elapsed_ms,
            chunks_retrieved=len(evidence_list),
            documents_retrieved=len(seen_documents),
        )

    def _simple_rerank(
        self,
        evidence: List[Evidence],
        query: str,
    ) -> List[Evidence]:
        """
        Reranking sederhana berdasarkan kemiripan teks.
        Ini adalah fallback - diimplementasi nanti dengan model reranker nyata.
        """
        # Simple TF-IDF-like scoring
        query_words = set(query.lower().split())
        scored = []

        for ev in evidence:
            chunk_words = set(ev.chunk.lower().split())
            overlap = len(query_words & chunk_words)
            score = overlap / max(len(query_words), 1)
            # Batasi score max 1.0
            score = min(score, 1.0)
            ev.score = score
            scored.append(ev)

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    def list_documents(self) -> DocumentListResponse:
        """List semua dokumen di knowledge base."""
        docs = self._store.list_documents()
        return DocumentListResponse(
            documents=docs,
            total=len(docs),
            page=1,
            page_size=self._config.retrieval_top_k,
        )

    def get_document_info(self, document_id: str) -> Optional[DocumentInfo]:
        """Get info dokumen."""
        return self._store.get_document_info(document_id)

    def delete_document(self, document_id: str) -> bool:
        """Hapus dokumen dari knowledge base."""
        return self._store.delete_document(document_id)

    def get_evidence_by_document(self, document_id: str) -> List[Evidence]:
        """Get semua evidence dari dokumen."""
        chunks = self._store.get_chunks_by_document(document_id)
        evidences = []
        for chunk in chunks:
            doc_info = self._store.get_document_info(chunk.document_id)
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
            evidences.append(evidence)
        return evidences


def create_rag(
    config: Optional[KnowledgeBaseConfig] = None,
    vector_store: Optional[MemoriaVectorStore] = None,
) -> RAG:
    """Factory function untuk membuat RAG instance."""
    return RAG(config=config, vector_store=vector_store)











