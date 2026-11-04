"""R2 invocation identity: isolated HTTP transports, no database or model workers."""
import asyncio
import ast
import dataclasses
import json
import os
import sys
import subprocess
from pathlib import Path

import httpx
import pytest

from app.core.nusantara_config import load_nusantara_config
from app.core.runtime_identity import BUILD_ID, capture_model_identity
from app.models.gateway import ModelGateway
from app.models.mock import MockProvider
from app.models.ollama import OllamaProvider
from app.models.openai_compatible import OpenAICompatibleProvider
from app.models.router import ModelRouter
from app.observability.context import request_context


def test_request_context_binds_distinct_invocations_to_one_instance():
    with request_context(request_id='http-r2-correlation'):
        first = capture_model_identity(provider_id='ollama', selected_model='selected')
        second = capture_model_identity(provider_id='ollama', selected_model='selected')
    standalone = capture_model_identity(provider_id='ollama', selected_model='selected')
    assert first.request_id == second.request_id == 'http-r2-correlation'
    assert first.request_id_source == second.request_id_source == 'REQUEST_CONTEXT'
    assert len({first.invocation_id, second.invocation_id, standalone.invocation_id}) == 3
    assert first.runtime_instance_id == second.runtime_instance_id == standalone.runtime_instance_id
    assert standalone.request_id == standalone.invocation_id
    assert standalone.request_id_source == 'STANDALONE'
    assert first.working_directory == os.getcwd()
    assert first.instance_captured_at <= first.timestamp


def test_runtime_instances_differ_in_real_subprocesses(tmp_path):
    script = ('import json; from app.core.runtime_identity import current_runtime_instance; '
              'from dataclasses import asdict; print(json.dumps(asdict(current_runtime_instance())))')
    environment = {**os.environ, 'PYTHONPATH': str(Path(__file__).parents[1])}
    observations = [json.loads(subprocess.check_output(
        [sys.executable, '-B', '-c', script], cwd=tmp_path, env=environment, text=True))
        for _ in range(2)]
    assert observations[0]['process_id'] != observations[1]['process_id']
    assert observations[0]['runtime_instance_id'] != observations[1]['runtime_instance_id']
    assert all(item['working_directory'] == str(tmp_path) for item in observations)


@pytest.mark.parametrize('change', [
    {'runtime_instance_id': None}, {'runtime_instance_id': 'foreign-instance'},
    {'process_id': -1}, {'invocation_id': ''},
])
def test_wrong_or_missing_instance_cannot_confirm_provider_response(change):
    receipt = capture_model_identity(provider_id='ollama', selected_model='selected')
    altered = dataclasses.replace(receipt, **change)
    assert altered.with_response('selected').identity_status == 'NOT_VERIFIED'


def test_stale_receipt_after_instance_change_is_not_confirmed(monkeypatch):
    import app.core.runtime_identity as owner
    receipt = capture_model_identity(provider_id='ollama', selected_model='selected')
    replacement = dataclasses.replace(owner.current_runtime_instance(), runtime_instance_id='new-instance')
    monkeypatch.setattr(owner, '_runtime_instance', replacement)
    assert receipt.with_response('selected').identity_status == 'NOT_VERIFIED'


def test_concurrent_generation_receipts_preserve_each_request_context():
    async def run():
        provider = OllamaProvider(model='selected')
        async def respond(request):
            await asyncio.sleep(0)
            return httpx.Response(200, json={'model': 'selected', 'done': True, 'response': 'answer'})
        provider._client = httpx.AsyncClient(base_url='http://fixture',
                                            transport=httpx.MockTransport(respond))
        async def generate(rid):
            with request_context(request_id=rid):
                return await provider.generate({'prompt': 'fixture'})
        try:
            return await asyncio.gather(generate('http-first'), generate('http-second'))
        finally:
            await provider.close()
    results = asyncio.run(run())
    receipts = [result['execution_identity'] for result in results]
    assert [r['request_id'] for r in receipts] == ['http-first', 'http-second']
    assert receipts[0]['invocation_id'] != receipts[1]['invocation_id']
    assert receipts[0]['runtime_instance_id'] == receipts[1]['runtime_instance_id']
    assert all(r['identity_status'] == 'RUNTIME_CONFIRMED' for r in receipts)


@pytest.mark.parametrize('incoming', ['http-fixture-id', 'invalid!id', ''])
def test_actual_http_middleware_binds_header_to_fixture_provider_receipt(incoming):
    import time
    from types import SimpleNamespace
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    source = Path(__file__).parents[1] / 'app/main.py'
    module = ast.parse(source.read_text(encoding='utf-8-sig'))
    middleware = next(node for node in module.body
                      if isinstance(node, ast.AsyncFunctionDef) and node.name == 'request_id_middleware')
    application = FastAPI()
    namespace = {'app': application, 'time': time, 'request_context': request_context,
                 'metrics': SimpleNamespace(incr=lambda *args: None, observe=lambda *args: None)}
    exec(compile(ast.Module(body=[middleware], type_ignores=[]), str(source), 'exec'), namespace)

    @application.get('/fixture-generation')
    async def generate():
        provider = OllamaProvider(model='selected')
        provider._client = httpx.AsyncClient(base_url='http://fixture', transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={'model': 'selected', 'done': True, 'response': 'answer'})))
        try:
            return (await provider.generate({'prompt': 'fixture'}))['execution_identity']
        finally:
            await provider.close()

    with TestClient(application) as client:
        response = client.get('/fixture-generation', headers={'X-Request-ID': incoming})
    assert response.status_code == 200
    receipt = response.json()
    assert receipt['request_id'] == response.headers['X-Request-ID']
    assert receipt['request_id_source'] == 'REQUEST_CONTEXT'
    assert receipt['runtime_instance_id'] and receipt['invocation_id'] != receipt['request_id']
    if incoming == 'http-fixture-id':
        assert receipt['request_id'] == incoming
    else:
        assert receipt['request_id'].startswith('req_')


@pytest.mark.parametrize('structured', [False, True])
@pytest.mark.parametrize('reported,done,status,result', [
    ('selected', True, 'RUNTIME_CONFIRMED', 'NOT_VERIFIED'),
    ('foreign', True, 'MISMATCH', 'MISMATCH'),
    (None, True, 'NOT_VERIFIED', 'NOT_VERIFIED'),
    ('selected', False, 'NOT_VERIFIED', 'NOT_VERIFIED'),
])
def test_generation_console_receipt_is_allowlisted_and_never_overall_verified(
        monkeypatch, structured, reported, done, status, result):
    events = []
    monkeypatch.setattr('app.models.ollama.log_event', lambda event, **fields: events.append((event, fields)))
    async def run():
        provider = OllamaProvider(model='selected')
        provider._client = httpx.AsyncClient(base_url='http://fixture', transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={'model': reported, 'done': done,
                'response': '{}' if structured else 'PRIVATE_RESPONSE'})))
        try:
            with request_context(request_id='http-telemetry'):
                method = provider.generate_structured if structured else provider.generate
                return await method({'prompt': 'PRIVATE_PROMPT', 'system': 'PRIVATE_SYSTEM'})
        finally:
            await provider.close()
    response = asyncio.run(run())
    event, fields = events[0]
    assert len(events) == 1 and event == 'provider_generation_identity'
    assert fields['request_id'] == 'http-telemetry'
    assert fields['identity_status'] == status and fields['result'] == result
    assert fields['invocation_id'] == response['execution_identity']['invocation_id']
    assert fields['runtime_instance_id'] == response['execution_identity']['runtime_instance_id']
    assert set(fields) == {'request_id', 'request_id_source', 'invocation_id', 'runtime_instance_id',
        'timestamp', 'instance_captured_at', 'build_id', 'process_id', 'provider_id',
        'configured_model', 'effective_model', 'selected_model', 'payload_model',
        'actual_model', 'identity_status', 'confirmation_source', 'result'}
    serialized = json.dumps(fields)
    assert all(secret not in serialized for secret in (
        'PRIVATE_PROMPT', 'PRIVATE_SYSTEM', 'PRIVATE_RESPONSE', sys.executable, os.getcwd()))


@pytest.mark.parametrize('structured', [False, True])
@pytest.mark.parametrize('failure', ['provider', 'model', 'connection'])
def test_failed_generation_logs_error_without_private_details(monkeypatch, structured, failure):
    from app.exceptions import ProviderUnavailableError
    events = []
    monkeypatch.setattr('app.models.ollama.log_event', lambda event, **fields: events.append(fields))
    def respond(request):
        if failure == 'connection':
            raise httpx.ConnectError('PRIVATE_NETWORK_DETAIL', request=request)
        return httpx.Response(503 if failure == 'provider' else 404,
                              json={'error': 'PRIVATE_UPSTREAM_DETAIL'})
    async def run():
        provider = OllamaProvider(model='missing')
        provider._client = httpx.AsyncClient(base_url='http://fixture', transport=httpx.MockTransport(respond))
        try:
            with request_context(request_id='http-failure'):
                with pytest.raises(ProviderUnavailableError):
                    await (provider.generate_structured if structured else provider.generate)({'prompt': 'PRIVATE_PROMPT'})
        finally:
            await provider.close()
    asyncio.run(run())
    assert len(events) == 1 and events[0]['result'] == 'ERROR'
    assert events[0]['identity_status'] == 'NOT_VERIFIED' and events[0]['actual_model'] is None
    assert events[0]['request_id'] == 'http-failure'
    assert 'PRIVATE_' not in json.dumps(events)


def test_console_logging_failure_does_not_change_provider_response(monkeypatch):
    def unavailable_logger(*args, **kwargs):
        raise RuntimeError('logger unavailable')
    monkeypatch.setattr('app.models.ollama.log_event', unavailable_logger)
    async def run():
        provider = OllamaProvider(model='selected')
        provider._client = httpx.AsyncClient(base_url='http://fixture', transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={'model': 'selected', 'done': True, 'response': 'answer'})))
        try:
            return await provider.generate({'prompt': 'fixture'})
        finally:
            await provider.close()
    assert asyncio.run(run())['content'] == 'answer'


def config():
    return load_nusantara_config(environment={'LLM_MODEL': 'configured'})


@pytest.mark.parametrize('reported,completed,status', [
    ('selected', True, 'RUNTIME_CONFIRMED'), ('foreign', True, 'MISMATCH'),
    (None, True, 'NOT_VERIFIED'), ('selected', False, 'NOT_VERIFIED'),
    ('', True, 'NOT_VERIFIED'), (17, True, 'NOT_VERIFIED'),
])
def test_response_identity_never_invents_actual_model(reported, completed, status):
    before = capture_model_identity(provider_id='ollama', selected_model='selected', configuration=config())
    after = before.with_response(reported, completed=completed)
    assert before.actual_model is None
    assert after.identity_status == status
    assert after.build_id == BUILD_ID
    assert after.process_id == os.getpid() and after.executable == sys.executable
    assert after.configuration_source == 'ENV'
    assert after.configured_model == after.effective_model == 'configured'
    assert after.selected_model == after.payload_model == 'selected'
    assert after.configuration_fingerprint
    with pytest.raises(dataclasses.FrozenInstanceError):
        before.payload_model = 'other'


@pytest.mark.parametrize('structured', [False, True])
def test_ollama_capture_precedes_await_and_survives_mutation(structured):
    provider = OllamaProvider(nusantara_config=config(), model='selected', model_source='REQUEST_OVERRIDE')
    seen = []
    def respond(request):
        payload = json.loads(request.content)
        seen.append(payload)
        return httpx.Response(200, json={'model': payload['model'], 'done': True,
                                        'response': '{}' if structured else 'answer'})
    async def run():
        client = httpx.AsyncClient(base_url='http://fixture', transport=httpx.MockTransport(respond))
        async def get_client():
            provider.model_name = 'changed-during-await'
            return client
        provider._get_client = get_client
        try:
            return await (provider.generate_structured({'prompt': 'fixture'}) if structured else
                          provider.generate({'prompt': 'fixture'}))
        finally:
            await client.aclose()
    result = asyncio.run(run())
    receipt = result['execution_identity']
    assert seen[0]['model'] == result['model'] == receipt['payload_model'] == 'selected'
    assert receipt['actual_model'] == 'selected'
    assert receipt['override_source'] == 'REQUEST_OVERRIDE'
    assert receipt['configured_model'] == 'configured'
    assert receipt['identity_status'] == 'RUNTIME_CONFIRMED'


@pytest.mark.parametrize('model,source', [(None, 'CONFIGURATION'), ('llama3.2:1b', 'EXPLICIT_CONSTRUCTOR')])
def test_omitted_and_default_equal_explicit_models_keep_distinct_sources(model, source):
    provider = OllamaProvider(model=model, nusantara_config=config())
    receipt = provider._capture_identity()
    assert receipt.override_source == source
    assert receipt.requested_model == model
    assert receipt.payload_model == ('configured' if model is None else model)
    assert receipt.actual_model is None


@pytest.mark.parametrize('structured,fallback', [(False, False), (True, False), (True, True)])
def test_openai_compatible_retains_upstream_identity_and_format_fallback(structured, fallback):
    provider = OpenAICompatibleProvider(model='selected')
    provider._supports_json_schema = lambda: not fallback
    seen = []
    def respond(request):
        seen.append(json.loads(request.content))
        provider.model_name = 'changed-after-payload'
        return httpx.Response(200, json={'model': 'selected',
            'choices': [{'message': {'content': '{}'}, 'finish_reason': 'stop'}]})
    async def run():
        provider._client = httpx.AsyncClient(base_url='http://fixture', transport=httpx.MockTransport(respond))
        try:
            return await (provider.generate_structured({'prompt': 'fixture', 'schema': {'type': 'object'}})
                          if structured else provider.generate({'prompt': 'fixture'}))
        finally:
            await provider.close()
    result = asyncio.run(run())
    assert seen[0]['model'] == result['model'] == result['execution_identity']['actual_model'] == 'selected'
    assert result['execution_identity']['fallback_status'] == 'NOT_ATTEMPTED'
    if fallback:
        assert result['execution_identity']['format_fallback'] == 'TEXT_JSON'


@pytest.mark.parametrize('kind', ['ollama', 'compatible'])
def test_inventory_health_is_not_execution_proof_and_preserves_schema(kind):
    provider = OllamaProvider(model='selected') if kind == 'ollama' else OpenAICompatibleProvider(model='selected')
    def respond(request):
        provider.model_name = 'changed-during-health'
        return httpx.Response(200, json={'models': [{'name': 'selected'}]} if kind == 'ollama'
                              else {'data': [{'id': 'selected'}]})
    async def run():
        provider._client = httpx.AsyncClient(base_url='http://fixture', transport=httpx.MockTransport(respond))
        try:
            return await provider.health_check()
        finally:
            await provider.close()
    health = asyncio.run(run())
    assert set(health) == {'status', 'model', 'available', 'latency_ms'}
    assert health['model'] == 'selected' and health['available']
    assert provider.last_health_identity['actual_model'] is None
    assert provider.last_health_identity['identity_status'] == 'NOT_VERIFIED'
    assert provider.last_health_identity['confirmation_source'] == 'MODEL_INVENTORY_ONLY'


def test_selection_is_immutable_and_provider_registry_drift_is_detected():
    provider = MockProvider()
    router = ModelRouter().register(provider)
    selection = router.route()
    with pytest.raises(dataclasses.FrozenInstanceError):
        selection.model_name = 'other'
    provider.provider_name = 'renamed'
    with pytest.raises(RuntimeError, match='registry identity drift'):
        router.route()
    with pytest.raises(RuntimeError, match='binding drift'):
        selection.assert_current_binding()


def test_gateway_keeps_selection_reason_and_receipt_binding():
    provider = OllamaProvider(model='selected')
    gateway = ModelGateway(ModelRouter().register(provider))
    async def run():
        provider._client = httpx.AsyncClient(base_url='http://fixture', transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={'model': 'selected', 'done': True, 'response': 'answer'})))
        try:
            return await gateway.generate({'prompt': 'fixture'})
        finally:
            await provider.close()
    result = asyncio.run(run())
    receipt = result['execution_identity']
    assert receipt['selected_provider'] == 'ollama'
    assert receipt['selection_reason']
    assert receipt['failover_status'] == 'NOT_ATTEMPTED'
    assert receipt['identity_status'] == 'RUNTIME_CONFIRMED'


def test_gateway_does_not_silently_failover_or_rewrite_foreign_receipt():
    class Foreign(MockProvider):
        def generate(self, request):
            return {'content': 'answer', 'execution_identity': {'provider_id': 'foreign', 'payload_model': 'foreign'}}
    with pytest.raises(RuntimeError, match='receipt binding mismatch'):
        asyncio.run(ModelGateway(ModelRouter().register(Foreign())).generate({'prompt': 'fixture'}))
    class Unavailable(MockProvider):
        def generate(self, request):
            raise RuntimeError('fixture unavailable')
    with pytest.raises(RuntimeError, match='fixture unavailable'):
        asyncio.run(ModelGateway(ModelRouter().register(Unavailable())).generate({'prompt': 'fixture'}))


def test_public_request_response_models_and_routes_unchanged():
    root = Path(__file__).parents[1]
    baseline = root / '.dev/checkpoints/r2-20261007/source-before'
    for name in ['app/api/routes.py', 'app/api/v2_routes.py']:
        def surface(path):
            module = ast.parse(path.read_text(encoding='utf-8-sig'))
            current = path == root/name
            approved = ast.parse('''class Approved:
    request_id: str | None = Field(default=None, pattern="^[a-f0-9]{32}$")
    retry_of: str | None = Field(default=None, pattern="^[a-f0-9]{32}$")
    document_ids: list[str] = Field(default_factory=list, max_length=20)
''').body[0]
            approved_fields = {field.target.id: field for field in approved.body}
            token_args = ast.parse('def allowed(x_admin_token: str | None = Header(default=None)): pass').body[0].args
            for node in module.body:
                if current and isinstance(node, ast.ClassDef) and node.name == 'ChatRequest':
                    retained = []
                    for field in node.body:
                        key = field.target.id if isinstance(field, ast.AnnAssign) else None
                        if key in approved_fields:
                            assert ast.dump(field) == ast.dump(approved_fields[key])
                            continue
                        if key == 'session_id':
                            expected = ast.parse("Field(default_factory=lambda: f'web-{uuid4()}', min_length=1, max_length=128)", mode='eval').body
                            assert ast.dump(field.value) == ast.dump(expected)
                            field.value = ast.parse("Field(default='web', min_length=1, max_length=128)", mode='eval').body
                        retained.append(field)
                    assert approved_fields.keys() <= {field.target.id for field in node.body if isinstance(field, ast.AnnAssign)}
                    node.body = retained
                if current and name == 'app/api/routes.py' and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {
                    'chat', 'search_knowledge', 'list_knowledge_documents'}:
                    assert ast.dump(node.args.args[-1]) == ast.dump(token_args.args[0])
                    assert ast.dump(node.args.defaults[-1]) == ast.dump(token_args.defaults[0])
                    node.args.args.pop()
                    node.args.defaults.pop()
            history = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'chat_history']
            if current and name == 'app/api/routes.py':
                assert len(history) == 1
                assert ast.unparse(history[0].decorator_list[0]) == "router.get('/chat/history')"
                expected = ast.parse("def history(x_chat_session: str = Header(default=''), x_admin_token: str | None = Header(default=None)): pass").body[0]
                assert ast.dump(history[0].args) == ast.dump(expected.args)
                module.body.remove(history[0])
            # Explicitly checked P0/idempotency additions above and the provider
            # enum below are authorized; every unaffected surface stays pinned.
            for node in module.body:
                if isinstance(node, ast.ClassDef) and node.name == '_PublicChatResponse':
                    for field in node.body:
                        if (isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name)
                            and field.target.id == 'provider_status'
                            and isinstance(field.annotation, ast.Subscript)
                            and isinstance(field.annotation.slice, ast.Tuple)):
                            field.annotation.slice.elts = [value for value in field.annotation.slice.elts
                                if not (isinstance(value, ast.Constant) and value.value == 'openrouter')]
            classes = [ast.dump(node) for node in module.body if isinstance(node, ast.ClassDef)]
            routes = [(node.name, ast.dump(node.args), [ast.dump(d) for d in node.decorator_list])
                      for node in module.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                              and isinstance(d.func.value, ast.Name) and d.func.value.id == 'router'
                              for d in node.decorator_list)]
            return classes, routes
        assert surface(root/name) == surface(baseline/name)


def _health_endpoint_client(source, provider):
    """Execute the actual endpoint AST without importing database/worker owners."""
    from types import SimpleNamespace
    from fastapi import APIRouter, FastAPI
    from fastapi.testclient import TestClient

    module = ast.parse(source.read_text(encoding='utf-8-sig'))
    endpoint = next(node for node in module.body
                    if isinstance(node, ast.AsyncFunctionDef) and node.name == 'health_detail')
    namespace = {
        'router': APIRouter(prefix='/v1'), 'OllamaProvider': provider,
        '_configuration': config(), 'BUILD_ID': BUILD_ID,
        'settings': SimpleNamespace(app_name='fixture-service', app_version='fixture-version'),
    }
    exec(compile(ast.Module(body=[endpoint], type_ignores=[]), str(source), 'exec'), namespace)
    app = FastAPI()
    app.include_router(namespace['router'])
    return TestClient(app)


@pytest.mark.parametrize('status,available', [
    ('ok', True), ('degraded', False), ('unavailable', False),
])
def test_public_health_distinguishes_inventory_identity_and_preserves_legacy_fields(status, available):
    root = Path(__file__).parents[1]
    instances = []

    class Provider:
        name = 'ollama'

        def __init__(self, *, nusantara_config):
            self.closed = False
            self.configuration = nusantara_config
            # Private state is deliberately untrusted and must never be projected.
            self.last_health_identity = {'actual_model': 'fabricated',
                'identity_status': 'RUNTIME_CONFIRMED', 'executable': 'PRIVATE_PATH',
                'api_key': 'PRIVATE_SECRET', 'build_id': 'forged'}
            instances.append(self)

        async def health_check(self):
            return {'status': status, 'available': available,
                    'model': self.configuration.llm.model, 'latency_ms': 12}

        async def close(self):
            self.closed = True

    prior = root / '.dev/checkpoints/r2-20261007/health-gate/source-before/app/api/routes.py'
    with _health_endpoint_client(prior, Provider) as client:
        old = client.get('/v1/health/detail')
    with _health_endpoint_client(root/'app/api/routes.py', Provider) as client:
        new = client.get('/v1/health/detail')
    assert old.status_code == new.status_code == 200
    before, after = old.json(), new.json()
    identity = after.pop('identity')
    assert after == before
    assert set(identity) == {'service', 'provider', 'model', 'build',
                             'verification_state', 'confirmation_source'}
    assert identity['service']['status'] == 'ok'
    assert identity['provider'] == {'name': 'ollama', 'status': status,
                                    'verification_state': 'HEALTH_PROBE_ONLY'}
    assert identity['model']['configured'] == identity['model']['effective'] == 'configured'
    assert identity['model']['selected'] == 'configured'
    assert identity['model']['source'] == 'ENV'
    assert identity['model']['payload'] is identity['model']['actual'] is None
    assert identity['model']['verification_state'] == identity['verification_state'] == 'NOT_VERIFIED'
    assert identity['build'] == {'id': BUILD_ID, 'verification_state': 'SOURCE_SNAPSHOT'}
    assert identity['confirmation_source'] == ('NONE' if status == 'unavailable'
                                               else 'MODEL_INVENTORY_ONLY')
    serialized = json.dumps(identity)
    assert all(secret not in serialized for secret in
               ['PRIVATE_PATH', 'PRIVATE_SECRET', 'fabricated', 'forged', 'executable', 'api_key'])
    assert all(provider.closed for provider in instances)
