"""
Knowledge & RAG Engine Schemas.
Evidence dari document, chunking, embedding, retrieval, reranking.
"""
import hashlib
import json
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.observability.context import current_ids, new_id
from app.observability.logging import log_event


@dataclass(frozen=True)
class EffectiveRAGProfile:
    """Immutable internal receipt; JSON storage prevents nested mutation.

    Only the consumed descriptor determines profile_id. Execution data,
    request correlation, consumer and timestamps are outside that identity.
    """
    descriptor_json: str
    invocation_id: str
    timestamp: str
    consumer: str
    correlation_json: str
    outcome_json: str = '{}'
    consumer_filter_json: str = '{}'
    request_top_k_source: str | None = None

    @property
    def profile_id(self) -> str:
        descriptor = json.loads(self.descriptor_json)
        # Intent/provenance can differ while the same values are consumed
        # (e.g. omitted top_k versus zero falling back to the instance value).
        identity = {key: descriptor[key] for key in
                    ('profile_version', 'source_build_id', 'effective_values', 'retrieval_strategy', 'thresholds')}
        encoded = json.dumps(identity, sort_keys=True, separators=(',', ':'), allow_nan=False)
        return 'sha256:' + hashlib.sha256(encoded.encode()).hexdigest()

    def snapshot(self) -> dict[str, Any]:
        data = json.loads(self.descriptor_json)
        outcome = json.loads(self.outcome_json)
        data.update(profile_id=self.profile_id, invocation_id=self.invocation_id,
                    timestamp=self.timestamp, consumer=self.consumer,
                    correlation=json.loads(self.correlation_json), execution_outcome=outcome)
        data['thresholds']['resolved_relevance_gate'] = outcome.get('resolved_relevance_gate')
        data['thresholds']['consumer_post_filter'] = json.loads(self.consumer_filter_json)
        data['reranker_identity']['execution_status'] = outcome.get('reranker_status', 'NOT_EXECUTED')
        for entry in data['provenance'].values():
            entry.update(consumer=self.consumer, invocation_id=self.invocation_id)
        if self.request_top_k_source is not None:
            data['provenance']['top_k'].update(request_source=self.request_top_k_source,
                request_source_location='app/api/routes.py:KnowledgeSearchRequest.top_k')
        data['provenance']['resolved_relevance_gate'] = {
            'parameter': 'resolved_relevance_gate', 'source': 'execution scores',
            'source_location': 'app/knowledge/rag.py:RAG._apply_relevance_gate',
            'source_layer': 'EXECUTION', 'configured_value': None,
            'effective_value': outcome.get('resolved_relevance_gate'),
            'precedence': 'max(absolute_gate, top_score * relative_threshold)',
            'override': None, 'status': 'EXECUTED' if outcome.get('gate_status') == 'EXECUTED' else 'NOT_VERIFIED',
            'consumer': self.consumer, 'invocation_id': self.invocation_id,
        }
        consumer_filter = data['thresholds']['consumer_post_filter']
        data['provenance']['consumer_post_filter'] = {
            'parameter': 'consumer_post_filter', 'source': 'V1 consumer constant' if self.consumer == 'V1_CHAT' else 'none',
            'source_location': consumer_filter.get('source_location', 'app/api/routes.py:chat' if self.consumer == 'V1_CHAT' else None),
            'source_layer': 'CONSUMER', 'configured_value': None,
            'effective_value': consumer_filter.get('threshold'), 'precedence': 'after canonical RAG gate',
            'override': None, 'status': consumer_filter.get('status', 'NOT_VERIFIED'),
            'consumer': self.consumer, 'invocation_id': self.invocation_id,
        }
        return data

    def with_descriptor(self, descriptor: dict[str, Any]) -> 'EffectiveRAGProfile':
        return replace(self, descriptor_json=json.dumps(descriptor, sort_keys=True, separators=(',', ':'), allow_nan=False))

    def complete(self, outcome: dict[str, Any]) -> 'EffectiveRAGProfile':
        return replace(self, outcome_json=json.dumps(outcome, sort_keys=True, allow_nan=False))


class RetrievalEvidenceList(list):
    """A list-compatible facade result carrying an internal receipt only."""
    def __init__(self, evidence, receipt=None):
        super().__init__(evidence)
        self.retrieval_receipt = receipt


class RetrievalCapture:
    def __init__(self, consumer: str, consumer_post_filter: float | None, request_top_k_source: str | None):
        self.consumer = consumer
        self.consumer_post_filter = consumer_post_filter
        self.request_top_k_source = request_top_k_source
        self.receipts: list[EffectiveRAGProfile] = []

    @property
    def canonical_gate_applied(self) -> bool:
        """Only completed canonical retrievals own relevance decisions.

        An uninstrumented adapter or a failed retrieval still uses the caller's
        conservative score floor. Receipts are internal, request-local data.
        """
        if not self.receipts:
            return False
        for receipt in self.receipts:
            outcome = json.loads(receipt.outcome_json)
            if (receipt.consumer != self.consumer or outcome.get('status') != 'COMPLETED'
                    or outcome.get('gate_status') not in {'EXECUTED', 'NOT_APPLICABLE_EMPTY'}):
                return False
        return True

    def post_filter(self, before: int, after: int) -> None:
        if not self.receipts:
            return
        receipt = self.receipts[-1]
        stage = {'threshold': None if self.canonical_gate_applied else self.consumer_post_filter,
                 'canonical_gate_applied': self.canonical_gate_applied, 'before': before, 'after': after,
                 'status': 'EXECUTED', 'source_location': 'app/api/routes.py:chat',
                 'source_layer': 'CONSUMER', 'precedence': 'after canonical RAG gate'}
        receipt = replace(receipt, consumer_filter_json=json.dumps(stage, sort_keys=True))
        self.receipts[-1] = receipt
        _log_receipt(receipt)


_retrieval_capture: ContextVar[RetrievalCapture | None] = ContextVar('rag_capture', default=None)


@contextmanager
def capture_retrieval(consumer: str, consumer_post_filter: float | None = None, *, request_top_k_source: str | None = None):
    """Reuse existing correlation context; never store a global last receipt."""
    capture = RetrievalCapture(consumer, consumer_post_filter, request_top_k_source)
    token = _retrieval_capture.set(capture)
    try:
        yield capture
    finally:
        _retrieval_capture.reset(token)


def make_rag_profile(descriptor: dict[str, Any]) -> EffectiveRAGProfile:
    capture = _retrieval_capture.get()
    consumer = capture.consumer if capture else 'DIRECT_RAG'
    stage = ({'threshold': capture.consumer_post_filter, 'status': 'NOT_EXECUTED'}
             if capture and capture.consumer_post_filter is not None else {'status': 'NOT_APPLICABLE'})
    return EffectiveRAGProfile(
        descriptor_json=json.dumps(descriptor, sort_keys=True, separators=(',', ':'), allow_nan=False),
        invocation_id=new_id('retrieval'), timestamp=datetime.now(timezone.utc).isoformat(),
        consumer=consumer, correlation_json=json.dumps(current_ids(), sort_keys=True),
        consumer_filter_json=json.dumps(stage, sort_keys=True),
        request_top_k_source=capture.request_top_k_source if capture else None)


def _log_receipt(receipt: EffectiveRAGProfile) -> None:
    snapshot = receipt.snapshot()
    log_event('effective_rag_profile', profile=snapshot)
    try:
        from app.knowledge.retrieval_evidence import persist_retrieval_receipt
        persist_retrieval_receipt(snapshot)
    except Exception as exc:
        # Do not log query text, retrieved content, or exception details.
        log_event(
            'effective_rag_profile_persistence_failed',
            invocation_id=snapshot.get('invocation_id'),
            exception_type=type(exc).__name__,
        )

def publish_rag_profile(receipt: EffectiveRAGProfile) -> None:
    capture = _retrieval_capture.get()
    if capture is not None:
        capture.receipts.append(receipt)
    _log_receipt(receipt)


class DocumentMetadata(BaseModel):
    """Metadata dokumen."""
    document_id: str = Field(..., description="ID unik dokumen")
    title: str = Field(..., description="Judul dokumen")
    source: str = Field(..., description="Sumber file/path URL")
    content_type: str = Field(default="text/plain", description="Tipe konten")
    size_bytes: int = Field(default=0, description="Ukuran file dalam bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    checksum: Optional[str] = Field(None, description="Hash checksum untuk verifikasi")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata kustom")


class TextChunk(BaseModel):
    """Satu chunk teks dari document."""
    chunk_id: str = Field(..., description="ID unik chunk")
    document_id: str = Field(..., description="ID dokumen induk")
    chunk_index: int = Field(..., description="Indeks chunk (0-based)")
    content: str = Field(..., description="Konten teks chunk")
    start_char: int = Field(..., description="Posisi karakter awal di dokumen")
    end_char: int = Field(..., description="Posisi karakter akhir di dokumen")
    tokens_estimate: int = Field(default=0, description="Estimasi jumlah token")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata chunk")


class EmbeddingResult(BaseModel):
    """Hasil embedding."""
    vector: List[float] = Field(..., description="Vector embedding")
    dimension: int = Field(..., description="Dimensi vector")
    model: str = Field(default="unknown", description="Model embedding yang digunakan")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StoredChunk(TextChunk):
    """Chunk yang sudah disimpan di vector store."""
    embedding: Optional[EmbeddingResult] = Field(None, description="Embedding jika sudah di embeddings")
    stored_at: datetime = Field(default_factory=datetime.utcnow)
    store_id: Optional[str] = Field(None, description="ID di vector store")


class Evidence(BaseModel):
    """Satuan evidence dari retrieval."""
    document_id: str = Field(..., description="ID dokumen")
    title: str = Field(default="", description="Judul dokumen")
    source: str = Field(default="", description="Sumber dokumen")
    chunk: str = Field(..., description="Konten chunk yang relevan")
    chunk_id: str = Field(..., description="ID chunk")
    chunk_index: int = Field(..., description="Indeks chunk")
    start_char: int = Field(..., description="Posisi awal")
    end_char: int = Field(..., description="Posisi akhir")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevansi score")
    store_id: Optional[str] = Field(None, description="ID di vector store")


class EvidencePack(BaseModel):
    """Pack evidence dari retrieval."""
    query: str = Field(..., description="Query asli")
    total_chunks: int = Field(..., description="Total chunk yang di-retrieve")
    total_documents: int = Field(..., description="Total dokumen unik")
    evidence: List[Evidence] = Field(default_factory=list, description="List evidence")
    reranked: bool = Field(default=False, description="Apakah sudah di-rerank")
    reranker_model: Optional[str] = Field(None, description="Model reranker jika digunakan")
    retrieval_method: str = Field(default="similarity", description="Metode retrieval")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """Hasil retrieval."""
    query: str = Field(..., description="Query")
    evidence_pack: EvidencePack = Field(..., description="Pack evidence")
    total_time_ms: int = Field(default=0, description="Waktu retrieval dalam ms")
    chunks_retrieved: int = Field(default=0, description="Jumlah chunk retrieved")
    documents_retrieved: int = Field(default=0, description="Jumlah dokumen retrieved")
    effective_profile: Optional[EffectiveRAGProfile] = Field(default=None, exclude=True)


class DocumentIngestRequest(BaseModel):
    """Request ingest document."""
    document_id: Optional[str] = Field(None, description="ID dokumen (otomatis jika None)")
    title: str = Field(..., description="Judul dokumen")
    source: str = Field(..., description="Konten teks literal; path atau URL tidak dibuka otomatis")
    content_type: str = Field(default="text/plain", description="Tipe konten: text/plain, text/markdown, application/pdf")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata tambahan")
    chunking_strategy: str = Field(default="sentence", description="Strategi chunking")
    chunk_size: int = Field(default=512, description="Ukuran chunk dalam karakter")
    chunk_overlap: int = Field(default=64, description="Overlap antar chunk")


class DocumentIngestResponse(BaseModel):
    """Response ingest document."""
    success: bool = Field(default=False, description="Apakah ingest berhasil")
    document_id: Optional[str] = Field(None, description="ID dokumen yang di-create")
    title: str = Field(default="", description="Judul dokumen")
    chunks_created: int = Field(default=0, description="Jumlah chunk yang di-create")
    chunks_stored: int = Field(default=0, description="Jumlah chunk yang tersimpan")
    total_time_ms: int = Field(default=0, description="Waktu ingest dalam ms")
    error: Optional[str] = Field(None, description="Error jika gagal")


class DocumentInfo(BaseModel):
    """Info dokumen yang tersimpan."""
    document_id: str = Field(..., description="ID dokumen")
    title: str = Field(..., description="Judul")
    source: str = Field(..., description="Sumber")
    content_type: str = Field(..., description="Tipe konten")
    chunks_count: int = Field(default=0, description="Jumlah chunk")
    size_bytes: int = Field(default=0, description="Ukuran")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentListResponse(BaseModel):
    """Response list dokumen."""
    documents: List[DocumentInfo] = Field(default_factory=list)
    total: int = Field(default=0, description="Total dokumen")
    page: int = Field(default=1)
    page_size: int = Field(default=20)


class QueryResult(BaseModel):
    """Hasil query RAG."""
    query: str = Field(..., description="Query asli")
    evidence_pack: EvidencePack = Field(..., description="Evidence yang ditemukan")
    answer: Optional[str] = Field(None, description="Answer jika sudah di-generate")
    llm_summary: Optional[str] = Field(None, description="Ringkasan dari LLM jika ada")
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_time_ms: int = Field(default=0, description="Waktu retrieval")
    total_chunks: int = Field(default=0, description="Total chunk retrieved")


class KnowledgeBaseConfig(BaseModel):
    """Konfigurasi knowledge base."""
    embedding_model: str = Field(default="indobenchmark/indobert-base-p1", description="Model embedding")
    embedding_dimension: int = Field(default=768, description="Dimensi embedding")
    vector_store_type: str = Field(default="sqlite", description="Tipe vector store: sqlite")
    chunking_strategy: str = Field(default="sentence", description="Strategi chunking")
    chunk_size: int = Field(default=512, description="Ukuran chunk karakter")
    chunk_overlap: int = Field(default=64, description="Overlap chunk")
    retrieval_top_k: int = Field(default=5, description="Jumlah top-k retrieve")
    reranker_enabled: bool = Field(default=False, description="Apakah reranker aktif")
    reranker_model: Optional[str] = Field(None, description="Model reranker")
    max_documents: int = Field(default=10000, description="Maksimal dokumen")


class KnowledgeStore(BaseModel):
    """Penyimpanan knowledge base."""
    documents: Dict[str, DocumentInfo] = Field(default_factory=dict, description="Index dokumen")
    chunks: Dict[str, StoredChunk] = Field(default_factory=dict, description="Index chunk")
    document_chunks: Dict[str, List[str]] = Field(default_factory=dict, description="Map document_id -> chunk_ids")


class Document(BaseModel):
    id: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    def chunk(self, chunk_size: int = 512, overlap: int = 64):
        from .chunker import chunk_text
        parts=chunk_text(self.content, chunk_size, overlap)
        return [TextChunk(chunk_id=f"{self.id}-{i}", document_id=self.id, chunk_index=i, content=x, start_char=0, end_char=len(x), tokens_estimate=max(1,len(x)//4), metadata=self.metadata) for i,x in enumerate(parts)]

Chunks = TextChunk
Chunk = TextChunk



