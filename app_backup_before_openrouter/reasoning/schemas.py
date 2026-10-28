"""
Reasoning Engine Schemas - Goal, assumptions, plan, evidence, actions, validation.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReasoningGoal(BaseModel):
    """Tujuan reasoning."""
    description: str = Field(..., description="Deskripsi tujuan")
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Kriteria keberhasilan"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Batasan/batasan"
    )
    priority: str = Field(
        default="normal",
        description="Prioritas: low/medium/high/critical"
    )


class ReasoningAssumption(BaseModel):
    """Asumsi dalam reasoning."""
    assumption: str = Field(..., description="Asumsi yang dibuat")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence asumsi"
    )
    source: str = Field(
        default="inferred",
        description="Sumber asumsi: inferred, provided, observed"
    )
    notes: Optional[str] = Field(None, description="Catatan tambahan")


class ReasoningPlan(BaseModel):
    """Rencana eksekusi."""
    plan_id: str = Field(..., description="ID rencana")
    description: str = Field(..., description="Deskripsi rencana")
    steps: List["PlanStep"] = Field(
        default_factory=list,
        description="Langkah-langkah dalam rencana"
    )
    total_steps: int = Field(..., description="Jumlah total langkah")
    estimated_effort: str = Field(
        default="medium",
        description="Estimasi effort: low/medium/high"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Prasyarat sebelum eksekusi"
    )


class PlanStep(BaseModel):
    """Satu langkah dalam rencana."""
    step_id: str = Field(..., description="ID langkah")
    step_number: int = Field(..., description="Nomor urut langkah")
    description: str = Field(..., description="Deskripsi langkah")
    action_type: str = Field(
        default="action",
        description="Tipe aksi: action, tool, retrieve, verify, human"
    )
    expected_output: Optional[str] = Field(
        None,
        description="Output yang diharapkan"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Langkah yang harus selesai sebelumnya"
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Kriteria sukses untuk langkah ini"
    )
    error_handling: Optional[str] = Field(
        None,
        description="Strategi penanganan error"
    )


class ReasoningEvidence(BaseModel):
    """Evidence yang dikumpulkan."""
    source: str = Field(..., description="Sumber evidence")
    document_id: Optional[str] = Field(None, description="ID dokumen jika dari knowledge")
    title: Optional[str] = Field(None, description="Judul sumber")
    content: str = Field(..., description="Konten evidence")
    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Skor relevansi"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence evidence"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata tambahan"
    )


class ReasoningAction(BaseModel):
    """Aksi yang dijalankan."""
    action_id: str = Field(..., description="ID aksi")
    description: str = Field(..., description="Deskripsi aksi")
    action_type: str = Field(
        default="action",
        description="Tipe: tool, api, manual, automated"
    )
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input untuk aksi"
    )
    result: Optional[Dict[str, Any]] = Field(
        None,
        description="Hasil aksi jika sudah dijalankan"
    )
    success: Optional[bool] = Field(
        None,
        description="Apakah aksi berhasil"
    )
    error: Optional[str] = Field(
        None,
        description="Error jika gagal"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Waktu eksekusi"
    )


class ValidationResult(BaseModel):
    """Hasil validasi."""
    validated: bool = Field(..., description="Apakah validasi berhasil")
    issues: List[str] = Field(
        default_factory=list,
        description="List issue jika tidak valid"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence hasil validasi"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detail validasi"
    )


class ReasoningArtifact(BaseModel):
    """Artefak reasoning yang disimpan."""
    artifact_id: str = Field(..., description="ID artefak")
    goal: ReasoningGoal = Field(..., description="Tujuan")
    assumptions: List[ReasoningAssumption] = Field(
        default_factory=list,
        description="Asumsi yang dibuat"
    )
    plan: ReasoningPlan = Field(..., description="Rencana eksekusi")
    evidence: List[ReasoningEvidence] = Field(
        default_factory=list,
        description="Evidence yang dikumpulkan"
    )
    actions: List[ReasoningAction] = Field(
        default_factory=list,
        description="Aksi yang dijalankan"
    )
    validation: Optional[ValidationResult] = Field(
        None,
        description="Hasil validasi akhir"
    )
    status: str = Field(
        default="in_progress",
        description="Status: in_progress, completed, failed, paused"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Waktu pembuatan"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Waktu update terakhir"
    )
    completed_at: Optional[datetime] = Field(None, description="Waktu selesai")


class ReasoningRequest(BaseModel):
    """Request untuk reasoning engine."""
    problem_description: str = Field(
        ...,
        description="Deskripsi masalah"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Context tambahan"
    )
    goal: Optional[ReasoningGoal] = Field(
        None,
        description="Tujuan spesifik"
    )
    evidence: Optional[List[ReasoningEvidence]] = Field(
        None,
        description="Evidence awal jika ada"
    )
    constraints: Optional[List[str]] = Field(
        None,
        description="Batasan khusus"
    )
    max_steps: int = Field(
        default=20,
        description="Maksimal langkah"
    )
    requires_human_approval: bool = Field(
        default=False,
        description="Apakah butuh approval manusia"
    )


class ReasoningResponse(BaseModel):
    """Response dari reasoning engine."""
    request_id: str = Field(..., description="ID request")
    artifact_id: str = Field(..., description="ID artefak")
    goal: ReasoningGoal = Field(..., description="Tujuan")
    assumptions: List[ReasoningAssumption] = Field(
        default_factory=list,
        description="Asumsi"
    )
    plan: ReasoningPlan = Field(..., description="Rencana")
    evidence_summary: str = Field(
        default="",
        description="Ringkasan evidence"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Info yang masih kurang"
    )
    needs_clarification: bool = Field(
        default=False,
        description="Apakah perlu klarifikasi"
    )
    requires_human_approval: bool = Field(
        default=False,
        description="Apakah butuh approval manusia"
    )
    clarification_questions: List[str] = Field(
        default_factory=list,
        description="Pertanyaan klarifikasi"
    )
    status: str = Field(
        default="in_progress",
        description="Status: in_progress, completed, needs_clarification"
    )

ReasoningResult = ReasoningResponse
Plan = ReasoningPlan


# Compatibility view used by earlier tests.
ReasoningResponse.evaluation_result = property(lambda self: {"status": self.status, "needs_clarification": self.needs_clarification})

ReasoningResponse.requires_human = property(lambda self: self.requires_human_approval)
