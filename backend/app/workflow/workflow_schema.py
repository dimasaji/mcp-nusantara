"""
Workflow Engine Schemas - Definition dan state machine.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class WorkflowState(str):
    """State enum untuk workflow."""
    START = "START"
    IDENTIFY_PROBLEM = "IDENTIFY_PROBLEM"
    COLLECT_INFORMATION = "COLLECT_INFORMATION"
    RETRIEVE_KNOWLEDGE = "RETRIEVE_KNOWLEDGE"
    VALIDATE = "VALIDATE"
    ACTION = "ACTION"
    VERIFY = "VERIFY"
    COMPLETE = "COMPLETE"
    NEED_HUMAN = "NEED_HUMAN"
    FAILED = "FAILED"


class WorkflowDefinition(BaseModel):
    """Definisi workflow - blueprint dari state machine."""
    workflow_id: str = Field(..., description="ID unik workflow")
    name: str = Field(..., description="Nama workflow")
    description: str = Field(default="", description="Deskripsi workflow")
    version: int = Field(default=1, description="Versi definisi")
    states: List[str] = Field(..., description="Semua state yang dimiliki workflow")
    initial_state: str = Field(default=WorkflowState.START, description="State awal")
    terminal_states: List[str] = Field(
        default_factory=lambda: [WorkflowState.COMPLETE, WorkflowState.NEED_HUMAN, WorkflowState.FAILED],
        description="State terminal (akhir)"
    )
    transitions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Map state -> list state tujuan yang valid"
    )
    allowed_actions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Map state -> list action yang diizinkan"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tambahan")

    @field_validator("transitions")
    @classmethod
    def validate_transitions(cls, v: Dict[str, List[str]], info) -> Dict[str, List[str]]:
        """Validasi transisi: pastikan semua state dalam transitions ada di states."""
        states = info.data.get("states", [])
        for from_state, to_states in v.items():
            if from_state not in states:
                raise ValueError(f"State '{from_state}' tidak ada dalam states")
            for to_state in to_states:
                if to_state not in states:
                    raise ValueError(f"State '{to_state}' tidak ada dalam states")
        return v


class WorkflowSession(BaseModel):
    """Instance workflow yang sedang berjalan."""
    session_id: str = Field(..., description="ID unik session workflow")
    workflow_id: str = Field(..., description="ID workflow definition")
    current_state: str = Field(default=WorkflowState.START, description="State saat ini")
    state_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Riwayat perubahan state"
    )
    context: Dict[str, Any] = Field(default_factory=dict, description="Context workflow")
    data: Dict[str, Any] = Field(default_factory=dict, description="Data yang dikumpulkan")
    errors: List[str] = Field(default_factory=list, description="Error yang terjadi")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Waktu mulai")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Waktu update terakhir")
    is_paused: bool = Field(default=False, description="Apakah paused")
    pause_time: Optional[datetime] = Field(None, description="Waktu pause jika ada")
    human_handoff: Optional[Dict[str, Any]] = Field(
        None,
        description="Info handoff ke manusia jika ada"
    )

    def transition_to(self, new_state: str, action: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Record transisi ke state baru."""
        entry = {
            "from_state": self.current_state,
            "to_state": new_state,
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "metadata": kwargs,
        }
        self.state_history.append(entry)
        self.current_state = new_state
        self.last_updated = datetime.utcnow()
        return entry


class WorkflowTransition(BaseModel):
    """Transisi antara state."""
    from_state: str = Field(..., description="State asal")
    to_state: str = Field(..., description="State tujuan")
    action: Optional[str] = Field(None, description="Action yang memicu transisi")
    condition: Optional[str] = Field(None, description="Kondisi transisi (opsional)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    """Hasil akhir workflow."""
    session_id: str = Field(..., description="ID session")
    workflow_id: str = Field(..., description="ID workflow")
    final_state: str = Field(..., description="State akhir")
    success: bool = Field(..., description="Apakah workflow sukses")
    output: Dict[str, Any] = Field(default_factory=dict, description="Output workflow")
    duration_seconds: float = Field(default=0.0, description="Durasi eksekusi")
    steps_count: int = Field(default=0, description="Jumlah step yang dijalankan")
    errors: List[str] = Field(default_factory=list, description="Error yang terjadi")
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowResumeRequest(BaseModel):
    """Request untuk resume workflow yang paused."""
    session_id: str = Field(..., description="ID session yang di-resume")
    context_updates: Optional[Dict[str, Any]] = Field(
        None,
        description="Update context saat resume"
    )
    data_updates: Optional[Dict[str, Any]] = Field(
        None,
        description="Update data saat resume"
    )


class WorkflowValidation(BaseModel):
    """Validasi workflow."""
    is_valid: bool = Field(..., description="Apakah workflow valid")
    issues: List[str] = Field(default_factory=list, description="List issue jika tidak valid")
    terminal_reachable: bool = Field(default=True, description="Apakah semua state bisa mencapai terminal")


class PersistenceConfig(BaseModel):
    """Konfigurasi persistence."""
    enabled: bool = Field(default=False, description="Aktifkan persistence")
    backend: str = Field(default="memory", description="Backend: memory, redis, postgres")
    key_prefix: str = Field(default="workflow:", description="Prefix key")
