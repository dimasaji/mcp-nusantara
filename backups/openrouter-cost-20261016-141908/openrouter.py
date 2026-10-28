"""Explicitly selected cloud adapter; no fallback, retries or eager secrets.

Usage and response model are provider-reported, never weight attestation.
Cancellation stops browser/client waiting, not necessarily server-side work.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import time
from typing import Callable

import httpx

from app.core.nusantara_config import ConfigurationError, NusantaraConfig
from app.core.runtime_identity import capture_model_identity
from app.models.base import LLMProvider


class OpenRouterError(RuntimeError):
    """Identifiers only: never attach raw HTTP bodies, headers or exceptions."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"OpenRouter: {code}")


class OpenRouterProvider(LLMProvider):
    provider_name = "openrouter"

    def __init__(self, *, nusantara_config: NusantaraConfig,
                 http_client: httpx.AsyncClient | None = None,
                 key_resolver: Callable[[], str | None] | None = None,
                 cost_ledger=None, cost_estimator=None):
        if nusantara_config.llm.provider != self.name:
            raise ConfigurationError("PROVIDER_MISMATCH")
        self.configuration = nusantara_config
        self.model_name = nusantara_config.llm.model
        self.base_url = nusantara_config.llm.base_url
        self.timeout = nusantara_config.llm.connection_timeout_s
        self._client = http_client
        self._owns_client = http_client is None
        # Only evaluated on explicit generation. No key is stored on the object.
        self._key_resolver = key_resolver or (lambda: os.environ.get("OPENROUTER_API_KEY"))
        self._cost_ledger = cost_ledger
        self._cost_estimator = cost_estimator

    def _key(self):
        try:
            key = self._key_resolver()
        except Exception:
            raise OpenRouterError("KEY_UNAVAILABLE") from None
        if not isinstance(key, str) or not key.strip() or "\r" in key or "\n" in key:
            raise OpenRouterError("KEY_UNAVAILABLE")
        return key

    async def generate(self, request):
        if self._cost_ledger is None or not callable(self._cost_estimator):
            raise OpenRouterError("COST_GOVERNANCE_UNAVAILABLE")

        if request.get("stream"):
            raise OpenRouterError("STREAM_UNSUPPORTED")
        prompt = request.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise OpenRouterError("INVALID_REQUEST")
        maximum = request.get("max_tokens")
        if maximum is None:
            maximum = self.configuration.llm.generation.max_tokens
        if type(maximum) is not int or maximum <= 0:
            raise OpenRouterError("INVALID_REQUEST")
        messages = []
        if request.get("system") is not None:
            if not isinstance(request["system"], str):
                raise OpenRouterError("INVALID_REQUEST")
            messages.append({"role": "system", "content": request["system"]})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "stream": False,
                   "max_tokens": min(maximum, self.configuration.llm.generation.max_tokens)}
        for name in ("temperature", "top_p"):
            value = request.get(name)
            if value is not None:
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise OpenRouterError("INVALID_REQUEST")
                if name == "temperature" and value > 2:
                    raise OpenRouterError("INVALID_REQUEST")
                if name == "top_p" and not 0 < value <= 1:
                    raise OpenRouterError("INVALID_REQUEST")
                payload[name] = value
        key = self._key()
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=False,
                                             trust_env=False)
        identity = capture_model_identity(provider_id=self.name, selected_model=self.model,
                                           configuration=self.configuration)
        started = time.perf_counter()
        # HTTPX enforces per-I/O deadlines; asyncio bounds the entire operation.
        try:
            async with asyncio.timeout(self.timeout):
                async with self._client.stream("POST", self.base_url + "/chat/completions",
                        json=payload, headers={"Authorization": "Bearer " + key},
                        timeout=self.timeout, follow_redirects=False) as response:
                    if response.status_code != 200:
                        raise OpenRouterError("HTTP_" + str(response.status_code))
                    raw = bytearray()
                    async for chunk in response.aiter_bytes():
                        raw.extend(chunk)
                        if len(raw) > 2 * 1024 * 1024:
                            raise OpenRouterError("RESPONSE_TOO_LARGE")
                    data = json.loads(raw)
        except OpenRouterError:
            raise
        except (httpx.TimeoutException, TimeoutError):
            raise OpenRouterError("TIMEOUT") from None
        except Exception:
            raise OpenRouterError("REQUEST_FAILED") from None
        # CancelledError is deliberately not caught: no retry or fallback.
        try:
            if not isinstance(data, dict) or "error" in data:
                raise ValueError()
            choices = data["choices"]
            if not isinstance(choices, list) or not choices:
                raise ValueError()
            content = choices[0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError()
            actual = data.get("model")
            if actual is not None and (not isinstance(actual, str) or not actual.strip() or
                    len(actual) > 256):
                raise ValueError()
        except (KeyError, IndexError, TypeError, ValueError):
            raise OpenRouterError("INVALID_RESPONSE") from None
        usage = data.get("usage")
        usage = usage if isinstance(usage, dict) else {}
        def count(name):
            value = usage.get(name)
            return value if type(value) is int and value >= 0 else None
        cost = usage.get("cost")
        cost = cost if type(cost) in (int, float) and math.isfinite(cost) and cost >= 0 else None
        reported_usage = {"input_tokens": count("prompt_tokens"),
                          "output_tokens": count("completion_tokens"),
                          "total_tokens": count("total_tokens"), "cost": cost,
                          "source": "PROVIDER_REPORTED",
                          "status": "AVAILABLE" if all(count(name) is not None for name in
                              ("prompt_tokens", "completion_tokens", "total_tokens")) else "UNKNOWN"}
        return {"content": content.strip(), "model": self.model,
                "requested_model": self.model, "reported_model": actual,
                "tokens_used": reported_usage["total_tokens"], "usage": reported_usage,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "provider_status": self.name,
                "execution_identity": identity.with_response(actual).safe_dump()}

    async def generate_structured(self, request):
        # The existing abstraction exposes structured output. Fail closed rather
        # than silently claiming schema validation for an unsupported capability.
        raise OpenRouterError("STRUCTURED_UNSUPPORTED")

    async def health_check(self):
        # No model-list request or paid probe: configuration readiness only.
        try:
            self._key()
        except OpenRouterError:
            return {"status": "KEY_UNAVAILABLE", "available": False,
                    "model": self.model, "latency_ms": 0}
        return {"status": "NOT_VERIFIED", "available": True,
                "model": self.model, "latency_ms": 0}

    def get_model_info(self):
        return {"provider": self.name, "model": self.model, "supports_structured": False,
                "availability": "NOT_VERIFIED", "loaded_weights": "NOT_VERIFIED",
                "hard_budget_enforcement": False}

    async def close(self):
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

