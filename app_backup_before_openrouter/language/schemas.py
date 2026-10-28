"""
Schemas untuk Language Engine.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NormalizationResult(BaseModel):
    """Hasil normalisasi teks."""
    original: str = Field(..., description="Teks asli")
    normalized: str = Field(..., description="Teks setelah normalisasi")
    changes: List[str] = Field(default_factory=list, description="Daftar perubahan yang dilakukan")


class LanguageDetectionResult(BaseModel):
    """Hasil deteksi bahasa."""
    language: str = Field(..., description="Kode bahasa (id, en, dll)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence deteksi")
    is_mixed: bool = Field(default=False, description="Apakah teks mengandung campuran bahasa")
    languages: Dict[str, float] = Field(default_factory=dict, description="Distribusi bahasa")


class IntentResult(BaseModel):
    """Hasil deteksi intent."""
    intent: str = Field(..., description="Nama intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence intent")
    category: Optional[str] = Field(None, description="Kategori intent")
    parent_intent: Optional[str] = Field(None, description="Intent induk jika ada")


class EntityResult(BaseModel):
    entities: Any = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    raw_matches: List[Dict[str, Any]] = Field(default_factory=list)
    doc_id: Optional[str] = None
    text: str = ""


class StructuredUnderstanding(BaseModel):
    """Pemahaman terstruktur dari input."""
    text: str = Field(..., description="Teks asli (setelah normalisasi)")
    language: LanguageDetectionResult
    intent: IntentResult
    entities: EntityResult
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tambahan")


class NLPSegment(BaseModel):
    """Segmen teks untuk analisis."""
    text: str
    start: int
    end: int
    language: Optional[str] = None


class PipelineConfig(BaseModel):
    """Konfigurasi pipeline."""
    normalize: bool = True
    detect_language: bool = True
    detect_intent: bool = True
    extract_entities: bool = True
    strict: bool = False  # Strict mode: raise error jika component gagal


class PipelineResult(BaseModel):
    """Hasil akhir pipeline."""
    input: str
    output: StructuredUnderstanding
    steps: List[str] = Field(default_factory=list, description="Langkah pipeline yang dijalankan")
    duration_ms: int = Field(default=0, description="Durasi pipeline dalam ms")


NormalizeResult = NormalizationResult

from enum import Enum
class EntityType(str, Enum):
    NIK='nik'; DOCUMENT='document'; NAME='name'; DATE='date'; PHONE='phone'; LOCATION='location'; UNKNOWN='unknown'; NUMBER='number'; PERSON='person'; ORGANIZATION='organization'; EMAIL='email'; ID='id'
