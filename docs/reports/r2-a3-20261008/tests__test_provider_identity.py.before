"""R2 invocation identity: isolated HTTP transports, no database or model workers."""
import asyncio
import ast
import dataclasses
import json
import os
import sys
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
