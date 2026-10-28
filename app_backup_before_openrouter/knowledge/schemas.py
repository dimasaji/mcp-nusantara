"""
Knowledge & RAG Engine Schemas.
Evidence dari document, chunking, embedding, retrieval, reranking.
"""
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


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


class DocumentIngestRequest(BaseModel):
    """Request ingest document."""
    document_id: Optional[str] = Field(None, description="ID dokumen (otomatis jika None)")
    title: str = Field(..., description="Judul dokumen")
    source: str = Field(..., description="Path file atau URL")
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
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Model embedding")
    embedding_dimension: int = Field(default=384, description="Dimensi embedding")
    vector_store_type: str = Field(default="chroma", description="Tipe vector store: chroma, qdrant, memori")
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
