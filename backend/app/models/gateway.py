"""Opt-in model access boundary reusing the existing provider router.

No default provider, network probe, fallback policy, or capability is invented.
Existing orchestrator hardening owns timeouts, failure paths, and policy checks.
"""
from __future__ import annotations

import inspect
from typing import Any

from app.models.base import GenerateRequest
from app.models.router import ModelRouter, ModelSelection


class ModelGateway:
    def __init__(self, router: ModelRouter):
        self.router = router

    def select(self, **routing: Any) -> ModelSelection:
        return self.router.route(**routing)

    async def generate(self, request: GenerateRequest, **routing: Any) -> Any:
        selection = self.select(**routing)
        selection.assert_current_binding()
        result = selection.provider.generate(request)
        if inspect.isawaitable(result):
            result = await result
        selection.assert_current_binding()
        if isinstance(result, dict) and isinstance(result.get('execution_identity'), dict):
            identity = dict(result['execution_identity'])
            if (identity.get('provider_id') != selection.provider_name or
                    identity.get('payload_model') != selection.model_name):
                raise RuntimeError('provider/model receipt binding mismatch')
            identity.update(selection_reason=selection.reason,
                            selected_provider=selection.provider_name,
                            failover_status=selection.failover_status)
            result = {**result, 'execution_identity': identity}
        return result

    async def generate_text(self, prompt: str, **routing: Any) -> str:
        """Adapter for V2Orchestrator's existing generate(prompt) callback."""
        result = await self.generate({"prompt": prompt}, **routing)
        text = result.get("content") if isinstance(result, dict) else getattr(result, "text", None)
        if not isinstance(text, str):
            raise TypeError("provider response must contain text")
        return text
