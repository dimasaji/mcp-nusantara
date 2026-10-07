"""
OpenAICompatibleProvider - implementasi LLMProvider untuk API yang kompatibel dengan OpenAI.
Bisa digunakan untuk Azure OpenAI, LM Studio, vLLM, dll.
"""
import json
import time
from typing import Any, Dict, List, Optional

import httpx
from app.core.runtime_identity import capture_model_identity

from app.models.base import (
    GenerateRequest,
    GenerateResponse,
    StructuredGenerateRequest,
    StructuredGenerateResponse,
    HealthCheckResponse,
    LLMProvider,
)


class OpenAICompatibleProvider(LLMProvider):
    """
    Provider untuk API yang kompatibel dengan OpenAI format.
    
    Mendukung: Azure OpenAI, LM Studio, vLLM, llama.cpp server, dll.
    """

    provider_name = "openai_compatible"
    model_name = "gpt-4o-mini"

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        api_key: str = "lm-studio",
        model: str | None = None,
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model if model is not None else 'gpt-4o-mini'
        self._requested_model = model
        self._model_source = 'EXPLICIT_CONSTRUCTOR' if model is not None else 'DEFAULT'
        self.last_health_identity = None
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get atau buat HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        request: GenerateRequest,
    ) -> GenerateResponse:
        """Generate teks menggunakan OpenAI-compatible API."""
        identity = capture_model_identity(provider_id=self.name, selected_model=self.model,
            requested_model=self._requested_model, override_source=self._model_source)
        client = await self._get_client()
        
        messages: List[Dict[str, str]] = []
        
        if request.get("system"):
            messages.append({"role": "system", "content": request["system"]})
        
        messages.append({"role": "user", "content": request.get("prompt", "")})
        
        payload: Dict[str, Any] = {
            "model": identity.payload_model,
            "messages": messages,
            "stream": False,
        }
        
        if request.get("max_tokens"):
            payload["max_tokens"] = request["max_tokens"]
        if request.get("temperature"):
            payload["temperature"] = request["temperature"]
        if request.get("top_p"):
            payload["top_p"] = request["top_p"]
        
        start_time = time.time()
        
        try:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            result = response.json()
            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            
            # Estimate tokens (OpenAI biasanya tidak return token usage di semua provider)
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            return GenerateResponse(
                content=content,
                model=identity.payload_model,
                execution_identity=identity.with_response(result.get('model'),
                    completed=bool(result.get('choices'))).safe_dump(),
                tokens_used=prompt_tokens + completion_tokens,
                latency_ms=int((time.time() - start_time) * 1000),
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
        except Exception as e:
            raise RuntimeError(f"OpenAI-compatible generate failed: {str(e)}") from e

    async def generate_structured(
        self,
        request: StructuredGenerateRequest,
    ) -> StructuredGenerateResponse:
        """Generate dengan output terstruktur menggunakan function calling atau JSON mode."""
        identity = capture_model_identity(provider_id=self.name, selected_model=self.model,
            requested_model=self._requested_model, override_source=self._model_source)
        client = await self._get_client()
        
        messages: List[Dict[str, str]] = []
        
        if request.get("system"):
            messages.append({"role": "system", "content": request["system"]})
        
        prompt = request.get("prompt", "")
        schema = request.get("schema", {})
        
        # Coba gunakan response_format = json_schema jika didukung
        if schema and self._supports_json_schema():
            messages.append({"role": "user", "content": prompt})
            
            payload: Dict[str, Any] = {
                "model": identity.payload_model,
                "messages": messages,
                "stream": False,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_output",
                        "schema": schema,
                    },
                },
            }
            
            if request.get("max_tokens"):
                payload["max_tokens"] = request["max_tokens"]
            if request.get("temperature"):
                payload["temperature"] = request["temperature"]
            
            start_time = time.time()
            
            try:
                response = await client.post("/chat/completions", json=payload)
                response.raise_for_status()
                
                result = response.json()
                choice = result.get("choices", [{}])[0]
                message = choice.get("message", {})
                content_str = message.get("content", "{}")
                
                try:
                    content = json.loads(content_str)
                except json.JSONDecodeError:
                    content = {"error": "Failed to parse JSON", "raw": content_str}
                
                return StructuredGenerateResponse(
                    content=content,
                    model=identity.payload_model,
                    execution_identity=identity.with_response(result.get('model'),
                        completed=bool(result.get('choices'))).safe_dump(),
                    tokens_used=0,  # JSON schema mode tidak selalu return usage
                    latency_ms=int((time.time() - start_time) * 1000),
                )
            except Exception as e:
                raise RuntimeError(f"Structured generate failed: {str(e)}") from e
        else:
            # Fallback: pakai prompt engineering
            prompt = f"{prompt}\n\nOutput harus dalam format JSON berikut:\n{json.dumps(schema, indent=2)}\n\nJawab dalam JSON saja."
            
            generate_request: GenerateRequest = {
                "prompt": prompt,
                "system": request.get("system"),
                "max_tokens": request.get("max_tokens"),
                "temperature": request.get("temperature"),
            }
            
            result = await self.generate(generate_request)
            
            try:
                content = json.loads(result["content"])
            except json.JSONDecodeError:
                content = {"raw": result["content"]}
            
            return StructuredGenerateResponse(
                content=content,
                model=result['model'],
                execution_identity={**result['execution_identity'], 'format_fallback': 'TEXT_JSON'},
                tokens_used=result["tokens_used"],
                latency_ms=result["latency_ms"],
            )

    def _supports_json_schema(self) -> bool:
        """Cek apakah provider mendukung JSON schema response format."""
        # Default: True untuk OpenAI, bisa di-override oleh subclass
        return True

    async def health_check(self) -> HealthCheckResponse:
        """Cek kesehatan API."""
        identity = capture_model_identity(provider_id=self.name, selected_model=self.model,
            requested_model=self._requested_model, override_source=self._model_source)
        client = await self._get_client()
        
        start_time = time.time()
        
        try:
            response = await client.get("/models")
            response.raise_for_status()
            
            models_data = response.json()
            models = models_data.get("data", [])
            available = any(m.get("id") == identity.payload_model for m in models)
            self.last_health_identity = {**identity.safe_dump(),
                'confirmation_source': 'MODEL_INVENTORY_ONLY',
                'model_available': available, 'actual_model': None,
                'identity_status': 'NOT_VERIFIED'}
            
            return HealthCheckResponse(
                status="ok" if available else "degraded",
                model=identity.payload_model,
                available=available,
                latency_ms=int((time.time() - start_time) * 1000),
            )
        except Exception:
            self.last_health_identity = {**identity.safe_dump(), 'model_available': False}
            return HealthCheckResponse(
                status="unavailable",
                model=identity.payload_model,
                available=False,
                latency_ms=int((time.time() - start_time) * 1000),
            )

    async def list_models(self) -> List[Dict[str, Any]]:
        """List semua model yang tersedia."""
        client = await self._get_client()
        response = await client.get("/models")
        response.raise_for_status()
        return response.json().get("data", [])
