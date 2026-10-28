"""Consumer integration with isolated stores/transports; no production access."""
import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from app.core.nusantara_config import ConfigurationError, load_nusantara_config
from app.models.ollama import OllamaProvider
from app.knowledge.engine import KnowledgeEngine
from app.knowledge.rag import RAG, MemoriaVectorStore, create_rag
from app.knowledge.schemas import KnowledgeBaseConfig
from app.knowledge.indobert_embedding import IndoBERTEmbeddingAdapter


def configured(tmp_path, **kwargs):
    return load_nusantara_config(project_root=tmp_path, overrides=kwargs)


def test_provider_payload_uses_snapshot_and_request_precedence(tmp_path):
    config = configured(tmp_path, llm={"model": "configured-model", "base_url": "http://127.0.0.1:12345", "connection_timeout_s": 9.0,
        "generation": {"context_length": 2048, "max_tokens": 100, "temperature": 0.3, "top_p": 0.8}})
    provider = OllamaProvider(nusantara_config=config)
    assert provider.timeout == 9
    assert provider.base_url == "http://127.0.0.1:12345"
    seen = []

    def respond(request):
        import json
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"response": "answer", "eval_count": 3})

    async def run():
        provider._client = httpx.AsyncClient(base_url=provider.base_url, transport=httpx.MockTransport(respond))
        try:
            response = await provider.generate({"prompt": "hello", "max_tokens": 50, "temperature": 0.6})
            assert response["content"] == "answer"
        finally:
            await provider.close()

    asyncio.run(run())
    assert seen[0]["model"] == "configured-model"
    assert seen[0]["options"] == {"num_ctx": 2048, "num_predict": 50, "temperature": 0.6, "top_p": 0.8}
    assert provider._options({})["num_predict"] == 100


def test_legacy_provider_and_explicit_nondefault_arguments(tmp_path, monkeypatch):
    import app.models.ollama as module
    monkeypatch.setattr(module.settings, "llm_context_tokens", 1024)
    legacy = OllamaProvider()
    assert legacy._options({}) == {"num_ctx": 1024, "num_predict": 512}
    config = configured(tmp_path, llm={"model": "snapshot-model"})
    explicit = OllamaProvider("http://localhost:1234", "explicit-model", 8.0, nusantara_config=config)
    assert (explicit.base_url, explicit.model_name, explicit.timeout) == ("http://localhost:1234", "explicit-model", 8.0)


def test_adapter_constructs_existing_client_without_starting_worker(tmp_path, monkeypatch):
    import app.knowledge.indobert_embedding as module
    seen = []
    class Client:
        def __init__(self, **kwargs):
            seen.append(kwargs)
        def encode(self, text):
            return {"ok": True, "embedding": [0.0] * 768}
    monkeypatch.setattr(module, "IndoBERTClient", Client)
    config = configured(tmp_path, embedding={"timeout_s": 12.0})
    adapter = IndoBERTEmbeddingAdapter(nusantara_config=config)
    assert seen == [{"python_executable": str(config.paths.worker_python), "worker_path": str(config.paths.worker), "response_timeout_s": 12.0}]
    assert len(adapter("text")) == 768


@pytest.mark.parametrize("embedding", [{"model": "uninstalled"}, {"dimension": 384}])
def test_incompatible_embedding_rejected_before_store_or_worker(tmp_path, monkeypatch, embedding):
    import app.knowledge.rag as module
    def forbidden(*args, **kwargs):
        pytest.fail("preflight attempted to initialize a store")
    monkeypatch.setattr(module, "SQLiteVectorStore", forbidden)
    with pytest.raises(ConfigurationError, match="EMBEDDING_PROFILE_UNSUPPORTED"):
        RAG(nusantara_config=configured(tmp_path, embedding=embedding))


@pytest.mark.parametrize("rag", [{"semantic_weight": 0.7, "lexical_weight": 0.3}, {"similarity_threshold": 0.5}])
def test_unwired_rag_parameters_not_silently_accepted(tmp_path, monkeypatch, rag):
    import app.knowledge.rag as module
    monkeypatch.setattr(module, "SQLiteVectorStore", lambda *a, **k: pytest.fail("store opened"))
    with pytest.raises(ConfigurationError, match="RAG_PARAMETER_NOT_INTEGRATED"):
        RAG(nusantara_config=configured(tmp_path, rag=rag))


def test_rag_actual_query_and_ingestion_use_config(tmp_path):
    config = configured(tmp_path, rag={"top_k": 2, "chunk_size": 80, "chunk_overlap": 10})
    class IsolatedStore(MemoriaVectorStore):
        # Complete the persisted-store protocol for this test fixture. The
        # legacy Memoria fallback does not implement these methods.
        def update_document_chunks_count(self, document_id, count):
            self._doc_info[document_id].chunks_count = count
        def search_lexical(self, query, top_k=20):
            return []
        def search_similarity(self, embedding, top_k=5):
            return [(chunk, score) for score, chunk in super().search_similarity(embedding, top_k)]
        def get_document_info(self, document_id):
            return self._doc_info.get(document_id)
    store = IsolatedStore()
    rag = create_rag(nusantara_config=config, vector_store=store)
    # Replace embedding without starting the actual worker. In-memory store is
    # explicitly supplied; no SQLite backend is touched.
    rag.set_embedding_func(lambda text: [1.0] * 768)
    from app.knowledge.schemas import DocumentIngestRequest
    response = rag.ingest_document(DocumentIngestRequest(title="Fixture", source="nusantara configuration " * 30, content_type="text/plain"))
    assert response.success
    assert rag._config.chunk_size == 80
    assert rag._config.chunk_overlap == 10
    result = rag.query("nusantara configuration")
    assert len(result.evidence_pack.evidence) == 2
    assert len(rag.query("nusantara", top_k=1).evidence_pack.evidence) == 1
    engine = KnowledgeEngine(rag=rag, nusantara_config=config)
    assert len(engine.search('nusantara configuration')) == 2
    assert len(engine.search('nusantara configuration', top_k=3)) == 3
    assert not (tmp_path / "data").exists()
    rag._embedding_adapter.stop()


def test_explicit_store_embedding_and_kb_config_preserved(tmp_path):
    config = configured(tmp_path, rag={"top_k": 2})
    store = MemoriaVectorStore()
    legacy_config = KnowledgeBaseConfig(retrieval_top_k=7)
    function = lambda text: [0.0] * 768
    rag = RAG(config=legacy_config, vector_store=store, embedding_func=function, nusantara_config=config)
    assert rag._store is store
    assert rag._embedding is function
    assert rag._config is legacy_config
    assert rag._config.retrieval_top_k == 7


def test_database_path_handoff_without_real_database(tmp_path, monkeypatch):
    import app.knowledge.rag as module
    seen = []
    def store(path):
        seen.append(path)
        return MemoriaVectorStore()
    monkeypatch.setattr(module, "SQLiteVectorStore", store)
    config = configured(tmp_path, knowledge={"database": "custom/knowledge.db"})
    rag = RAG(nusantara_config=config, embedding_func=lambda text: [0.0] * 768)
    assert seen == [str(tmp_path / "custom/knowledge.db")]
    assert isinstance(rag._store, MemoriaVectorStore)
    assert not (tmp_path / "custom").exists()


def test_knowledge_facade_preserves_omitted_and_explicit_topk(tmp_path, monkeypatch):
    import app.knowledge.engine as module
    config = configured(tmp_path, rag={"top_k": 3})
    seen = []
    class Fake:
        def query(self, **kwargs):
            seen.append(kwargs)
            return SimpleNamespace(evidence_pack=SimpleNamespace(evidence=[]))
    fake = Fake()
    def factory(**kwargs):
        assert kwargs == {"nusantara_config": config}
        return fake
    monkeypatch.setattr(module, "create_rag", factory)
    engine = KnowledgeEngine(nusantara_config=config)
    engine.search("question")
    engine.search("question", top_k=2)
    engine.search("question", top_k=5)
    assert [item["top_k"] for item in seen] == [None, 2, 5]
    assert KnowledgeEngine(rag=fake, nusantara_config=config).rag is fake


def test_r1_preserves_out_of_scope_protected_sources():
    import json
    root = Path(__file__).parents[1]
    baseline = json.loads((root / "reports/CONFIGURATION_BASELINE_20261006.json").read_text())
    assert baseline["status"] == "AUDIT_ONLY"
    checkpoint = json.loads((root / "reports/configuration/CONFIGURATION_PROGRESS.json").read_text())
    # API routes is now explicitly authorized for R1; its pre-change bytes must
    # still agree with the historical audit. Other protected code stays intact.
    r1 = json.loads((root / '.dev/checkpoints/r1-local-001-20261007/BASELINE.json').read_text(encoding='utf-8-sig'))
    before = {item['path']: item['before_sha256'] for item in r1['files']}
    assert before['app/api/routes.py'] == checkpoint['protected_hashes_before']['app/api/routes.py']
    for relative in ["app/developer_core/engine.py", "app/trust/engine.py", "app/policy/engine.py"]:
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == checkpoint["protected_hashes_before"][relative]


def test_guarded_api_assembly_and_public_regression(tmp_path):
    """Real API composition, fake persistence/semantic worker, no production I/O."""
    import os
    import subprocess
    import sys
    script = r'''
import os, pathlib, socket, sqlite3, subprocess
def forbidden(*args, **kwargs):
    raise AssertionError('Forbidden database/worker/network operation in R1 fixture')
sqlite3.connect = forbidden
subprocess.Popen = forbidden
socket.socket.connect = forbidden
import app.knowledge.rag as rag
rag.SQLiteVectorStore = lambda *a, **k: rag.MemoriaVectorStore()
import app.language.engine as language
language.SemanticIntentEngine = None
from app.core.config import settings
config = settings.compose_configuration(dotenv_environment={}, environment={},
    overrides={'llm': {'model': 'composed-fixture'}, 'rag': {'top_k': 3}})
from app.main import app
from app.api import routes, v2_routes
assert app.state.effective_configuration is config
assert routes._configuration is v2_routes._configuration is config
assert routes._knowledge.configuration is v2_routes._knowledge.configuration is config
assert routes._knowledge.rag._config.retrieval_top_k == 3
assert v2_routes._knowledge.rag._config.retrieval_top_k == 3
from app.models.ollama import OllamaProvider
assert OllamaProvider(nusantara_config=config).model == 'composed-fixture'
assert OllamaProvider(model='llama3.2:1b', nusantara_config=config).model == 'llama3.2:1b'
import pytest
raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider',
    '--basetemp=' + os.environ['R1_FIXTURE_ROOT'] + '/regression-tmp',
    '--junitxml=' + os.environ['R1_FIXTURE_REPORT'],
    'tests/test_v1_response_projection.py', 'tests/test_v1_stage_budget.py',
    'tests/test_runtime_identity.py']))
'''
    root = Path(__file__).parents[1]
    env = dict(os.environ, NUSANTARA_DATA_DIR=str(tmp_path / 'runtime'),
               R1_FIXTURE_ROOT=str(tmp_path), PYTHONDONTWRITEBYTECODE='1',
               R1_FIXTURE_REPORT=str(root / '.dev/checkpoints/r1-local-001-20261007/public-regression.xml'))
    result = subprocess.run([sys.executable, '-B', '-c', script], cwd=root, env=env,
                            text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
