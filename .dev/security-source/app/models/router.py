"""
Model Router - memilih model berdasarkan task, complexity, privacy, latency, cost.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, cast

from app.models.base import GenerateRequest, GenerateResponse, LLMProvider

if TYPE_CHECKING:
    from app.models.base import LLMProvider


class ModelSelection:
    """Hasil pemilihan model."""

    def __init__(
        self,
        provider: LLMProvider,
        model_name: str,
        reason: str,
        estimated_latency_ms: int,
        estimated_cost_per_1k_tokens: float,
    ):
        self.provider = provider
        self.model_name = model_name
        self.reason = reason
        self.estimated_latency_ms = estimated_latency_ms
        self.estimated_cost_per_1k_tokens = estimated_cost_per_1k_tokens

    def __repr__(self) -> str:
        return f"ModelSelection(provider={self.provider.name!r}, model={self.model_name!r}, reason={self.reason!r})"


class ModelRouter:
    """Model router yang memilih provider berdasarkan konteks penggunaan."""

    def __init__(self) -> None:
        self._providers: Dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> ModelRouter:
        self._providers[provider.name] = provider
        return self

    def route(
        self,
        task: str = "general",
        complexity: str = "medium",
        privacy: str = "internal",
        latency_sensitive: bool = False,
        budget_sensitive: bool = False,
        prefer_local: bool = True,
        prefer_faster: bool = False,
        prefer_cheaper: bool = False,
    ) -> ModelSelection:
        """
        Pilih model terbaik berdasarkan konteks.
        """
        providers = self._providers
        if not providers:
            raise RuntimeError("Tidak ada provider yang terdaftar. Gunakan router.register()")

        # Decision tree sederhana
        if privacy == "sensitive" and "ollama" in providers:
            provider = providers["ollama"]
            reason = "Privacy sensitif: all data stays local"
            return ModelSelection(provider, provider.model, reason, 1000, 0.0)

        if latency_sensitive and "ollama" in providers:
            provider = providers["ollama"]
            reason = "Latensi rendah: local inference, no network round-trip"
            return ModelSelection(provider, provider.model, reason, 500, 0.0)

        if budget_sensitive and "ollama" in providers:
            provider = providers["ollama"]
            reason = "Biaya nol: local inference, no API cost"
            return ModelSelection(provider, provider.model, reason, 800, 0.0)

        # Task-based selection
        if task in ("code", "coding", "programming", "debug", "refactor"):
            if prefer_faster and "ollama" in providers:
                provider = providers["ollama"]
                model = provider.model
                reason = "Coding task + prefer faster: local model"
            else:
                provider = (providers.get("openai") or providers.get("ollama")
                            or next(iter(providers.values())))
                model = provider.model
                reason = "Coding task: memilih model dengan coding capability"
            return ModelSelection(provider, model, reason, 1500, 0.0 if provider.name == "ollama" else 0.01)

        if task in ("math", "logic", "reasoning", "analysis"):
            if prefer_cheaper and "ollama" in providers:
                provider = providers["ollama"]
                model = provider.model
                reason = "Reasoning task + budget: local model"
            else:
                provider = (providers.get("openai") or providers.get("ollama")
                            or next(iter(providers.values())))
                model = provider.model
                reason = "Reasoning task: model dengan reasoning capability"
            return ModelSelection(provider, model, reason, 2000, 0.0 if provider.name == "ollama" else 0.015)

        # Default: general tasks
        if prefer_local and "ollama" in providers:
            provider = providers["ollama"]
            model = provider.model
            reason = "General task + local preference: ollama"
        elif "openai" in providers:
            provider = providers["openai"]
            model = provider.model
            reason = "General task: openai (fallback)"
        else:
            provider = next(iter(providers.values()))
            model = getattr(provider, "model", getattr(provider, "model_name", "default"))
            reason = "General task: registered provider fallback"

        return ModelSelection(provider, model, reason, 800, 0.0 if provider.name == "ollama" else 0.005)

    def route_and_generate(
        self,
        request: GenerateRequest,
        task: str = "general",
        complexity: str = "medium",
        privacy: str = "internal",
        latency_sensitive: bool = False,
        budget_sensitive: bool = False,
        prefer_local: bool = True,
    ) -> GenerateResponse:
        """
        Route dan generate dalam satu langkah.
        """
        selection = self.route(
            task=task,
            complexity=complexity,
            privacy=privacy,
            latency_sensitive=latency_sensitive,
            budget_sensitive=budget_sensitive,
            prefer_local=prefer_local,
        )
        return cast(LLMProvider, selection.provider).generate(request)

    def list_providers(self) -> Dict[str, str]:
        """List provider yang terdaftar."""
        return {name: provider.model for name, provider in self._providers.items()}
