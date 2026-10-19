"""V1 operator selection, actual Hermes execution and legacy boundary contracts.

HTTP checks run in the explicitly guarded composition recorded with the evidence.
"""
import asyncio
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.core.nusantara_config import ConfigurationError


def isolated_owner(tmp_path, workers=1):
    owner = Settings(_env_file=None)
    owner.compose_configuration(project_root=tmp_path, environment={}, dotenv_environment={},
        overrides={'llm': {'model': 'fixture-a'}, 'runtime': {'workers': workers}})
    return owner


def test_model_replacement_is_atomic_and_old_snapshot_remains_valid(tmp_path):
    owner = isolated_owner(tmp_path)
    original, revision = owner.configuration_snapshot()
    replacement, revision2 = owner.select_operator_model('fixture-b', expected_revision=revision,
                                                        validated_configuration=original)
    assert revision2 == revision + 1
    assert original.llm.model == 'fixture-a'
    assert replacement.llm.model == owner.llm_model == 'fixture-b'
    assert replacement.rag is original.rag and replacement.knowledge is original.knowledge
    assert owner.configuration_snapshot() == (replacement, revision2)
    assert owner.model_control_status()['selection_source'] == 'OPERATOR'
    with pytest.raises(ConfigurationError, match='CONFLICT'):
        owner.select_operator_model('fixture-a', expected_revision=revision, validated_configuration=original)
    assert owner.configuration_snapshot() == (replacement, revision2)


@pytest.mark.parametrize('model', ['', 'bad model', '\nsecret', 'x'*257])
def test_invalid_selection_leaves_owner_unchanged(tmp_path, model):
    owner = isolated_owner(tmp_path)
    snapshot, revision = owner.configuration_snapshot()
    with pytest.raises(ConfigurationError):
        owner.select_operator_model(model, expected_revision=revision, validated_configuration=snapshot)
    assert owner.configuration_snapshot() == (snapshot, revision)


def test_multiple_workers_are_not_claimed_as_globally_consistent(tmp_path):
    owner = isolated_owner(tmp_path, workers=2)
    snapshot, revision = owner.configuration_snapshot()
    assert not owner.model_control_status()['selection_enabled']
    with pytest.raises(ConfigurationError, match='SINGLE_NORMAL_WORKER'):
        owner.select_operator_model('fixture-b', expected_revision=revision, validated_configuration=snapshot)


def test_operator_provider_switch_is_process_local_and_restores_openrouter_bootstrap(tmp_path):
    owner = Settings(_env_file=None)
    owner.compose_configuration(project_root=tmp_path, environment={}, dotenv_environment={},
        overrides={'llm': {'provider': 'openrouter', 'base_url': 'https://openrouter.ai/api/v1',
                           'model': 'openai/gpt-4o-mini'}})
    original, revision = owner.configuration_snapshot()
    local = owner.configuration_for_operator_provider('ollama')
    assert local.llm.provider == 'ollama'
    assert local.llm.base_url == 'http://127.0.0.1:11434'
    assert local.llm.connection_timeout_s == 240.0
    assert original.llm.provider == 'openrouter'
    selected, next_revision = owner.select_operator_runtime('ollama', 'qwen2.5:7b',
        expected_revision=revision, validated_configuration=original)
    assert (selected.llm.provider, selected.llm.model) == ('ollama', 'qwen2.5:7b')
    assert next_revision == revision + 1
    restored, revision = owner.select_operator_runtime('openrouter', 'openai/gpt-4o-mini',
        expected_revision=next_revision, validated_configuration=selected)
    assert (restored.llm.provider, restored.llm.model, restored.llm.base_url) == (
        'openrouter', 'openai/gpt-4o-mini', 'https://openrouter.ai/api/v1')
    assert revision == next_revision + 1


@pytest.fixture
def controlled_client(monkeypatch, tmp_path):
    from app.main import app
    from app.api import routes
    from app.memory.engine import MemoryEngine
    from app.models.ollama import OllamaProvider
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'isolated-operator-fixture')
    owner = isolated_owner(tmp_path)
    monkeypatch.setattr(routes, 'settings', owner)
    monkeypatch.setattr(app.state, 'configuration_owner', owner)
    monkeypatch.setattr(app.state, 'effective_configuration', owner.configuration_snapshot()[0])
    monkeypatch.setattr(routes._gate_integration, 'memory', MemoryEngine(storage_root=tmp_path / 'history'))
    monkeypatch.setattr(routes._knowledge, 'search_knowledge', lambda *args, **kwargs: [])
    async def unavailable(self):
        return {'available': False, 'status': 'OFFLINE', 'model': self.model, 'latency_ms': 0}
    monkeypatch.setattr(OllamaProvider, 'health_check', unavailable)
    # No lifespan: do not start the production ingestion watcher in fixture tests.
    client = TestClient(app, base_url='http://127.0.0.1:8000', client=('127.0.0.1', 50111))
    try:
        yield client
    finally:
        client.close()


def test_operator_model_is_used_by_real_hermes_and_public_projection(controlled_client, monkeypatch):
    import app.api.control_plane as control
    async def fixture_inventory(configuration):
        return ['fixture-a', 'fixture-b']
    monkeypatch.setattr(control, '_available_model_names', fixture_inventory)
    from app.api import routes
    from app.knowledge.schemas import Evidence, RetrievalEvidenceList

    fixture_evidence = Evidence(
        document_id="FIXTURE-NOT-OFFICIAL",
        title="Fixture KTP-el",
        source="isolated-test-fixture",
        chunk="KTP-el adalah Kartu Tanda Penduduk elektronik yang digunakan sebagai identitas resmi penduduk Indonesia.",
        chunk_id="FIXTURE-CHUNK-001",
        chunk_index=0,
        start_char=0,
        end_char=105,
        metadata={},
        score=0.95,
    )
    monkeypatch.setattr(
        routes._knowledge,
        "search_knowledge",
        lambda *args, **kwargs: RetrievalEvidenceList([fixture_evidence]),
    )
    from app.hermes.agent import HermesAgent
    called = []
    original = HermesAgent.run
    def observed(self, *args, **kwargs):
        called.append(self.provider.model)
        return original(self, *args, **kwargs)
    monkeypatch.setattr(HermesAgent, 'run', observed)
    client = controlled_client
    token = {'X-Admin-Token': 'isolated-operator-fixture'}
    inventory = client.get('/v1/control-plane/models', headers=token)
    assert inventory.status_code == 200 and 'fixture-b' in inventory.json()['models']
    before = client.get('/v1/control-plane/model-status').json()
    changed = client.post('/v1/control-plane/model-selection', headers=token,
        json={'model': 'fixture-b', 'expected_revision': before['revision']})
    assert changed.status_code == 200 and changed.json()['change_status'] == 'APPLIED'
    from app.models.ollama import OllamaProvider
    seen = []

    async def fixture_health_check(self):
        return {
            "status": "ok",
            "model": self.model,
            "available": True,
            "latency_ms": 0,
        }

    async def fixture_generate(self, payload):
        identity = self._capture_identity().safe_dump()
        result = {
            "content": (
                "KTP-el adalah Kartu Tanda Penduduk elektronik "
                "yang digunakan sebagai identitas resmi penduduk Indonesia."
            ),
            "model": self.model,
            "tokens_used": 0,
            "latency_ms": 0,
            "execution_identity": identity,
        }
        seen.append((self.model, identity["payload_model"]))
        return result

    monkeypatch.setattr(OllamaProvider, "health_check", fixture_health_check)
    monkeypatch.setattr(OllamaProvider, "generate", fixture_generate)
    session = 'operator-memory-preservation'
    existing = list(routes._gate_integration.memory.context(session))
    answer = client.post('/v1/chat', json={'user_input': 'Apa itu KTP-el?', 'session_id': session})
    assert answer.status_code == 200
    data = answer.json()
    assert data['model'] == 'fixture-b' and data['provider_status'] == 'ollama'
    assert called == ['fixture-b'] and seen == [('fixture-b', 'fixture-b')]
    assert data['grounding']['grounded']
    assert 'gate_pipeline' not in data and 'reasoning' not in data
    assert data['evidence'][0]['document_id'] == 'FIXTURE-NOT-OFFICIAL'
    history = routes._gate_integration.memory.context(session)
    assert len(history) == len(existing) + 2
    assert history[-2]['role'] == 'user' and history[-1]['role'] == 'assistant'
    diagnostic = client.get('/v1/control-plane/model-status').json()['last_request']
    assert diagnostic['model'] == 'fixture-b' and 'HERMES_RUN' in diagnostic['stages']
    assert 'PUBLIC_PROJECTION' in diagnostic['stages']


def test_ollama_inventory_and_chat_use_selected_qwen_without_openrouter(controlled_client, monkeypatch, tmp_path):
    import app.api.control_plane as control
    from app.main import app
    from app.api import routes
    from app.models.ollama import OllamaProvider
    from app.models.openrouter import OpenRouterProvider

    owner = Settings(_env_file=None)
    owner.compose_configuration(project_root=tmp_path, environment={}, dotenv_environment={},
        overrides={'llm': {'provider': 'openrouter', 'base_url': 'https://openrouter.ai/api/v1',
                           'model': 'openai/gpt-4o-mini'}})
    monkeypatch.setattr(routes, 'settings', owner)
    monkeypatch.setattr(app.state, 'configuration_owner', owner)
    monkeypatch.setattr(app.state, 'effective_configuration', owner.configuration_snapshot()[0])

    inventory_calls = []
    async def inventory(self):
        inventory_calls.append((self._configuration.llm.provider, self.base_url))
        return [{'name': 'qwen2.5:7b'}, {'name': 'llama3.2:1b'}]
    monkeypatch.setattr(OllamaProvider, 'list_models', inventory)
    token = {'X-Admin-Token': 'isolated-operator-fixture'}
    models = controlled_client.get('/v1/control-plane/models?provider=ollama', headers=token)
    assert models.status_code == 200
    assert models.json()['models'] == ['llama3.2:1b', 'qwen2.5:7b']
    assert models.json()['provider'] == 'ollama'
    assert inventory_calls == [('ollama', 'http://127.0.0.1:11434')]

    before = controlled_client.get('/v1/control-plane/model-status').json()
    applied = controlled_client.post('/v1/control-plane/model-selection', headers=token,
        json={'provider': 'ollama', 'model': 'qwen2.5:7b', 'expected_revision': before['revision']})
    assert applied.status_code == 200
    assert (applied.json()['provider'], applied.json()['model']) == ('ollama', 'qwen2.5:7b')

    local_calls = []
    async def local_health(self):
        return {'status': 'ok', 'model': self.model, 'available': True, 'latency_ms': 1}
    async def local_generate(self, payload):
        local_calls.append((self.name, self.model))
        return {'content': 'Jawaban dari Qwen lokal.', 'model': self.model,
                'tokens_used': 0, 'latency_ms': 1,
                'execution_identity': self._capture_identity().safe_dump()}
    async def no_openrouter(*args, **kwargs):
        pytest.fail('Ollama chat must not dispatch through OpenRouter')
    monkeypatch.setattr(OllamaProvider, 'health_check', local_health)
    monkeypatch.setattr(OllamaProvider, 'generate', local_generate)
    monkeypatch.setattr(OpenRouterProvider, 'generate', no_openrouter)
    answer = controlled_client.post('/v1/chat', json={'user_input': 'Jelaskan layanan PIAK-03 secara umum.'})
    assert answer.status_code == 200
    assert answer.json()['provider_status'] == 'ollama'
    assert answer.json()['model'] == 'qwen2.5:7b'
    assert local_calls == [('ollama', 'qwen2.5:7b')]

    from app.exceptions import ProviderUnavailableError
    async def local_failure(self, payload):
        raise ProviderUnavailableError('ollama')
    monkeypatch.setattr(OllamaProvider, 'generate', local_failure)
    failed = controlled_client.post('/v1/chat', json={
        'user_input': 'Explain this local service briefly.', 'session_id': 'ollama-no-cloud-fallback'})
    assert failed.status_code == 503


def test_ollama_inventory_failure_does_not_change_provider_selection(controlled_client, monkeypatch, tmp_path):
    import app.api.control_plane as control
    from app.main import app
    from app.api import routes
    from app.models.ollama import OllamaProvider
    owner = Settings(_env_file=None)
    owner.compose_configuration(project_root=tmp_path, environment={}, dotenv_environment={},
        overrides={'llm': {'provider': 'openrouter', 'base_url': 'https://openrouter.ai/api/v1',
                           'model': 'openai/gpt-4o-mini'}})
    monkeypatch.setattr(routes, 'settings', owner)
    monkeypatch.setattr(app.state, 'configuration_owner', owner)
    monkeypatch.setattr(app.state, 'effective_configuration', owner.configuration_snapshot()[0])
    async def unavailable(self):
        raise RuntimeError('local Ollama unavailable')
    monkeypatch.setattr(OllamaProvider, 'list_models', unavailable)
    token = {'X-Admin-Token': 'isolated-operator-fixture'}
    before = controlled_client.get('/v1/control-plane/model-status').json()
    result = controlled_client.post('/v1/control-plane/model-selection', headers=token,
        json={'provider': 'ollama', 'model': 'qwen2.5:7b', 'expected_revision': before['revision']})
    after = controlled_client.get('/v1/control-plane/model-status').json()
    assert result.status_code == 503
    assert (after['provider'], after['model'], after['revision']) == (
        before['provider'], before['model'], before['revision'])


@pytest.mark.parametrize('greeting', ['Hallo', 'Halo', 'Hai', 'Selamat pagi', '  HALLO!  '])
def test_standalone_greeting_is_nonfactual_local_response(controlled_client, monkeypatch, greeting):
    from app.api import routes
    from app.models.ollama import OllamaProvider
    from app.hermes.agent import HermesAgent
    monkeypatch.setattr(routes._knowledge, 'search_knowledge', lambda *args, **kwargs: [])
    calls = []
    original_run = HermesAgent.run
    def observed_run(self, *args, **kwargs):
        calls.append('hermes')
        return original_run(self, *args, **kwargs)
    monkeypatch.setattr(HermesAgent, 'run', observed_run)
    original_generate = OllamaProvider.generate
    async def observed_generate(self, payload):
        calls.append('provider')
        return await original_generate(self, payload)
    monkeypatch.setattr(OllamaProvider, 'generate', observed_generate)
    session = 'greeting-' + greeting.strip()
    data = controlled_client.post('/v1/chat', json={'user_input': greeting, 'session_id': session}).json()
    assert data['response'] == 'Halo! Ada yang bisa saya bantu?'
    assert data['provider_status'] == 'local_rule'
    assert data['understanding']['intent'] == 'greeting'
    assert calls == ['hermes']
    assert data['evidence'] == [] and not data['trust']['supports_claim']
    assert data['trust']['requires_human']  # No relaxation of trust assessment.
    assert data['grounding']['reason'] == 'deterministic_response'
    assert [turn['role'] for turn in routes._gate_integration.memory.context(session)] == ['user', 'assistant']
    assert 'gate_pipeline' not in data


@pytest.mark.parametrize('question', ['Hallo, apa syarat membuat KTP?', 'Halo apa biaya KTP?', 'Apa syaratnya?', 'Lalu berapa biayanya?'])
def test_substantive_and_followup_questions_never_take_greeting_shortcut(controlled_client, monkeypatch, question):
    from app.api import routes
    from app.models.ollama import OllamaProvider
    monkeypatch.setattr(routes._knowledge, 'search_knowledge', lambda *args, **kwargs: [])
    prompts = []
    async def fixture_health_check(self):
        return {
            "status": "ok",
            "model": self.model,
            "available": True,
            "latency_ms": 0,
        }
    async def fixture_generate(self, payload):
        prompts.append(payload["prompt"])
        return {
            "content": "Jawaban ini tidak didukung oleh evidence.",
            "model": self.model,
            "tokens_used": 0,
            "latency_ms": 0,
        }
    monkeypatch.setattr(OllamaProvider, "health_check", fixture_health_check)
    monkeypatch.setattr(OllamaProvider, "generate", fixture_generate)
    data = controlled_client.post('/v1/chat', json={'user_input': question, 'session_id': 'followup-regression'}).json()
    assert not data['grounding']['grounded']
    if question=='Apa syaratnya?':
        assert data['provider_status']=='local_rule'
        assert data['response']=='Layanan apa yang Anda maksud?'
        assert not data['evidence'] and prompts==[]
    else:
        assert data['provider_status'] == 'ollama'
        assert data['response'] == 'Informasi tersebut belum tersedia secara cukup dalam knowledge base.'
        assert len(prompts) == 1 and question in prompts[0]


def test_auth_unavailable_failure_and_conflict_never_change_selection(controlled_client, monkeypatch):
    import app.api.control_plane as control

    async def fixture_inventory(configuration):
        return ['fixture-a', 'fixture-b']

    monkeypatch.setattr(control, '_available_model_names', fixture_inventory)
    client = controlled_client
    path = '/v1/control-plane/model-selection'
    before = client.get('/v1/control-plane/model-status').json()
    payload = {'model': 'fixture-a', 'expected_revision': before['revision']}
    assert client.post(path, json=payload).status_code == 403
    assert client.get('/v1/control-plane/models').status_code == 403
    token = {'X-Admin-Token': 'isolated-operator-fixture'}
    assert client.post(path, headers=token, json={**payload, 'model': 'not-installed'}).status_code == 422
    assert client.post(path, headers=token, json={**payload, 'expected_revision': before['revision']+1}).status_code == 409
    import app.api.control_plane as control
    async def unavailable(*args):
        from fastapi import HTTPException
        raise HTTPException(503, 'MODEL_INVENTORY_UNAVAILABLE')
    monkeypatch.setattr(control, '_available_model_names', unavailable)
    assert client.post(path, headers=token, json=payload).status_code == 503
    after = client.get('/v1/control-plane/model-status').json()
    assert (after['model'], after['revision']) == (before['model'], before['revision'])
    assert client.post('/v1/chat', json={'user_input': 'hello', 'model': 'not-active'}).status_code == 409


def test_unsupported_knowledge_filter_is_rejected_before_retrieval(controlled_client):
    from app.knowledge.engine import KnowledgeEngine
    class MustNotRun:
        def query(self, **kwargs):
            pytest.fail('unsupported source restriction reached unrestricted retrieval')
    with pytest.raises(ValueError, match='FILTER_NOT_SUPPORTED'):
        KnowledgeEngine(rag=MustNotRun()).search_knowledge('query', filter={'authority': 'official'})
    assert controlled_client.post('/v1/knowledge/search', json={'query': 'query', 'filter': {'authority': 'official'}}).status_code == 422


def test_model_change_during_request_does_not_rebind_its_provider(controlled_client, monkeypatch):
    from app.api import routes
    from app.models.ollama import OllamaProvider
    owner = routes.settings
    current, revision = owner.configuration_snapshot()
    original = OllamaProvider.health_check
    async def concurrent_change(self):
        owner.select_operator_model('fixture-a' if current.llm.model != 'fixture-a' else 'fixture-b',
            expected_revision=revision, validated_configuration=current)
        return await original(self)
    monkeypatch.setattr(OllamaProvider, 'health_check', concurrent_change)
    response = controlled_client.post('/v1/chat', json={'user_input': 'Apa itu KTP-el?', 'session_id': 'in-flight'})
    assert response.status_code == 200
    assert response.json()['model'] == current.llm.model
    assert owner.configuration_snapshot()[0].llm.model != current.llm.model


def test_inventory_race_fails_cas_without_applying_stale_operator_choice(controlled_client, monkeypatch):
    from app.api import routes
    import app.api.control_plane as control
    current, revision = routes.settings.configuration_snapshot()
    target = 'fixture-a' if current.llm.model != 'fixture-a' else 'fixture-b'
    async def raced_inventory(configuration):
        routes.settings.select_operator_model(current.llm.model, expected_revision=revision,
                                               validated_configuration=current)
        return ['fixture-a', 'fixture-b']
    monkeypatch.setattr(control, '_available_model_names', raced_inventory)
    result = controlled_client.post('/v1/control-plane/model-selection',
        headers={'X-Admin-Token': 'isolated-operator-fixture'},
        json={'model': target, 'expected_revision': revision})
    assert result.status_code == 409
    snapshot, effective_revision = routes.settings.configuration_snapshot()
    assert snapshot.llm.model == current.llm.model and effective_revision == revision + 1


def test_evidence_profile_external_origin_and_missing_admin_fail_closed(controlled_client, monkeypatch):
    from app.main import app
    assert controlled_client.get('/v1/control-plane/model-status', headers={'Origin': 'https://external.example'}).status_code == 403
    before = app.state.configuration_owner.configuration_snapshot()
    monkeypatch.delenv('NUSANTARA_ADMIN_TOKEN', raising=False)
    assert controlled_client.post('/v1/control-plane/model-selection',
        headers={'X-Admin-Token': 'isolated-operator-fixture'},
        json={'model': 'fixture-a', 'expected_revision': before[1]}).status_code == 403
    monkeypatch.setattr(app.state, 'configuration_owner', None)
    assert controlled_client.get('/v1/control-plane/model-status').status_code == 503



