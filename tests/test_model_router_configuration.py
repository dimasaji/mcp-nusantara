"""Provider identity must describe the model actually used for generation."""
import pytest

from app.core.nusantara_config import load_nusantara_config
from app.models.mock import MockProvider
from app.models.ollama import OllamaProvider
from app.models.router import ModelRouter


@pytest.mark.parametrize("options", [
    {}, {"privacy": "sensitive"}, {"latency_sensitive": True}, {"budget_sensitive": True},
    {"task": "coding"}, {"task": "coding", "prefer_faster": True},
    {"task": "reasoning"}, {"task": "reasoning", "prefer_cheaper": True},
])
def test_snapshot_model_is_selected_in_every_ollama_branch(options):
    config = load_nusantara_config(overrides={"llm": {"model": "configured-local-model"}})
    provider = OllamaProvider(nusantara_config=config)
    selection = ModelRouter().register(provider).route(**options)
    assert selection.provider is provider
    assert selection.model_name == provider.model == config.llm.model
    assert provider._client is None


@pytest.mark.parametrize("task", ["general", "coding", "reasoning"])
def test_alternative_registered_provider_remains_usable(task):
    provider = MockProvider()
    selection = ModelRouter().register(provider).route(task=task)
    response = selection.provider.generate({"prompt": "fixture"})
    assert selection.provider is provider
    assert selection.model_name == provider.model
    assert response.model == selection.model_name


def test_provider_preferences_are_preserved_without_claiming_cloud_availability():
    # The openai name below is a local test fixture, not a live adapter/capability.
    local = MockProvider()
    local.provider_name, local.model_name = "ollama", "local-fixture"
    cloud = MockProvider()
    cloud.provider_name, cloud.model_name = "openai", "cloud-fixture"
    router = ModelRouter().register(local).register(cloud)
    assert router.route(task="coding").provider is cloud
    assert router.route(task="reasoning").model_name == "cloud-fixture"
    assert router.route(privacy="sensitive", task="coding").provider is local
    assert router.route(task="coding", prefer_faster=True).provider is local
    assert router.route(task="reasoning", prefer_cheaper=True).provider is local
    assert router.route(prefer_local=False).provider is cloud


def test_empty_registry_still_fails_clearly():
    with pytest.raises(RuntimeError, match="Tidak ada provider"):
        ModelRouter().route(task="coding")
