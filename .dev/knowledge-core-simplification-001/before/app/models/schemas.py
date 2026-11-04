"""
Schemas untuk LLM Provider.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request untuk generate teks."""
    prompt: str = Field(..., description="Prompt/teks input")
    max_tokens: int = Field(default=1024, ge=1, le=16384, description="Maksimal token output")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature untuk sampling")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Nucleus sampling")
    top_k: Optional[int] = Field(default=None, ge=1, description="Top-k sampling")
    repetition_penalty: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Repetition penalty")
    stop: List[str] = Field(default_factory=list, description="Token penghenti")
    system_prompt: Optional[str] = Field(default=None, description="System prompt (optional)")
    stream: bool = Field(default=False, description="Apakah streaming")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tambahan")


class GenerateResponse(BaseModel):
    """Response dari generate."""
    text: str = Field(..., description="Output teks")
    model: str = Field(..., description="Nama model yang digunakan")
    provider: str = Field(..., description="Nama provider")
    usage: Dict[str, int] = Field(default_factory=dict, description="Usage: prompt_tokens, completion_tokens, total_tokens")
    latency_ms: int = Field(default=0, description="Latensi dalam milidetik")
    finish_reason: Literal["stop", "length", "error", "cancel"] = Field(default="stop", description="Alasan selesai")


class StructuredOutput(BaseModel):
    """Output terstruktur (generic)."""
    data: Dict[str, Any] = Field(default_factory=dict, description="Data terstruktur")
    model: str = Field(default="unknown", description="Model yang digunakan")
    provider: str = Field(default="unknown", description="Provider")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence output (bukan kepastian fakta)")


class HealthStatus(BaseModel):
    """Status kesehatan provider."""
    status: Literal["healthy", "unhealthy", "unknown"] = Field(..., description="Status kesehatan")
    provider: str = Field(..., description="Nama provider")
    model: str = Field(default="unknown", description="Model")
    latency_ms: int = Field(default=0, description="Latensi health check")
    is_mock: bool = Field(default=False, description="Apakah mock provider")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detail tambahan")


class ProviderConfig(BaseModel):
    """Konfigurasi provider."""
    name: str = Field(..., description="Nama provider")
    base_url: str = Field(default="", description="Base URL API")
    api_key: Optional[str] = Field(default=None, description="API Key (jika ada)")
    model: str = Field(default="default", description="Model default")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Timeout permintaan")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maksimal retry")
    is_local: bool = Field(default=False, description="Apakah local provider")
    is_mock: bool = Field(default=False, description="Apakah mock provider")


def create_default_provider_config(name: str, is_local: bool = True) -> ProviderConfig:
    """Buat konfigurasi provider default."""
    return ProviderConfig(
        name=name,
        base_url="http://localhost:11434" if is_local else "https://api.openai.com/v1",
        model="llama3.2:1b" if is_local else "gpt-4o-mini",
        is_local=is_local,
        is_mock=False,
    )


# Compatibility request type used by provider tests.
StructuredGenerateRequest = GenerateRequest

StructuredGenerateResponse = StructuredOutput

HealthCheckResponse = HealthStatus

class ModelSelection:
    def __init__(self, provider, model_name='unknown', reason=''): self.provider=provider; self.model_name=model_name; self.reason=reason
