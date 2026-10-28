"""
Base LLMProvider abstraction.
Semua provider harus inherit dari class ini.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, NotRequired, Optional, TypedDict


class GenerateRequest(TypedDict, total=False):
    """Request untuk generate."""
    prompt: str
    system: Optional[str]
    max_tokens: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]
    stream: Optional[bool]


class GenerateResponse(TypedDict):
    """Response dari generate."""
    content: str
    model: str
    tokens_used: int
    latency_ms: int
    execution_identity: NotRequired[Dict[str, Any]]


class StructuredGenerateRequest(TypedDict, total=False):
    """Request untuk generate terstruktur."""
    prompt: str
    system: Optional[str]
    schema: Dict[str, Any]
    max_tokens: Optional[int]
    temperature: Optional[float]


class StructuredGenerateResponse(TypedDict):
    """Response dari generate terstruktur."""
    content: Dict[str, Any]
    model: str
    tokens_used: int
    latency_ms: int
    execution_identity: NotRequired[Dict[str, Any]]


class HealthCheckResponse(TypedDict):
    """Response dari health check."""
    status: str
    model: str
    available: bool
    latency_ms: int


class LLMProvider(ABC):
    """
    Abstract base class untuk semua LLM Provider.
    
    Setiap provider harus implementasi:
    - generate(): Generate teks biasa
    - generate_structured(): Generate dengan output terstruktur (JSON/schema)
    - health_check(): Cek koneksi & ketersediaan model
    """

    provider_name: str = "base"
    model_name: str = "unknown"

    @property
    def name(self) -> str:
        return self.provider_name

    @property
    def model(self) -> str:
        return self.model_name

    @abstractmethod
    async def generate(
        self,
        request: GenerateRequest,
    ) -> GenerateResponse:
        """
        Generate teks dari prompt.
        
        Args:
            request: GenerateRequest berisi prompt dan parameter
            
        Returns:
            GenerateResponse berisi hasil generate
        """
        ...

    @abstractmethod
    async def generate_structured(
        self,
        request: StructuredGenerateRequest,
    ) -> StructuredGenerateResponse:
        """
        Generate teks dengan output terstruktur sesuai schema.
        
        Args:
            request: StructuredGenerateRequest berisi prompt, schema, dan parameter
            
        Returns:
            StructuredGenerateResponse berisi hasil generate terstruktur
        """
        ...

    @abstractmethod
    async def health_check(self) -> HealthCheckResponse:
        """
        Cek kesehatan provider dan ketersediaan model.
        
        Returns:
            HealthCheckResponse berisi status kesehatan
        """
        ...

    async def generate_stream(
        self,
        request: GenerateRequest,
    ) -> List[str]:
        """
        Generate dengan streaming (optional).
        Default implementasi membagi menjadi chunk.
        """
        response = await self.generate(request)
        # Split content menjadi chunk untuk streaming
        chunk_size = max(1, len(response["content"]) // 10)
        return [
            response["content"][i : i + chunk_size]
            for i in range(0, len(response["content"]), chunk_size)
        ]

    def get_model_info(self) -> Dict[str, Any]:
        """Return informasi model."""
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "supported_tasks": ["text_generation", "chat", "code"],
            "max_context": 128000,
            "supports_structured": True,
        }


__all__ = [
    "LLMProvider",
    "GenerateRequest",
    "GenerateResponse",
    "StructuredGenerateRequest",
    "StructuredGenerateResponse",
    "HealthCheckResponse",
]
