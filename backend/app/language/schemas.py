
"""
Canonical schemas untuk Nusantara Language Engine.

File ini adalah single source of truth untuk kontrak data NLP:
- Normalization
- Language Detection
- Intent Classification
- Entity Extraction
- Structured Understanding
- Pipeline Result

Prinsip:
1. Pydantic sebagai kontrak data.
2. Backward compatible dengan komponen lama.
3. Tidak mengandung business logic.
4. Siap dikembangkan untuk IndoBERT, RAG, Hermes, dan Ollama.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# ENUMS
# ============================================================


class EntityType(str, Enum):
    """Tipe entity yang dikenali Language Engine."""

    NIK = "nik"
    DOCUMENT = "document"
    NAME = "name"
    DATE = "date"
    PHONE = "phone"
    LOCATION = "location"
    UNKNOWN = "unknown"
    NUMBER = "number"
    PERSON = "person"
    ORGANIZATION = "organization"
    EMAIL = "email"
    ID = "id"


# ============================================================
# NORMALIZATION
# ============================================================


class NormalizationResult(BaseModel):
    """Hasil normalisasi teks."""

    original: str = Field(
        ...,
        description="Teks asli sebelum normalisasi",
    )

    normalized: str = Field(
        ...,
        description="Teks setelah normalisasi",
    )

    changes: List[str] = Field(
        default_factory=list,
        description="Daftar perubahan yang dilakukan",
    )


# Backward compatibility:
# normalizer.py sebelumnya menggunakan nama NormalizeResult.
NormalizeResult = NormalizationResult


# ============================================================
# LANGUAGE DETECTION
# ============================================================


class LanguageDetectionResult(BaseModel):
    """Hasil deteksi bahasa."""

    language: str = Field(
        ...,
        description="Kode bahasa utama, contoh: id, en",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence deteksi bahasa",
    )

    is_mixed: bool = Field(
        default=False,
        description="Apakah teks mengandung campuran bahasa",
    )

    languages: Dict[str, float] = Field(
        default_factory=dict,
        description="Distribusi confidence bahasa",
    )


# ============================================================
# INTENT
# ============================================================


class IntentResult(BaseModel):
    """
    Hasil klasifikasi intent.

    Ini adalah CONTRACT CANONICAL yang digunakan seluruh
    Language Engine.

    Jangan membuat IntentResult kedua di intent.py.
    """

    intent: str = Field(
        ...,
        description="Nama intent utama",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence klasifikasi intent",
    )

    category: Optional[str] = Field(
        default=None,
        description="Kategori intent",
    )

    parent_intent: Optional[str] = Field(
        default=None,
        description="Intent induk jika tersedia",
    )


# ============================================================
# ENTITY
# ============================================================


class Entity(BaseModel):
    """
    Satu entity hasil ekstraksi.

    Contoh:
        {
            "text": "KTP",
            "type": "document",
            "start": 20,
            "end": 23,
            "confidence": 0.98
        }
    """

    text: str = Field(
        ...,
        description="Teks entity yang ditemukan",
    )

    type: EntityType = Field(
        default=EntityType.UNKNOWN,
        description="Jenis entity",
    )

    start: Optional[int] = Field(
        default=None,
        ge=0,
        description="Posisi awal entity",
    )

    end: Optional[int] = Field(
        default=None,
        ge=0,
        description="Posisi akhir entity",
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence entity",
    )


class EntityResult(BaseModel):
    """Hasil ekstraksi entity."""

    entities: Any = Field(
        default_factory=list,
        description="Daftar entity hasil ekstraksi",
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence keseluruhan entity extraction",
    )

    raw_matches: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Hasil pencocokan mentah dari extractor",
    )

    doc_id: Optional[str] = Field(
        default=None,
        description="ID dokumen jika terkait dokumen tertentu",
    )

    text: str = Field(
        default="",
        description="Teks yang dianalisis",
    )


# ============================================================
# STRUCTURED UNDERSTANDING
# ============================================================


class StructuredUnderstanding(BaseModel):
    """
    Hasil pemahaman terstruktur dari Language Engine.

    Ini menjadi output utama NLP sebelum diteruskan ke
    Hermes / RAG / Tool / Workflow.
    """

    text: str = Field(
        ...,
        description="Teks setelah normalisasi",
    )

    language: LanguageDetectionResult = Field(
        ...,
        description="Hasil deteksi bahasa",
    )

    intent: IntentResult = Field(
        ...,
        description="Hasil klasifikasi intent",
    )

    entities: EntityResult = Field(
        ...,
        description="Hasil ekstraksi entity",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata tambahan pipeline",
    )


# ============================================================
# NLP SEGMENT
# ============================================================


class NLPSegment(BaseModel):
    """Segmen teks untuk analisis NLP."""

    text: str = Field(
        ...,
        description="Isi segmen",
    )

    start: int = Field(
        ...,
        ge=0,
        description="Posisi awal segmen",
    )

    end: int = Field(
        ...,
        ge=0,
        description="Posisi akhir segmen",
    )

    language: Optional[str] = Field(
        default=None,
        description="Bahasa segmen",
    )


# ============================================================
# PIPELINE CONFIGURATION
# ============================================================


class PipelineConfig(BaseModel):
    """Konfigurasi Language Engine pipeline."""

    normalize: bool = Field(
        default=True,
        description="Aktifkan normalisasi",
    )

    detect_language: bool = Field(
        default=True,
        description="Aktifkan language detection",
    )

    detect_intent: bool = Field(
        default=True,
        description="Aktifkan intent classification",
    )

    extract_entities: bool = Field(
        default=True,
        description="Aktifkan entity extraction",
    )

    strict: bool = Field(
        default=False,
        description=(
            "Jika True, exception component diteruskan. "
            "Jika False, pipeline menggunakan fallback."
        ),
    )


# ============================================================
# PIPELINE RESULT
# ============================================================


class PipelineResult(BaseModel):
    """Hasil akhir Language Engine."""

    input: str = Field(
        ...,
        description="Input asli user",
    )

    output: StructuredUnderstanding = Field(
        ...,
        description="Structured understanding",
    )

    steps: List[str] = Field(
        default_factory=list,
        description="Langkah pipeline yang dijalankan",
    )

    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Durasi pipeline dalam milidetik",
    )


# ============================================================
# EXPORT CONTRACT
# ============================================================


__all__ = [
    "EntityType",
    "NormalizationResult",
    "NormalizeResult",
    "LanguageDetectionResult",
    "IntentResult",
    "Entity",
    "EntityResult",
    "StructuredUnderstanding",
    "NLPSegment",
    "PipelineConfig",
    "PipelineResult",
]

