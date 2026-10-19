"""Real provider code behind mock HTTP transports; no live application/provider request."""
import asyncio
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx
import pytest

from app.api.runtime_verification import install_runtime_verification, VERIFICATION_PATH
from app.core.nusantara_config import load_nusantara_config
from app.core.runtime_attestation import install_runtime_attestation, ATTESTATION_PATH
from app.models.ollama import OllamaProvider


def app_fixture(tmp_path, monkeypatch, *, model='fixture-model', responder=None):
    calls, factories = [], []
    def respond(request):
        calls.append(request)
        return responder(request) if responder else httpx.Response(200,
            json={'model': model, 'done': True, 'response': 'PRIVATE_TEST_RESPONSE'})
    def factory(**kwargs):
        factories.append(kwargs)
        return httpx.MockTransport(respond)
    monkeypatch.setattr(httpx, 'AsyncHTTPTransport', factory)
    config = load_nusantara_config(project_root=tmp_path, overrides={
        'runtime': {'profile': 'ATTESTATION'}, 'llm': {'model': model}})
    app = FastAPI()
    controller = install_runtime_verification(app, config)
    install_runtime_attestation(app, entrypoint='isolated:app')
    return app, controller, calls, factories


def session(app):
    return TestClient(app, base_url='http://127.0.0.1:8000', client=('127.0.0.1', 45000))


def headers(token):
    return {'Authorization': 'Bearer '+token, 'X-Request-ID': 'caller-owned-id'}


def test_receipt_assessment_missing_unbound_and_conflicting_storage(tmp_path, monkeypatch):
    from app.core.runtime_correlation import CorrelationReceipt
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch)
    assert not controller.receipt_assessment()['correlation_valid']
    receipt = CorrelationReceipt('request', 'invocation', 'fixture-instance', os.getpid(),
        'source', 'scoped', 'ollama', controller.endpoint, 'fixture-model',
        '2026-10-08T00:00:00+00:00', '2026-10-08T00:00:01+00:00',
        True, False, 1, 'PROVIDER_RESPONSE_CORRELATED')
    controller._store(receipt)  # Unverified server test context, no permit/provider.
    assert not controller.receipt_assessment()['correlation_valid']
    with pytest.raises(ValueError, match='CONFLICTING_RECEIPT'):
        controller._store(receipt)
    assert controller.receipt == receipt and not calls
    assert controller.authorization.state == 'DISARMED'
    assert controller.authorization.dispatch_count == 0


def test_receipt_assessment_controller_checks_current_os_code_and_fixture(tmp_path, monkeypatch):
    from dataclasses import replace
    from datetime import datetime, timedelta, timezone
    import app.api.runtime_verification as owner
    from app.core.runtime_correlation import CorrelationReceipt
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch)
    current = datetime.now(timezone.utc)
    stamp = current.isoformat()  # A valid fixture must not predate this process start.
    process = owner._process_identity()
    instance = owner.current_runtime_instance()
    receipt = CorrelationReceipt('request', 'invocation', instance.runtime_instance_id, os.getpid(),
        owner.BUILD_ID, controller._code_hash, 'ollama', controller.endpoint, 'fixture-model',
        stamp, stamp, True, False, 1, 'PROVIDER_RESPONSE_CORRELATED')
    # Synthetic trusted-context branch tests logic, not genuine provider evidence.
    controller._store(receipt, process_start=process['process_start_time'], evidence_class='PROVIDER_RESPONSE')
    assert controller.receipt_assessment()['correlation_valid'], controller.receipt_assessment()
    observer = controller._code_observer
    monkeypatch.setattr(controller, '_code_observer', lambda:'wrong-code')
    assert not controller.receipt_assessment()['correlation_valid']
    monkeypatch.setattr(controller, '_code_observer', observer)
    monkeypatch.setattr(owner, '_process_identity', lambda:{'process_start_time':'2020-01-01T00:00:00+00:00'})
    assert not controller.receipt_assessment()['correlation_valid']
    monkeypatch.setattr(owner, '_process_identity', lambda:process)
    monkeypatch.setattr(controller, '_receipt_observation', replace(controller._receipt_observation, evidence_class='TEST_ISOLATED'))
    assert not controller.receipt_assessment()['correlation_valid']
    assert not calls and controller.authorization.state == 'DISARMED'
    assert controller.authorization.dispatch_count == 0


def test_receipt_assessment_observer_failure_is_fail_closed(tmp_path, monkeypatch):
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch)
    def unavailable(): raise RuntimeError('PRIVATE_CONTEXT_FAILURE')
    monkeypatch.setattr(controller, '_code_observer', unavailable)
    result = controller.receipt_assessment()
    assert result['status'] == 'NOT_VERIFIED' and not result['correlation_valid']
    assert result['reason'] == 'CURRENT_CONTEXT_UNAVAILABLE'
    assert 'PRIVATE_CONTEXT_FAILURE' not in json.dumps(result)
    assert not calls and controller.authorization.state == 'DISARMED'


@pytest.mark.asyncio
async def test_receipt_assessment_send_success_failure_never_creates_provider_evidence(tmp_path, monkeypatch):
    from app.core.runtime_correlation import ResponseObservationMiddleware, CorrelationReceipt
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch)
    receipt = CorrelationReceipt('request', 'invocation', 'fixture', os.getpid(),
        'source', 'scoped', 'ollama', controller.endpoint, 'fixture-model',
        'start', 'complete', True, False, 1, 'PROVIDER_RESPONSE_CORRELATED')
    controller._store(receipt, evidence_class='TEST_ISOLATED')
    async def response_app(scope, receive, send):
        await send({'type':'http.response.start','status':200,'headers':[(b'x-request-id',b'request')]})
        await send({'type':'http.response.body','body':b'','more_body':False})
    async def failed_send(message):
        if message['type']=='http.response.body': raise RuntimeError('isolated-send-failed')
    async def sent(message): pass
    wrapped = ResponseObservationMiddleware(response_app, controller)
    scope={'type':'http','path':VERIFICATION_PATH}
    with pytest.raises(RuntimeError): await wrapped(scope, None, failed_send)
    assert not controller.receipt.application_response_sent
    await wrapped(scope, None, sent)
    assert controller.receipt.application_response_sent and not controller.receipt.external_client_observed
    assert not controller.receipt_assessment()['correlation_valid']
    assert not calls and controller.authorization.state == 'DISARMED'


def test_real_provider_receipt_join_send_observation_and_no_second_generation(tmp_path, monkeypatch):
    app, controller, calls, factories = app_fixture(tmp_path, monkeypatch)
    token = controller.authorization.grant()
    with session(app) as client:
        before = client.get(ATTESTATION_PATH).json()['attestation']
        assert before['provider_invocation'] is None
        response = client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'}, headers=headers(token))
        assert response.status_code == 200
        receipt = response.json()['receipt']
        assert receipt['request_id'] == response.headers['x-request-id'] != 'caller-owned-id'
        assert receipt['invocation_id'] and receipt['runtime_instance_id'] == before['runtime_instance_id']
        assert receipt['pid'] == os.getpid()
        assert receipt['source_snapshot'] == before['build']['source_build_hash']
        assert receipt['scoped_loaded_code'] == before['build']['loaded_code_hash']
        assert receipt['actual_model'] == 'fixture-model' and receipt['provider_id'] == 'ollama'
        assert receipt['started_at'] <= receipt['completed_at']
        assert receipt['response_observed'] is True
        assert receipt['application_response_sent'] is False  # body cannot attest its own later delivery
        observed = client.get(ATTESTATION_PATH).json()['attestation']
        assert observed['provider_invocation']['application_response_sent'] is True
        assert observed['provider_invocation']['external_client_observed'] is False
        assert observed['build']['full_application_build_verified'] is False
        assert observed['runtime_identity'] == 'NOT_VERIFIED'
        second = client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'}, headers=headers(token))
        assert second.status_code == 403
    assert len(calls) == 1 and factories == [{'retries': 0, 'trust_env': False}]
    payload = json.loads(calls[0].content)
    assert payload['model'] == 'fixture-model'
    encoded = json.dumps(receipt)+json.dumps(observed)
    assert token not in encoded and 'PRIVATE_TEST_RESPONSE' not in encoded and payload['prompt'] not in encoded
    assert controller.authorization.state == 'TERMINAL'


@pytest.mark.parametrize('result', [
    {'model': 'other-model', 'done': True, 'response': 'secret'},
    {'model': 'fixture-model', 'done': False, 'response': 'secret'},
    {'done': True, 'response': 'secret'},
    {'model': 'fixture-model', 'done': True, 'response': {'invalid': 'content'}},
])
def test_unconfirmed_model_or_completion_fails_without_retry(tmp_path, monkeypatch, result):
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch,
        responder=lambda req: httpx.Response(200, json=result))
    token = controller.authorization.grant()
    with session(app) as client:
        for _ in range(2):
            assert client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'},
                               headers=headers(token)).status_code == 403
    assert len(calls) == 1 and controller.receipt.response_observed is False


@pytest.mark.parametrize('status', [302, 307, 308, 500])
def test_redirect_and_failure_do_not_retry_or_fallback(tmp_path, monkeypatch, status):
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch, responder=lambda req:
        httpx.Response(status, headers={'location': 'http://example.com/api/generate'}, json={'private': 'hidden'}))
    token = controller.authorization.grant()
    with session(app) as client:
        assert client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'},
                           headers=headers(token)).status_code == 502
        assert client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'},
                           headers=headers(token)).status_code == 403
    assert len(calls) == 1 and controller.authorization.dispatch_count == 1


@pytest.mark.parametrize('data', [
    {'probe': 'runtime-correlation', 'model': 'alternate'},
    {'probe': 'runtime-correlation', 'provider': 'alternate'},
    {'probe': 'runtime-correlation', 'fallback': True},
    {'probe': 'runtime-correlation', 'prompt': 'private prompt'},
    {'probe': 'x'*200}, {},
])
def test_request_overrides_and_unbounded_input_rejected_without_dispatch(tmp_path, monkeypatch, data):
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch)
    token = controller.authorization.grant()
    with session(app) as client:
        assert client.post(VERIFICATION_PATH, json=data, headers=headers(token)).status_code == 400
    assert not calls and controller.authorization.state == 'ARMED'


def test_disarmed_local_only_and_no_network_arm_endpoint(tmp_path, monkeypatch):
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch)
    with session(app) as client:
        assert client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'},
                           headers=headers('random')).status_code == 403
        assert client.post('/v1/runtime/arm').status_code == 404
        assert client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'},
            headers={**headers('random'), 'origin': 'http://127.0.0.1:5173'}).status_code == 403
    with TestClient(app, base_url='http://127.0.0.1:8000', client=('192.0.2.1', 1)) as client:
        assert client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'}).status_code == 403
    assert not calls and controller.authorization.state == 'DISARMED'


def test_loaded_provider_code_drift_blocks_before_dispatch(tmp_path, monkeypatch):
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch)
    token = controller.authorization.grant()
    async def changed_provider(self, request):
        raise AssertionError('changed code must not run')
    monkeypatch.setattr(OllamaProvider, 'generate', changed_provider)
    with session(app) as client:
        assert client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'},
                           headers=headers(token)).status_code == 403
        assert client.get(ATTESTATION_PATH).json()['attestation']['build']['loaded_code_binding'] == 'NOT_VERIFIED'
    assert not calls and controller.authorization.dispatch_count == 0


@pytest.mark.asyncio
async def test_closed_injected_client_cannot_recreate_permissive_provider_client(tmp_path, monkeypatch):
    calls = []
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request:
        (calls.append(request), httpx.Response(200, json={}))[1]))
    provider = OllamaProvider(http_client=client)
    await provider.close()
    with pytest.raises(RuntimeError, match='INJECTED_CLIENT_CLOSED'):
        await provider.generate({'prompt': 'fixture'})
    assert not calls


def test_transport_timeout_consumes_attempt_without_retry(tmp_path, monkeypatch):
    def timed_out(request):
        raise httpx.ReadTimeout('synthetic timeout', request=request)
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch, responder=timed_out)
    token = controller.authorization.grant()
    with session(app) as client:
        assert client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'},
                           headers=headers(token)).status_code == 502
        assert client.post(VERIFICATION_PATH, json={'probe': 'runtime-correlation'},
                           headers=headers(token)).status_code == 403
    assert len(calls) == 1 and controller.receipt.response_observed is False


@pytest.mark.asyncio
async def test_failed_final_asgi_send_is_not_recorded_as_delivery(tmp_path, monkeypatch):
    from app.core.runtime_correlation import ResponseObservationMiddleware
    app, controller, calls, _ = app_fixture(tmp_path, monkeypatch)
    receipt = await controller.invoke(controller.authorization.grant())
    async def response_app(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200,
                    'headers': [(b'x-request-id', receipt.request_id.encode())]})
        await send({'type': 'http.response.body', 'body': b'fixture'})
    async def failed_send(message):
        if message['type'] == 'http.response.body':
            raise OSError('synthetic disconnect')
    middleware = ResponseObservationMiddleware(response_app, controller)
    with pytest.raises(OSError):
        await middleware({'type': 'http', 'path': VERIFICATION_PATH}, None, failed_send)
    assert controller.receipt.application_response_sent is False


def test_normal_app_composition_preserves_existing_routers_and_caller_ids(tmp_path):
    root = Path(__file__).parents[1]
    # Only API owner modules are substituted to avoid their DB initialization in this unit test.
    script = r'''
import json, sys, types
from fastapi import APIRouter
for module_name, paths in [('app.api.routes', ['/v1/chat']), ('app.api.v2_routes', ['/v2/chat','/v2/dev'])]:
    owner = types.ModuleType(module_name)
    owner.router = APIRouter()
    for path in paths:
        async def synthetic_route(): return {'fixture':'composition-only'}
        owner.router.add_api_route(path, synthetic_route, methods=['POST'])
    sys.modules[module_name] = owner
from app.main import app
from app.core.config import settings
from fastapi.testclient import TestClient
assert app.state.effective_configuration is settings.effective_configuration
assert app.state.runtime_profile == 'NORMAL'
assert not hasattr(app.state, 'runtime_verification')
assert not hasattr(app.state, 'runtime_authorization')
paths = set(app.openapi()['paths'])
assert {'/v1/chat','/v2/chat','/v2/dev'} <= paths
assert '/v1/runtime/verification' not in paths
with TestClient(app) as client:
    response = client.post('/v1/chat', headers={'X-Request-ID':'normal-caller-id'})
    assert response.headers['x-request-id'] == 'normal-caller-id'
print(json.dumps({'profile':'NORMAL','evidence':'ISOLATED_COMPOSITION_WITH_STUB_API_OWNERS'}))
'''
    env = {**os.environ, 'PYTHONPATH': str(root), 'PYTHONDONTWRITEBYTECODE': '1',
           'NUSANTARA_RUNTIME_PROFILE': 'NORMAL', 'NUSANTARA_CONTROL_PLANE_READ_ONLY': '0'}
    output = json.loads(subprocess.check_output([sys.executable, '-B', '-c', script],
                        cwd=tmp_path, env=env, text=True))
    assert output['profile'] == 'NORMAL'


@pytest.mark.asyncio
async def test_concurrent_cancelled_generation_consumes_reservation(tmp_path, monkeypatch):
    entered, blocked = asyncio.Event(), asyncio.Event()
    calls = []
    async def respond(request):
        calls.append(request)
        entered.set()
        await blocked.wait()
        return httpx.Response(200, json={'model': 'fixture-model', 'done': True, 'response': 'x'})
    app, controller, _, _ = app_fixture(tmp_path, monkeypatch, responder=respond)
    # Async handler must be awaited by MockTransport, not returned by a sync fixture wrapper.
    monkeypatch.setattr(httpx, 'AsyncHTTPTransport', lambda **kw: httpx.MockTransport(respond))
    token = controller.authorization.grant()
    first = asyncio.create_task(controller.invoke(token))
    await entered.wait()
    with pytest.raises(ValueError):
        await controller.invoke(token)
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    with pytest.raises(ValueError):
        await controller.invoke(token)
    assert len(calls) == 1 and controller.authorization.state == 'TERMINAL'
    assert controller.receipt.outcome == 'FAILED_OR_CANCELLED'


def test_existing_public_v1_v2_configuration_and_control_plane_sources_untouched():
    root = Path(__file__).parents[1]
    evidence = json.loads((root/'docs/reports/r2-a8-remediation-20261008/PROFILE_BEFORE.json').read_text(encoding='utf-8-sig'))
    protected = {'app/api/routes.py', 'app/api/v2_routes.py', 'app/core/config.py',
                 'app/core/runtime_identity.py', 'app/core/control_plane_projection.py'}
    for item in evidence['files']:
        if item['path'] in protected:
            from v1_baseline import assert_current_source
            assert_current_source(item['path'])


def test_attestation_real_app_boot_request_response_shutdown_avoid_protected_state(tmp_path):
    root = Path(__file__).parents[1]
    script = r'''
import builtins, io, json, os, sqlite3, sys, importlib.abc
from pathlib import Path
class ProtectedImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('app.knowledge', 'app.rag', 'app.language')) or fullname in ('app.api.routes','app.api.v2_routes'):
            raise AssertionError('protected runtime owner imported')
sys.meta_path.insert(0, ProtectedImports())
def forbidden(*args, **kwargs):
    raise AssertionError('protected runtime operation')
sqlite3.connect = forbidden
original_open, original_io_open = builtins.open, io.open
def guarded_open(original):
    def open_file(file, mode='r', *args, **kwargs):
        if not isinstance(file, int):
            name = str(file).lower().replace('\\','/')
            assert not name.endswith(('.db','.db-wal','.db-shm')) and '/data/knowledge/' not in name
        assert not any(flag in mode for flag in ('w','a','x','+'))
        return original(file, mode, *args, **kwargs)
    return open_file
builtins.open, io.open = guarded_open(original_open), guarded_open(original_io_open)
import httpx
calls = []
def respond(request):
    calls.append(request)
    return httpx.Response(200, json={'model':'fixture-model','done':True,'response':'SENSITIVE_FIXTURE_RESPONSE'})
httpx.AsyncHTTPTransport = lambda **kw: httpx.MockTransport(respond)
from app.models.ollama import OllamaProvider
OllamaProvider.health_check = forbidden
OllamaProvider.list_models = forbidden
from app.main import app
from fastapi.testclient import TestClient
controller = app.state.runtime_verification
assert app.state.effective_configuration.runtime.profile == 'ATTESTATION'
assert controller.authorization.state == 'DISARMED'
token = controller.authorization.grant()
with TestClient(app, base_url='http://127.0.0.1:8000', client=('127.0.0.1',1)) as client:
    import app.api.control_plane as control_plane
    control_plane.project = forbidden
    assert client.get('/v1/control-plane/snapshot').json()['live_actions'] == 'LOCKED'
    response = client.post('/v1/runtime/verification', json={'probe':'runtime-correlation'},
        headers={'Authorization':'Bearer '+token, 'X-Request-ID':'untrusted-client-id'})
    assert response.status_code == 200
    receipt = response.json()['receipt']
    assert receipt['request_id'] == response.headers['x-request-id'] != 'untrusted-client-id'
    observation = client.get('/v1/runtime/attestation').json()['attestation']
    assert observation['provider_invocation']['application_response_sent']
    for path in ('/v1/chat','/v2/chat','/v2/dev'):
        assert client.post(path).status_code == 404
assert len(calls) == 1
encoded = json.dumps(observation)
assert token not in encoded and 'SENSITIVE_FIXTURE_RESPONSE' not in encoded
assert not any(name.startswith(('app.knowledge','app.rag','app.language')) for name in sys.modules)
assert app.state.runtime_authorization._audit.path is None
assert app.state.runtime_authorization._policy is None
assert app.state.runtime_authorization._isolated_transport is None
assert app.state.runtime_authorization.evidence()['live_actions'] == 'LOCKED'
assert {name for name in sys.modules if name.startswith('app.approval')} <= {
    'app.approval','app.approval.audit_trail','app.approval.queue','app.approval.runtime_authorization'}
print(json.dumps({'verification_type':'ISOLATED_GUARDED_ASGI_WITH_MOCK_HTTP','live_runtime_verified':False,
    'profile':'ATTESTATION','dispatch_count':len(calls),'observation':observation,
    'foundation':app.state.runtime_authorization.evidence()}))
'''
    env = {**os.environ, 'PYTHONPATH': str(root), 'PYTHONDONTWRITEBYTECODE': '1',
        'NUSANTARA_RUNTIME_PROFILE': 'ATTESTATION', 'NUSANTARA_CONTROL_PLANE_READ_ONLY': '0',
        'LLM_MODEL': 'fixture-model', 'LLM_BASE_URL': 'http://localhost:11434'}
    # Remove inherited aliases that could conflict with the explicitly isolated fixture snapshot.
    env.pop('NUSANTARA_LLM_MODEL', None)
    env.pop('NUSANTARA_RUNTIME_PORT', None)
    env['PORT'] = '8000'
    result = json.loads(subprocess.check_output([sys.executable, '-B', '-c', script],
                       cwd=tmp_path, env=env, text=True))
    assert result['dispatch_count'] == 1 and result['live_runtime_verified'] is False
    evidence = os.environ.get('R2_PROFILE_TEST_EVIDENCE')
    if evidence:
        Path(evidence).write_text(json.dumps(result, indent=2), encoding='utf-8')
