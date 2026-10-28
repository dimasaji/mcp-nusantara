"""
Problem Engine Schemas.
Human story → Situation → Problem → Goal → Constraints → Missing Info → Possible Solution.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Situation(BaseModel):
    """Situasi/conteks masalah."""
    description: str = Field(..., description="Deskripsi situasi")
    context: Dict[str, Any] = Field(default_factory=dict, description="Konteks tambahan")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProblemStatement(BaseModel):
    """Pernyataan masalah."""
    raw_input: str = Field(..., description="Input mentah dari user")
    cleaned_input: str = Field(..., description="Input setelah dibersihkan")
    problem_type: str = Field(..., description="Tipe masalah (document, technical, process, dll)")
    description: str = Field(..., description="Deskripsi masalah yang diidentifikasi")
    urgency: str = Field(default="medium", description="Tingkat urgensi: low/medium/high/critical")
    language: str = Field(default="id", description="Bahasa input")


class Goal(BaseModel):
    """Tujuan yang ingin dicapai."""
    description: str = Field(..., description="Deskripsi tujuan")
    outcome: Optional[str] = Field(None, description="Outcome yang diharapkan")
    constraints: List[str] = Field(default_factory=list, description="Batuan/constraints")
    success_criteria: List[str] = Field(default_factory=list, description="Kriteria keberhasilan")


class MissingInfo(BaseModel):
    """Informasi yang masih kurang."""
    field: str = Field(..., description="Nama field/info yang kurang")
    reason: str = Field(..., description="Alasan mengapa info ini diperlukan")
    suggestion: Optional[str] = Field(None, description="Saran cara melengkapi")
    critical: bool = Field(default=False, description="Apakah info ini kritis")


class ClarificationRequest(BaseModel):
    """Request untuk klarifikasi."""
    needs_clarification: bool = Field(default=False, description="Apakah perlu klarifikasi")
    missing_fields: List[MissingInfo] = Field(default_factory=list, description="Daftar info yang kurang")
    questions: List[str] = Field(default_factory=list, description="Pertanyaan klarifikasi")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence pemahaman")


class RiskAssessment(BaseModel):
    """Domain dan tingkat risiko."""
    domain: str = Field(..., description="Domain masalah")
    risk_level: str = Field(default="low", description="Tingkat risiko: low/medium/high/critical")
    risk_factors: List[str] = Field(default_factory=list, description="Faktor risiko")
    requires_human_approval: bool = Field(default=False, description="Apakah butuh persetujuan manusia")


class PossibleSolution(BaseModel):
    """Solusi yang mungkin."""
    approach: str = Field(..., description="Pendekatan solusi")
    steps: List[str] = Field(default_factory=list, description="Langkah-langkah")
    pros: List[str] = Field(default_factory=list, description="Kelebihan")
    cons: List[str] = Field(default_factory=list, description="Kekurangan")
    estimated_effort: str = Field(default="medium", description="Estimasi effort: low/medium/high")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence solusi")
    requires_clarification_before: bool = Field(default=False, description="Butuh klarifikasi sebelum eksekusi")


class SolutionEvaluation(BaseModel):
    """Evaluasi solusi."""
    approach_used: str = Field(..., description="Pendekatan yang digunakan")
    success: bool = Field(default=False, description="Apakah berhasil")
    result: Optional[str] = Field(None, description="Hasil")
    validation_details: Optional[Dict[str, Any]] = Field(None, description="Detail validasi")
    failures: List[str] = Field(default_factory=list, description="Gagal yang terjadi")
    lessons_learned: List[str] = Field(default_factory=list, description="Pelajaran yang dipetik")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence evaluasi")


class ProblemResolution(BaseModel):
    """Resolusi masalah lengkap."""
    problem_id: str = Field(..., description="ID masalah")
    original_input: str = Field(..., description="Input asli")
    language: str = Field(default="id")
    problem: ProblemStatement
    goal: Goal
    constraints_applied: List[str] = Field(default_factory=list, description="Constraints yang diterapkan")
    risk: RiskAssessment
    missing_info: List[MissingInfo] = Field(default_factory=list)
    clarification_request: Optional[ClarificationRequest] = None
    possible_solutions: List[PossibleSolution] = Field(default_factory=list)
    selected_solution: Optional[PossibleSolution] = None
    evaluation: Optional[SolutionEvaluation] = None
    resolution_status: str = Field(default="in_progress", description="Status: in_progress/solved/failed/deferred")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProblemSchema(BaseModel):
    """Schema utama untuk Problem Engine."""
    raw_input: str = Field(..., description="Input mentah dari user")
    language: str = Field(default="id", description="Bahasa input")
    detected_intent: Optional[str] = Field(None, description="Intent yang terdeteksi (dari language engine)")
    entities: Dict[str, List[str]] = Field(default_factory=dict, description="Entity yang diekstrak")
    classifications: List[Dict[str, Any]] = Field(default_factory=list, description="Hasil klasifikasi")
    resolution: Optional[ProblemResolution] = Field(None, description="Resolusi lengkap")
