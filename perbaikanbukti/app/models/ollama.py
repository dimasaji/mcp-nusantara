"""
OllamaProvider - implementasi LLMProvider untuk Ollama.
Tidak boleh ada direct Ollama call di luar provider ini.
"""
import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import httpx
from app.exceptions import ProviderUnavailableError
from app.core.config import settings
from app.core.nusantara_config import ConfigurationError, NusantaraConfig
from app.core.runtime_identity import capture_model_identity
from app.observability.logging import log_event

from app.models.base import (
    GenerateRequest,
    GenerateResponse,
    StructuredGenerateRequest,
    StructuredGenerateResponse,
    HealthCheckResponse,
    LLMProvider,
)


class OllamaProvider(LLMProvider):
    """
    Provider untuk Ollama Local API.
    
    Menggunakan HTTP client untuk komunikasi dengan Ollama server.
    Semua call ke Ollama harus melalui provider ini.
    """

    provider_name = "ollama"
    model_name = "llama3.2:1b"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        *,
        nusantara_config: NusantaraConfig | None = None,
        model_source: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        # Omitted values use the snapshot; explicit values always win, including
        # values equal to the old defaults. No provider registry is duplicated.
        self._configuration = nusantara_config
        self._requested_model = model
        self._model_source = (model_source or 'EXPLICIT_CONSTRUCTOR') if model is not None else (
            'CONFIGURATION' if nusantara_config is not None else 'DEFAULT')
        self.last_health_identity = None
        if nusantara_config is not None:
            if nusantara_config.llm.provider != self.provider_name:
                raise ConfigurationError("PROVIDER_MISMATCH")
            if base_url is None:
                base_url = nusantara_config.llm.base_url
            if model is None:
                model = nusantara_config.llm.model
            if timeout is None:
                timeout = nusantara_config.llm.connection_timeout_s
        self.base_url = (base_url if base_url is not None else "http://localhost:11434").rstrip("/")
        self.model_name = model if model is not None else "llama3.2:1b"
        self.timeout = timeout if timeout is not None else 120.0
        # An explicitly injected diagnostic client is owned/closed by this instance.
        self._client: Optional[httpx.AsyncClient] = http_client
        self._injected_client = http_client is not None

    def _capture_identity(self):
        return capture_model_identity(provider_id=self.name, selected_model=self.model,
            configuration=self._configuration, requested_model=self._requested_model,
            override_source=self._model_source)

    @staticmethod
    def _emit_identity(identity, *, failed: bool = False) -> None:
        # Console telemetry is an observation, never overall live verification.
        fields = {key: getattr(identity, key) for key in (
            'request_id', 'request_id_source', 'invocation_id', 'runtime_instance_id',
            'timestamp', 'instance_captured_at', 'build_id', 'process_id',
            'provider_id', 'configured_model', 'effective_model', 'selected_model',
            'payload_model', 'actual_model', 'identity_status', 'confirmation_source')}
        fields['result'] = ('ERROR' if failed else 'MISMATCH'
                            if identity.identity_status == 'MISMATCH' else 'NOT_VERIFIED')
        try:
            log_event('provider_generation_identity', **fields)
        except Exception:
            # Logging failure must not change generation results or mask errors.
            pass

    def _options(self, request) -> dict:
        generation = self._configuration.llm.generation if self._configuration else None
        context = generation.context_length if generation else settings.llm_context_tokens
        if not 512 <= context <= 131072:
            raise ValueError('llm_context_tokens must be between 512 and 131072')
        options = {'num_ctx': context, 'num_predict': generation.max_tokens if generation else 512}
        if request.get('max_tokens') is not None:
            options['num_predict'] = max(1, min(int(request['max_tokens']), context))
        for key in ('temperature', 'top_p'):
            if request.get(key) is not None:
                options[key] = request[key]
            elif generation is not None and getattr(generation, key) is not None:
                options[key] = getattr(generation, key)
        return options

    async def _get_client(self) -> httpx.AsyncClient:
        """Get atau buat HTTP client."""
        if self._client is None or self._client.is_closed:
            if self._injected_client:
                raise RuntimeError('INJECTED_CLIENT_CLOSED')
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
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
        """Generate teks dari Ollama API."""
        identity = self._capture_identity()
        client = await self._get_client()
        
        payload: Dict[str, Any] = {
            "model": identity.payload_model,
            "prompt": request.get("prompt", ""),
            "stream": False,
            "options": self._options(request),
        }
        
        if request.get("system"):
            payload["system"] = request["system"]
        
        start_time = time.time()
        
        try:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("response", "")
            receipt = identity.with_response(result.get('model'),
                                            completed=result.get('done') is True)
            self._emit_identity(receipt)
            
            return GenerateResponse(
                content=content,
                model=identity.payload_model,
                execution_identity=receipt.safe_dump(),
                tokens_used=result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                latency_ms=int((time.time() - start_time) * 1000),
            )
        except httpx.HTTPStatusError as e:
            self._emit_identity(identity, failed=True)
            raise ProviderUnavailableError(self.provider_name) from e
        except httpx.RequestError as e:
            self._emit_identity(identity, failed=True)
            raise ProviderUnavailableError(self.provider_name) from e
        except Exception as e:
            self._emit_identity(identity, failed=True)
            raise RuntimeError(f"Ollama generate failed: {str(e)}") from e

    async def generate_structured(
        self,
        request: StructuredGenerateRequest,
    ) -> StructuredGenerateResponse:
        """Generate dengan output terstruktur (JSON schema)."""
        identity = self._capture_identity()
        client = await self._get_client()
        
        prompt = request.get("prompt", "")
        system = request.get("system", "")
        
        # Tambahkan instruction untuk output JSON
        schema = request.get("schema", {})
        if schema:
            json_schema = json.dumps(schema, indent=2)
            prompt = f"{prompt}\n\nOutput harus dalam format JSON berikut:\n{json_schema}\n\nJawab dalam JSON saja."
        
        payload: Dict[str, Any] = {
            "model": identity.payload_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": "json",
            "options": self._options(request),
        }
        
        
        start_time = time.time()
        
        try:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            
            result = response.json()
            content_str = result.get("response", "{}")
            
            # Parse JSON dari response
            try:
                content = json.loads(content_str)
            except json.JSONDecodeError:
                content = {"error": "Failed to parse JSON", "raw": content_str}
            receipt = identity.with_response(result.get('model'),
                                            completed=result.get('done') is True)
            self._emit_identity(receipt)
            
            return StructuredGenerateResponse(
                content=content,
                model=identity.payload_model,
                execution_identity=receipt.safe_dump(),
                tokens_used=result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                latency_ms=int((time.time() - start_time) * 1000),
            )
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            self._emit_identity(identity, failed=True)
            raise ProviderUnavailableError(self.provider_name) from e
        except Exception as e:
            self._emit_identity(identity, failed=True)
            raise RuntimeError(f"Ollama structured generate failed: {str(e)}") from e

    async def health_check(self) -> HealthCheckResponse:
        """Cek kesehatan Ollama server."""
        identity = self._capture_identity()
        client = await self._get_client()
        
        start_time = time.time()
        
        try:
            # Cek list model
            response = await client.get("/api/tags")
            response.raise_for_status()
            
            models = response.json().get("models", [])
            available = any(m.get("name") == identity.payload_model for m in models)
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
        """List semua model yang tersedia di Ollama."""
        client = await self._get_client()
        response = await client.get("/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])
