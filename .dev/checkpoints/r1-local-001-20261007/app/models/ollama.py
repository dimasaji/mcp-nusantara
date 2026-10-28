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
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:1b",
        timeout: float = 120.0,
        *,
        nusantara_config: NusantaraConfig | None = None,
    ):
        # Existing positional values remain authoritative when non-default.
        # Default-valued legacy arguments are interpreted as unspecified when
        # opting into a snapshot; omit snapshot to retain exact legacy behavior.
        self._configuration = nusantara_config
        if nusantara_config is not None:
            if nusantara_config.llm.provider != self.provider_name:
                raise ConfigurationError("PROVIDER_MISMATCH")
            if base_url == "http://localhost:11434":
                base_url = nusantara_config.llm.base_url
            if model == "llama3.2:1b":
                model = nusantara_config.llm.model
            if timeout == 120.0:
                timeout = nusantara_config.llm.connection_timeout_s
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

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
        client = await self._get_client()
        
        payload: Dict[str, Any] = {
            "model": self.model,
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
            
            return GenerateResponse(
                content=content,
                model=self.model,
                tokens_used=result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                latency_ms=int((time.time() - start_time) * 1000),
            )
        except httpx.HTTPStatusError as e:
            raise ProviderUnavailableError(self.provider_name) from e
        except httpx.RequestError as e:
            raise ProviderUnavailableError(self.provider_name) from e
        except Exception as e:
            raise RuntimeError(f"Ollama generate failed: {str(e)}") from e

    async def generate_structured(
        self,
        request: StructuredGenerateRequest,
    ) -> StructuredGenerateResponse:
        """Generate dengan output terstruktur (JSON schema)."""
        client = await self._get_client()
        
        prompt = request.get("prompt", "")
        system = request.get("system", "")
        
        # Tambahkan instruction untuk output JSON
        schema = request.get("schema", {})
        if schema:
            json_schema = json.dumps(schema, indent=2)
            prompt = f"{prompt}\n\nOutput harus dalam format JSON berikut:\n{json_schema}\n\nJawab dalam JSON saja."
        
        payload: Dict[str, Any] = {
            "model": self.model,
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
            
            return StructuredGenerateResponse(
                content=content,
                model=self.model,
                tokens_used=result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                latency_ms=int((time.time() - start_time) * 1000),
            )
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            raise ProviderUnavailableError(self.provider_name) from e
        except Exception as e:
            raise RuntimeError(f"Ollama structured generate failed: {str(e)}") from e

    async def health_check(self) -> HealthCheckResponse:
        """Cek kesehatan Ollama server."""
        client = await self._get_client()
        
        start_time = time.time()
        
        try:
            # Cek list model
            response = await client.get("/api/tags")
            response.raise_for_status()
            
            models = response.json().get("models", [])
            available = any(m.get("name") == self.model for m in models)
            
            return HealthCheckResponse(
                status="ok" if available else "degraded",
                model=self.model,
                available=available,
                latency_ms=int((time.time() - start_time) * 1000),
            )
        except Exception:
            return HealthCheckResponse(
                status="unavailable",
                model=self.model,
                available=False,
                latency_ms=int((time.time() - start_time) * 1000),
            )

    async def list_models(self) -> List[Dict[str, Any]]:
        """List semua model yang tersedia di Ollama."""
        client = await self._get_client()
        response = await client.get("/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])
