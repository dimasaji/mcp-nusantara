"""Inventory must not instantiate a provider different from runtime selection."""
import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


def test_unsupported_inventory_provider_is_explicit_without_constructing_ollama(monkeypatch):
    from app.api.control_plane import _available_model_names
    from app.models import ollama

    def wrong_provider(**kwargs):
        pytest.fail('OpenRouter inventory must not construct Ollama')

    monkeypatch.setattr(ollama, 'OllamaProvider', wrong_provider)
    config = SimpleNamespace(llm=SimpleNamespace(provider='unsupported'))
    with pytest.raises(HTTPException) as error:
        asyncio.run(_available_model_names(config))
    assert error.value.status_code == 503
    assert error.value.detail == 'MODEL_INVENTORY_UNSUPPORTED_PROVIDER'


def test_openrouter_catalog_uses_only_existing_verified_pricing(tmp_path, monkeypatch):
    import json
    from app.api.control_plane import _available_model_names
    from app.models import ollama
    monkeypatch.setattr(ollama, 'OllamaProvider', lambda **kwargs: pytest.fail('wrong provider'))
    pricing=tmp_path/'data/config/openrouter-pricing-v1.json'
    pricing.parent.mkdir(parents=True)
    valid={'verified':True,'input_usd_per_token':'0.000001','output_usd_per_token':'0.000001',
           'max_input_tokens':4096,'max_output_tokens':220}
    pricing.write_text(json.dumps({'models':{'fixture/approved':valid,'fixture/unverified':{**valid,'verified':False}}}))
    config=SimpleNamespace(llm=SimpleNamespace(provider='openrouter'),paths=SimpleNamespace(project_root=tmp_path))
    before=pricing.read_bytes()
    assert asyncio.run(_available_model_names(config))==['fixture/approved']
    assert pricing.read_bytes()==before
    pricing.unlink()
    with pytest.raises(HTTPException) as error:
        asyncio.run(_available_model_names(config))
    assert error.value.status_code==503 and not pricing.exists()
