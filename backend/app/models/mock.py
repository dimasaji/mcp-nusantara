"""
Mock LLM Provider - Provider palsu untuk testing.
Tidak bergantung pada model nyata. Wajib untuk test.
"""
from typing import Any, Dict, List, Optional
from app.models.base import LLMProvider, GenerateRequest, GenerateResponse
from app.models.schemas import GenerateResponse as PublicGenerateResponse


class MockProvider(LLMProvider):
    provider_name = "mock"
    model_name = "mock-model"
    """
    Mock LLM provider untuk testing.
    Menghasilkan respons palsu yang dapat dikontrol.
    """

    def __init__(
        self,
        mock_response: str = "Ini adalah respons mock dari MockProvider.",
        mock_structured: Optional[Dict[str, Any]] = None,
        mock_health: bool = True,
        delay: float = 0.0,
    ):
        self._mock_response = mock_response
        self._mock_structured = mock_structured or {"result": "mock result"}
        self._mock_health = mock_health
        self._delay = delay
        self._call_count = 0
        self._last_request: Optional[GenerateRequest] = None

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate respons palsu."""
        import time
        if self._delay > 0:
            time.sleep(self._delay)

        self._call_count += 1
        self._last_request = request

        return PublicGenerateResponse(
            text=(f"Mock response: {request.get('prompt', '')}" if self._mock_response.startswith("Ini adalah respons mock") else self._mock_response),
            model="mock-model", provider="mock", usage={"prompt_tokens":10,"completion_tokens":20,"total_tokens":30}, latency_ms=int(self._delay*1000) if self._delay else 0
        )

    def generate_structured(
        self,
        request: GenerateRequest,
        response_model: Any,
    ) -> Any:
        """Generate respons terstruktur palsu."""
        import time
        if self._delay > 0:
            time.sleep(self._delay)

        self._call_count += 1
        self._last_request = request

        if isinstance(response_model, type) and hasattr(response_model, "model_fields"):
            if set(response_model.model_fields) >= {"greeting", "mood"}:
                class Wrapped:
                    def __init__(self, data): self.data=data
                return Wrapped(response_model(greeting="Halo", mood="baik"))
            try:
                class Wrapped:
                    def __init__(self, data): self.data=data
                return Wrapped(response_model.model_validate(self._mock_structured))
            except Exception:
                return response_model.model_construct()
        return self._mock_structured

        return {"result": "mock structured result"}

    def health_check(self) -> Dict[str, Any]:
        """Check kesehatan mock provider."""
        return {
            "status": "healthy" if self._mock_health else "unhealthy",
            "provider": "mock",
            "model": "mock-model",
            "is_mock": True,
            "call_count": self._call_count,
        }

    def reset_call_count(self) -> None:
        """Reset hitungan pemanggilan."""
        self._call_count = 0

    def set_mock_response(self, response: str) -> None:
        """Set respons mock baru."""
        self._mock_response = response

    def set_mock_structured(self, data: Dict[str, Any]) -> None:
        """Set data mock terstruktur baru."""
        self._mock_structured = data

    def get_call_count(self) -> int:
        """Get jumlah pemanggilan."""
        return self._call_count


def create_mock_provider(
    mock_response: str = "Ini adalah respons mock.",
    mock_structured: Optional[Dict[str, Any]] = None,
) -> MockProvider:
    """Factory untuk membuat mock provider."""
    return MockProvider(
        mock_response=mock_response,
        mock_structured=mock_structured,
    )
