"""Configuration loading contracts; no production imports or state changes."""
import dataclasses
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from app.core.nusantara_config import ConfigurationError, load_nusantara_config


def test_defaults_preserve_declared_and_effective_source_profiles(tmp_path):
    config = load_nusantara_config(project_root=tmp_path)
    assert config.llm.provider == "ollama"
    assert config.llm.model == "llama3.2:1b"
    assert config.llm.generation.context_length == 4096
    assert config.embedding.model == "indobenchmark/indobert-base-p1"
    assert config.embedding.dimension == 768
    assert config.knowledge.store_backend == "sqlite"
    assert config.legacy_declarations.embedding_model == "local-hash"
    assert config.legacy_declarations.vector_store_type == "memory"
    assert config.runtime.port == 8000
    assert config.rag.top_k == 5
    assert config.features.developer_core is None
    assert not (tmp_path / "data").exists()
    assert all(record.source == "DEFAULT" for record in config.provenance)


def test_leaf_precedence_and_input_not_mutated(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"llm": {"model": "file-model"},
                               "runtime": {"port": 8001}, "rag": {"top_k": 6}}))
    env = {"llm_model": "env-model", "PORT": "8002"}
    explicit = {"llm": {"model": "explicit-model"}}
    config = load_nusantara_config(config_file=path, environment=env,
                                  overrides=explicit, project_root=tmp_path)
    assert config.llm.model == "explicit-model"
    assert config.runtime.port == 8002
    assert config.rag.top_k == 6
    assert config.llm.generation.max_tokens == 512
    sources = {p.field: p.source for p in config.provenance}
    assert sources["llm.model"] == "EXPLICIT"
    assert sources["runtime.port"] == "ENV"
    assert sources["rag.top_k"] == "FILE"
    assert env == {"llm_model": "env-model", "PORT": "8002"}
    assert explicit == {"llm": {"model": "explicit-model"}}


def test_environment_opt_in_and_no_dotenv_loading(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("LLM_MODEL=dotenv-model\n")
    monkeypatch.setenv("LLM_MODEL", "process-model")
    monkeypatch.chdir(tmp_path)
    assert load_nusantara_config().llm.model == "llama3.2:1b"
    assert load_nusantara_config(environment={"LLM_MODEL": os.environ["LLM_MODEL"]}).llm.model == "process-model"


@pytest.mark.parametrize("env", [
    {"LLM_MODEL": "one", "llm_model": "one"},
    {"LLM_MODEL": "one", "NUSANTARA_LLM_MODEL": "two"},
    {"RETRIEVAL_TOP_K": "5", "NUSANTARA_RAG_TOP_K": "5"},
])
def test_alias_conflict_is_order_independent(env):
    for values in (env, dict(reversed(list(env.items())))):
        with pytest.raises(ConfigurationError, match="ENV_ALIAS_CONFLICT"):
            load_nusantara_config(environment=values)


@pytest.mark.parametrize("overrides", [
    {"runtime": {"port": 0}}, {"runtime": {"port": 65536}},
    {"runtime": {"port": True}}, {"runtime": {"port": "8000"}},
    {"runtime": {"workers": 0}}, {"runtime": {"stage_timeout_s": float("nan")}},
    {"llm": {"connection_timeout_s": float("inf")}},
    {"llm": {"provider": "unsupported"}}, {"llm": {"model": ""}},
    {"llm": {"model": "   "}}, {"llm": {"generation": {"top_p": 0}}},
    {"llm": {"generation": {"max_tokens": 8192}}},
    {"llm": {"generation": {"context_length": 511}}},
    {"rag": {"chunk_overlap": 512}}, {"rag": {"top_k": 0}},
    {"rag": {"semantic_weight": 0.7}},
    {"rag": {"semantic_weight": 0.7, "lexical_weight": 0.7}},
    {"rag": {"similarity_threshold": 2}},
    {"rag": {"reranker_enabled": True}},
    {"features": {"reranker": True}},
    {"knowledge": {"store_backend": "memory"}},
    {"unknown": {"secret": "credential-sentinel"}},
    {"llm": {"api_key": "credential-sentinel"}},
])
def test_invalid_configuration_rejected_with_safe_error(overrides):
    with pytest.raises(ConfigurationError) as caught:
        load_nusantara_config(overrides=overrides)
    assert "credential-sentinel" not in str(caught.value)
    assert "credential-sentinel" not in repr(caught.value)


@pytest.mark.parametrize("url", ["https://u:credential-sentinel@example.com", "http://host/?key=credential-sentinel", "file:///secret", "https://host/#credential-sentinel", "http://host:wrong", "http://host:0"])
def test_credential_url_safe_error(url):
    with pytest.raises(ConfigurationError) as caught:
        load_nusantara_config(overrides={"llm": {"base_url": url}})
    assert "credential-sentinel" not in str(caught.value)


def test_secret_values_never_resolved_or_dumped():
    config = load_nusantara_config(environment={"LLM_API_KEY": "credential-sentinel", "OPENAI_API_KEY": "credential-sentinel", "AUTH_REF": "credential-sentinel"},
                                  overrides={"llm": {"auth_env_ref": "AUTH_REF"}})
    assert config.llm.auth_env_ref == "AUTH_REF"
    surfaces = [repr(config), repr(config.llm), json.dumps(config.safe_dump()), config.canonical_json(), repr(config.provenance)]
    assert all("credential-sentinel" not in s and "AUTH_REF" not in s for s in surfaces)


def test_nested_immutability_and_defensive_dump(tmp_path):
    config = load_nusantara_config(project_root=tmp_path)
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.provenance = ()
    with pytest.raises(Exception):
        config.llm.model = "changed"
    with pytest.raises(Exception):
        config.llm.generation.max_tokens = 1
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.provenance[0].source = "EXPLICIT"
    dump = config.safe_dump()
    dump["llm"]["model"] = "changed"
    assert config.llm.model == "llama3.2:1b"


def test_paths_lexically_resolved_without_touching_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = load_nusantara_config(environment={"NUSANTARA_KNOWLEDGE_DB": "custom/db.sqlite", "NUSANTARA_INDOBERT_WORKER": "worker.py"})
    assert config.knowledge.database == tmp_path / "custom/db.sqlite"
    assert config.paths.worker == tmp_path / "worker.py"
    assert not (tmp_path / "custom").exists()
    absolute = tmp_path / "elsewhere.db"
    assert load_nusantara_config(overrides={"knowledge": {"database": absolute}}).knowledge.database == absolute
    with pytest.raises(ConfigurationError, match="ROOT_CONFLICT"):
        load_nusantara_config(overrides={"paths": {"project_root": tmp_path / "other"}})


@pytest.mark.parametrize("content", ["bad credential-sentinel", "[]", '{"runtime":{"port":8001,"port":8002}}', '{"runtime":{"stage_timeout_s":NaN}}'])
def test_file_errors_bounded_and_safe(tmp_path, content):
    path = tmp_path / "config.json"
    path.write_text(content)
    with pytest.raises(ConfigurationError) as caught:
        load_nusantara_config(config_file=path)
    assert "credential-sentinel" not in str(caught.value)


def test_missing_and_oversized_file(tmp_path):
    with pytest.raises(ConfigurationError):
        load_nusantara_config(config_file=tmp_path / "missing-credential-sentinel.json")
    path = tmp_path / "huge.json"
    path.write_bytes(b" " * (1024 * 1024 + 1))
    with pytest.raises(ConfigurationError, match="FILE_SIZE_LIMIT"):
        load_nusantara_config(config_file=path)


@pytest.mark.parametrize("environment", [{"PORT": "credential-sentinel"}, {"PORT": "1.5"}, {"DEBUG": "yes"}, {"PORT": "true"}, {"PORT": 8000}])
def test_invalid_environment(environment):
    with pytest.raises(ConfigurationError) as caught:
        load_nusantara_config(environment=environment)
    assert "credential-sentinel" not in str(caught.value)


def test_bounded_depth_and_no_interpolation():
    data = "credential-sentinel"
    for _ in range(15):
        data = {"nested": data}
    with pytest.raises(ConfigurationError, match="DEPTH_LIMIT"):
        load_nusantara_config(overrides=data)
    config = load_nusantara_config(overrides={"llm": {"model": "${UNRESOLVED_MODEL}"}})
    assert config.llm.model == "${UNRESOLVED_MODEL}"


def test_determinism_with_input_order_and_empty_overrides(tmp_path):
    first = load_nusantara_config(project_root=tmp_path, environment={"PORT": "8010", "LLM_MODEL": "test-model"})
    second = load_nusantara_config(project_root=tmp_path, environment={"LLM_MODEL": "test-model", "PORT": "8010"}, overrides={})
    assert first == second
    assert first.canonical_json() == second.canonical_json()


def test_weights_and_reranker_valid_pair():
    config = load_nusantara_config(overrides={"rag": {"semantic_weight": 0.7, "lexical_weight": 0.3, "reranker_enabled": True, "reranker_model": "configured-reranker"}, "features": {"reranker": True}})
    assert config.rag.semantic_weight == 0.7


def test_no_commands_writes_database_or_engine_import(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("loader attempted a side effect")
    for name in ["run", "Popen", "call", "check_call", "check_output"]:
        monkeypatch.setattr(subprocess, name, forbidden)
    monkeypatch.setattr(os, "system", forbidden)
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    for name in ["write_text", "write_bytes", "mkdir", "unlink", "rename", "replace"]:
        monkeypatch.setattr(Path, name, forbidden)
    module_path = Path(__file__).parents[1] / "app/core/nusantara_config.py"
    source = module_path.read_text(encoding="utf-8")
    assert not any(f"from {prefix}" in source for prefix in ["app.api", "app.knowledge", "app.models", "app.main"])
    config = load_nusantara_config(project_root=tmp_path)
    assert config.knowledge.database == tmp_path / "data/knowledge/nusantara_knowledge.db"
