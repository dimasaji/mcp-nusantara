"""
Context Engine Schemas.
Model context: session, history, intent, entities, goal, facts, missing info.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, computed_field


class ContextMetadata(BaseModel):
    """Metadata konteks."""
    session_id: str = Field(..., description="ID unik session")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Waktu pembuatan session")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Waktu update terbaru")
    version: int = Field(default=1, description="Versi context (increment setiap update)")
    source: str = Field(default="user", description="Sumber context (user, system, external)")
    tags: List[str] = Field(default_factory=list, description="Tag untuk kategorisasi")


class HistoryEntry(BaseModel):
    """Satu entri history percakapan."""
    turn_id: int = Field(..., description="ID urutan percakapan")
    role: str = Field(..., description="Role: user, assistant, system")
    content: str = Field(..., description="Konten pesan")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Waktu pesan")
    language: Optional[str] = Field(None, description="Bahasa pesan")
    intent: Optional[str] = Field(None, description="Intent yang terdeteksi")
    entities: Dict[str, List[str]] = Field(default_factory=dict, description="Entity yang diekstrak")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tambahan")

    class Config:
        json_schema_extra = {
            "example": {
                "turn_id": 1,
                "role": "user",
                "content": "KTP saya belum jadi",
                "timestamp": "2024-01-15T10:30:00Z",
                "language": "id",
                "intent": "document_status",
                "entities": {"document": ["KTP"]},
            }
        }


class ContextState(BaseModel):
    """State konteks percakapan."""
    session_id: str = Field(..., description="ID session")
    user_input: str = Field(default="", description="Input saat ini")
    history: List[HistoryEntry] = Field(default_factory=list, description="Riwayat percakapan")
    current_intent: Optional[str] = Field(None, description="Intent saat ini")
    entities: Dict[str, List[str]] = Field(default_factory=dict, description="Entity yang dikumpulkan")
    previous_problem: Optional[str] = Field(None, description="Masalah sebelumnya (jika ada)")
    current_goal: Optional[str] = Field(None, description="Tujuan saat ini")
    known_facts: Dict[str, Any] = Field(default_factory=dict, description="Fakta yang sudah diketahui")
    missing_information: List[str] = Field(default_factory=list, description="Info yang masih kurang")
    metadata: ContextMetadata = Field(default_factory=ContextMetadata, description="Metadata session")
    context_window_size: int = Field(default=10, description="Jumlah history terbaru yang dipertahankan")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Waktu pembuatan")

    @computed_field
    @property
    def total_turns(self) -> int:
        """Total jumlah turn dalam history."""
        return len(self.history)

    @computed_field
    @property
    def last_turn(self) -> Optional[HistoryEntry]:
        """Turn terakhir."""
        if self.history:
            return self.history[-1]
        return None


class ContextUpdate(BaseModel):
    """Update yang bisa diterapkan ke context."""
    session_id: Optional[str] = None
    history_add: Optional[HistoryEntry] = None
    current_intent: Optional[str] = None
    entities_update: Optional[Dict[str, List[str]]] = None
    previous_problem: Optional[str] = None
    current_goal: Optional[str] = None
    known_facts_update: Optional[Dict[str, Any]] = None
    missing_information_add: Optional[List[str]] = None
    metadata_update: Optional[ContextMetadata] = None
    prune_history: Optional[bool] = None  # Prune ke context_window_size
    clear_history: Optional[bool] = None


class MissingInformationRequest(BaseModel):
    """Request untuk cek missing information."""
    context: ContextState
    required_fields: List[str] = Field(..., description="Field yang dibutuhkan untuk menyelesaikan task")


class MissingInformationResponse(BaseModel):
    """Response missing information."""
    is_complete: bool = Field(..., description="Apakah context sudah lengkap")
    missing_fields: List[str] = Field(default_factory=list, description="Field yang masih kurang")
    suggestions: List[str] = Field(default_factory=list, description="Saran untuk melengkapi")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence kelengkapan")


class ContextWindowConfig(BaseModel):
    """Konfigurasi context window."""
    max_turns: int = Field(default=10, ge=1, le=100, description="Jumlah turn maksimal")
    max_total_tokens: Optional[int] = Field(None, ge=1, description="Maksimal token total")
    prune_older_than_turns: int = Field(default=10, description="Prune history di atas ini")
    deduplicate: bool = Field(default=True, description="Deduplikasi history")
    preserve_recent: bool = Field(default=True, description="Pertahankan history terbaru")
    privacy_filter: bool = Field(default=True, description="Filter data sensitif")


class SessionIsolationConfig(BaseModel):
    """Konfigurasi isolasi session."""
    enabled: bool = Field(default=True, description="Aktifkan isolasi session")
    max_concurrent_sessions: int = Field(default=100, ge=1, le=1000, description="Maksimal session aktif")
    auto_create_session: bool = Field(default=True, description="Buat session otomatis untuk user baru")
    session_timeout_minutes: int = Field(default=30, ge=0, le=1440, description="Timeout session (0=tidak ada)")
    cross_session_sharing: bool = Field(default=False, description="Bagikan context antar session")

Context = ContextState
ContextWindow = ContextWindowConfig
