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
    make_rag_profile,
    publish_rag_profile,
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
from app.core.nusantara_config import ConfigurationError, NusantaraConfig


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
        *,
        nusantara_config: NusantaraConfig | None = None,
    ):
        self.configuration = nusantara_config
        self._kb_source = ('KB_EXPLICIT' if config is not None else
                           'R1' if nusantara_config is not None else 'KB_DEFAULT')
        if nusantara_config is not None:
            if (nusantara_config.rag.semantic_weight is not None or
                    nusantara_config.rag.similarity_threshold is not None):
                raise ConfigurationError("RAG_PARAMETER_NOT_INTEGRATED")
            if embedding_func is None:
                IndoBERTEmbeddingAdapter.validate_configuration(nusantara_config)
                if config is not None and (config.embedding_dimension != 768 or
                        config.embedding_model != "indobenchmark/indobert-base-p1"):
                    raise ConfigurationError("EMBEDDING_PROFILE_UNSUPPORTED")
        if nusantara_config is not None and config is None:
            config = KnowledgeBaseConfig(
                embedding_model=nusantara_config.embedding.model,
                embedding_dimension=nusantara_config.embedding.dimension,
                vector_store_type=nusantara_config.knowledge.store_backend,
                chunk_size=nusantara_config.rag.chunk_size,
                chunk_overlap=nusantara_config.rag.chunk_overlap,
                retrieval_top_k=nusantara_config.rag.top_k,
                reranker_enabled=nusantara_config.rag.reranker_enabled,
                reranker_model=nusantara_config.rag.reranker_model,
            )
        self._config = config or KnowledgeBaseConfig()
        self._kb_initial = self._config.model_dump()
        self._store = vector_store if vector_store is not None else (
            SQLiteVectorStore(str(nusantara_config.knowledge.database))
            if nusantara_config is not None else SQLiteVectorStore())
        self._parser = parser or DocParser()
        self._chunker = chunker or SentenceChunker()
        # Gunakan IndoBERT 768D sebagai default embedding RAG.
        # Jika embedding_func diberikan dari luar, tetap gunakan custom embedding.
        self._embedding_adapter = None
        if embedding_func is not None:
            self._embedding = embedding_func
        else:
            self._embedding_adapter = (IndoBERTEmbeddingAdapter(nusantara_config=nusantara_config)
                                       if nusantara_config is not None else IndoBERTEmbeddingAdapter())
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

    def _profile_descriptor(self, requested_top_k, top_k, rerank, candidate_k):
        """Observe existing owners; this is not a configuration loader."""
        from app.core.runtime_identity import BUILD_ID

        snapshot = self.configuration
        kb = self._config
        sqlite_store = type(self._store) is SQLiteVectorStore
        default_embedding = self._embedding_adapter is not None and self._embedding is self._embedding_adapter
        known_reranker = getattr(self._simple_rerank, '__func__', None) is RAG._simple_rerank
        algorithm = ('simple_keyword_overlap' if known_reranker else 'NOT_VERIFIED') if rerank and kb.reranker_enabled else 'NOT_APPLICABLE'
        values = {
            'top_k': top_k, 'semantic_weight': 0.70, 'lexical_weight': 0.30,
            'candidate_count': candidate_k, 'retrieval_mode': 'hybrid',
            'semantic_normalization': 'cosine_without_rescaling' if sqlite_store else 'NOT_VERIFIED',
            'lexical_normalization': 'token_overlap/query_tokens_capped_at_1' if sqlite_store else 'NOT_VERIFIED',
            'missing_stage_score': 0.0, 'absolute_relevance_gate': 0.30,
            'relative_threshold': 0.50, 'rerank_requested': bool(rerank),
            'rerank_enabled': kb.reranker_enabled,
            'actual_reranker': algorithm,
            'knowledge_source': {'implementation': type(self._store).__module__ + '.' + type(self._store).__qualname__,
                                 'reference': str(self._store.db_path) if sqlite_store else None,
                                 'status': 'EFFECTIVE' if sqlite_store else 'NOT_VERIFIED'},
            'embedding_identity': {'configured_model': kb.embedding_model,
                                   'configured_dimension': kb.embedding_dimension,
                                   'implementation': 'IndoBERTEmbeddingAdapter' if default_embedding else 'custom_callable',
                                   'actual_model': None, 'status': 'NOT_VERIFIED'},
        }
        provenance = {}

        def record(name, configured=None, layer='RAG_INTERNAL', location='app/knowledge/rag.py:RAG.query',
                   override=None, precedence='internal implementation constant', status='EFFECTIVE'):
            provenance[name] = {'parameter': name, 'source': layer, 'source_location': location,
                                'source_layer': layer, 'configured_value': configured,
                                'effective_value': values[name], 'precedence': precedence,
                                'override': override, 'status': status}

        r1_sources = {entry.field: entry.source for entry in snapshot.provenance} if snapshot else {}
        for name in values:
            record(name)
        for name, field, r1_field in [('top_k', 'retrieval_top_k', 'rag.top_k'),
                                     ('rerank_enabled', 'reranker_enabled', 'rag.reranker_enabled')]:
            layer = self._kb_source
            if getattr(kb, field) != self._kb_initial[field]:
                layer = 'INSTANCE_MUTATION'
            if layer == 'R1':
                layer = 'R1_' + r1_sources.get(r1_field, 'NOT_VERIFIED')
            record(name, getattr(snapshot.rag, 'top_k' if name == 'top_k' else field) if snapshot else None,
                   layer=layer, location='app/knowledge/rag.py:RAG.__init__ -> KnowledgeBaseConfig.' + field,
                   precedence='argument or instance value; KB_EXPLICIT > R1 > KB_DEFAULT',
                   status='INHERITED' if layer.startswith('R1_') else 'DEFAULT' if layer == 'KB_DEFAULT' else 'EFFECTIVE')
        if requested_top_k:
            record('top_k', snapshot.rag.top_k if snapshot else None, layer='INVOCATION',
                   override=requested_top_k, precedence='truthy argument > instance value', status='OVERRIDDEN')
        else:
            provenance['top_k']['override'] = requested_top_k
        provenance['top_k']['instance_value'] = kb.retrieval_top_k
        for name in ('semantic_weight', 'lexical_weight'):
            provenance[name]['configured_value'] = getattr(snapshot.rag, name) if snapshot else None
        record('candidate_count', layer='DERIVED', precedence='max(effective_top_k * 4, 20)')
        record('rerank_requested', False, layer='INVOCATION', override=bool(rerank),
               precedence='query argument; default False', status='OVERRIDDEN' if rerank else 'DEFAULT')
        for name in ('semantic_normalization', 'lexical_normalization'):
            record(name, layer='STORE_IMPLEMENTATION', location='app/knowledge/store.py:SQLiteVectorStore',
                   status='EFFECTIVE' if sqlite_store else 'NOT_VERIFIED')
        record('knowledge_source', layer='STORE_INSTANCE', location='app/knowledge/rag.py:RAG.__init__',
               status=values['knowledge_source']['status'])
        record('embedding_identity', layer='EMBEDDING_INSTANCE', location='app/knowledge/rag.py:RAG.__init__/set_embedding_func',
               status='NOT_VERIFIED')
        record('actual_reranker', layer='RERANKER_IMPLEMENTATION', location='app/knowledge/rag.py:RAG._simple_rerank',
               status='NOT_VERIFIED' if algorithm == 'NOT_VERIFIED' else 'EFFECTIVE')
        return {
            'profile_version': 1, 'effective_values': values,
            'source_config': {'fingerprint': 'sha256:' + hashlib.sha256(snapshot.canonical_json().encode()).hexdigest()
                              if snapshot else None, 'status': 'R1_SNAPSHOT' if snapshot else 'NOT_VERIFIED'},
            'source_build_id': BUILD_ID,
            'retrieval_strategy': 'canonical_hybrid_semantic_lexical_topk_rerank_gate',
            'reranker_identity': {'algorithm': values['actual_reranker'], 'configured_label': kb.reranker_model,
                                  'model_identity': 'NOT_APPLICABLE' if known_reranker else 'NOT_VERIFIED', 'requested': bool(rerank),
                                  'enabled': kb.reranker_enabled},
            'thresholds': {'absolute_relevance_gate': 0.30, 'relative_threshold': 0.50,
                           'score_space': 'keyword_overlap' if algorithm == 'simple_keyword_overlap' else 'NOT_VERIFIED' if algorithm == 'NOT_VERIFIED' else 'hybrid'},
            'provenance': provenance,
        }

    def query(self, query_text: str, top_k: Optional[int] = None, rerank: bool = False) -> RetrievalResult:
        effective_top_k = top_k or self._config.retrieval_top_k
        candidate_k = max(effective_top_k * 4, 20)
        descriptor = self._profile_descriptor(top_k, effective_top_k, rerank, candidate_k)
        receipt = make_rag_profile(descriptor)
        trace = {'status': 'STARTED', 'stage': 'embedding', 'gate_status': 'NOT_EXECUTED',
                 'reranker_status': 'NOT_EXECUTED', 'resolved_relevance_gate': None}

        def finish_receipt():
            # Observe mutations by custom callbacks without changing their behavior.
            if 'rerank_enabled_consumed' in trace:
                enabled = trace['rerank_enabled_consumed']
                algorithm = trace['reranker_algorithm_consumed'] if rerank and enabled else 'NOT_APPLICABLE'
                if enabled != descriptor['effective_values']['rerank_enabled']:
                    descriptor['provenance']['rerank_enabled'].update(source='INSTANCE_MUTATION', source_layer='INSTANCE_MUTATION')
                descriptor['effective_values'].update(rerank_enabled=enabled, actual_reranker=algorithm)
                descriptor['reranker_identity'].update(enabled=enabled, algorithm=algorithm,
                    configured_label=trace['reranker_label_consumed'],
                    model_identity='NOT_APPLICABLE' if algorithm != 'NOT_VERIFIED' else 'NOT_VERIFIED')
                descriptor['thresholds']['score_space'] = 'keyword_overlap' if algorithm == 'simple_keyword_overlap' else 'NOT_VERIFIED' if algorithm == 'NOT_VERIFIED' else 'hybrid'
                descriptor['provenance']['rerank_enabled']['effective_value'] = enabled
                descriptor['provenance']['actual_reranker'].update(effective_value=algorithm,
                    status='NOT_VERIFIED' if algorithm == 'NOT_VERIFIED' else 'EFFECTIVE')
            return receipt.with_descriptor(descriptor).complete(trace)

        try:
            result = self._query(query_text, effective_top_k, rerank, trace)
        except Exception as exc:
            trace.update(status='FAILED', exception_type=type(exc).__name__)
            publish_rag_profile(finish_receipt())
            raise
        trace.update(status='COMPLETED', stage='result', returned_count=result.chunks_retrieved)
        result.effective_profile = finish_receipt()
        publish_rag_profile(result.effective_profile)
        return result

    def _query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        rerank: bool = False,
        trace: Optional[dict] = None,
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

        trace['stage'] = 'semantic_search'

        semantic_candidates = self._store.search_similarity(
            query_embedding,
            candidate_k,
        )
        trace['semantic_count'] = 0
        trace['stage'] = 'lexical_search'

        # ============================================================
        # 2. LEXICAL RETRIEVAL
        # ============================================================
        lexical_candidates = self._store.search_lexical(
            query_text,
            candidate_k,
        )
        trace['lexical_count'] = 0
        trace['stage'] = 'fusion'

        # ============================================================
        # 3. FUSION
        # Semantic 70% + Lexical 30%
        # Bobot ini masih eksperimen dan akan divalidasi benchmark.
        # ============================================================
        candidates = {}

        for chunk, score in semantic_candidates:
            trace['semantic_count'] += 1
            candidates[chunk.chunk_id] = {
                "chunk": chunk,
                "semantic_score": float(score),
                "lexical_score": 0.0,
            }

        for chunk, score in lexical_candidates:
            trace['lexical_count'] += 1
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
        trace['rerank_enabled_consumed'] = self._config.reranker_enabled
        trace['reranker_label_consumed'] = self._config.reranker_model
        trace['reranker_algorithm_consumed'] = ('simple_keyword_overlap'
            if getattr(self._simple_rerank, '__func__', None) is RAG._simple_rerank else 'NOT_VERIFIED')
        if rerank and trace['rerank_enabled_consumed']:
            trace['stage'] = 'rerank'
            evidence_list = self._simple_rerank(
                evidence_list,
                query_text,
            )
            trace['reranker_status'] = 'EXECUTED'

        trace['stage'] = 'relevance_gate'
        trace['before_gate_count'] = len(evidence_list)
        trace['resolved_relevance_gate'] = (max(0.30, max(float(ev.score) for ev in evidence_list) * 0.50)
                                            if evidence_list else None)

        evidence_list = self._apply_relevance_gate(
            evidence_list,
            min_score=0.30,
            relative_threshold=0.50,
        )
        trace['gate_status'] = 'EXECUTED' if trace['before_gate_count'] else 'NOT_APPLICABLE_EMPTY'

        seen_documents = {
            ev.document_id
            for ev in evidence_list
        }

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

    def _apply_relevance_gate(
        self,
        evidence: List[Evidence],
        min_score: float = 0.30,
        relative_threshold: float = 0.50,
    ) -> List[Evidence]:
        """
        Buang evidence yang terlalu lemah agar dokumen tidak relevan
        tidak ikut dikirim ke LLM.
        """
        if not evidence:
            return []

        evidence = sorted(
            evidence,
            key=lambda item: item.score,
            reverse=True,
        )

        top_score = float(evidence[0].score)

        threshold = max(
            float(min_score),
            top_score * float(relative_threshold),
        )

        filtered = [
            ev
            for ev in evidence
            if float(ev.score) >= threshold
        ]

        logger.info(
            "RAG relevance gate: top_score=%.4f threshold=%.4f "
            "before=%d after=%d",
            top_score,
            threshold,
            len(evidence),
            len(filtered),
        )

        return filtered

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
        # Match word boundaries as lexical retrieval does: punctuation and KTP-el
        # must not erase otherwise-supported overlap before the relevance gate.
        import re
        query_words = set(re.findall(r"\b[a-zA-Z0-9_]+\b", query.lower()))
        scored = []

        for ev in evidence:
            chunk_words = set(re.findall(r"\b[a-zA-Z0-9_]+\b", ev.chunk.lower()))
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
    *,
    nusantara_config: NusantaraConfig | None = None,
) -> RAG:
    """Factory function untuk membuat RAG instance."""
    if nusantara_config is None:
        return RAG(config=config, vector_store=vector_store)
    return RAG(config=config, vector_store=vector_store, nusantara_config=nusantara_config)

# ---------------------------------------------------------------------------
# NUSANTARA CANONICAL RAG API
# ---------------------------------------------------------------------------
# Canonical public interface for Nusantara Core.
# The implementation remains in RAG.
# This is only a compatibility alias.
# ---------------------------------------------------------------------------

HybridRAG = RAG

