"""PENDING-only integration: in-process ASGI, no socket/provider/IPC activation."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from app.api.control_plane import router
from app.approval.runtime_authorization import AuthorizationError, SCOPE
from test_runtime_authorization import fixture, command


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    app, owner, controller, calls = fixture(tmp_path, live_locked=True)
    app.include_router(router)
    import app.api.control_plane as routes
    monkeypatch.setattr(routes, 'project', lambda: (_ for _ in ()).throw(AssertionError('protected projection')))
    return TestClient(app, base_url='http://127.0.0.1:8000', client=('127.0.0.1', 123)), owner, controller, calls


def body(owner):
    return {'scope': SCOPE, 'evidence_version': owner.evidence()['evidence_version']}


def post(client, data, **kwargs):
    return client.post('/v1/control-plane/intention', json=data,
        headers={'Origin': 'http://127.0.0.1:5173'}, **kwargs)


def test_pending_snapshot_and_duplicate_no_authority(isolated):
    client, owner, controller, calls = isolated
    state = client.get('/v1/control-plane/snapshot').json()
    assert state['projection_contract'] == 'ATTESTATION_FOUNDATION_V1'
    assert 'schema_version' not in state and 'gates' not in state
    first = post(client, body(owner))
    assert first.status_code == 200 and first.json()['state'] == 'PENDING'
    audit_count = len(owner._audit.entries())
    second = post(client, body(owner))
    assert second.json() == first.json() and len(owner._audit.entries()) == audit_count
    assert len(owner._reviews) == len(owner._queue._items) == 1
    assert controller.authorization.state == 'DISARMED' and not calls and owner._permit is None
    assert owner._policy is not None  # Isolated fixture only; not a listener or deployed policy.


@pytest.mark.parametrize('change', [{'evidence_version': '0'*64}, {'scope': 'NORMAL'},
    {'actor': 'operator'}, {'reviewer': 'trusted'}, {'pid': 1}, {'token': 'x'},
    {'operation': 'ARM'}, {'operation': 'EXECUTE'}, {'model': 'x'}, {'ttl': 999}])
def test_stale_or_asserted_fields_rejected_before_mutation(isolated, change):
    client, owner, controller, calls = isolated
    response = post(client, {**body(owner), **change})
    assert response.status_code in (409, 422)
    assert not owner._reviews and not owner._queue._items and not owner._audit.entries()
    assert not owner._poisoned and controller.authorization.state == 'DISARMED' and not calls


@pytest.mark.parametrize('origin', ['', 'null', 'http://localhost:5173', 'http://evil.example', 'http://127.0.0.1:5174'])
def test_origin_rejected_before_mutation(isolated, origin):
    client, owner, _, _ = isolated
    response = client.post('/v1/control-plane/intention', json=body(owner), headers={'Origin': origin})
    assert response.status_code == 403 and not owner._audit.entries()


@pytest.mark.parametrize('raw', ['{"scope":"x","scope":"y"}', '[' , '[]', '"x"', 'x'*513])
def test_bounded_json(isolated, raw):
    client, owner, _, _ = isolated
    response = client.post('/v1/control-plane/intention', content=raw,
        headers={'Origin':'http://127.0.0.1:5173', 'Content-Type':'application/json'})
    assert response.status_code in (413, 422) and not owner._audit.entries()


def test_wrong_host_peer_normal_and_missing_owner(isolated):
    client, owner, _, _ = isolated
    response = client.post('/v1/control-plane/intention', json=body(owner), headers={
        'Origin':'http://127.0.0.1:5173','Host':'127.0.0.1:5173'})
    assert response.status_code == 403
    remote = TestClient(client.app, base_url='http://127.0.0.1:8000', client=('192.0.2.1', 1))
    assert post(remote, body(owner)).status_code == 403
    client.app.state.runtime_profile = 'NORMAL'
    assert post(client, body(owner)).status_code == 404
    client.app.state.runtime_profile = 'ATTESTATION'
    del client.app.state.runtime_authorization
    assert post(client, body(owner)).status_code == 503
    assert not owner._audit.entries()


def test_concurrency_expiry_capacity_and_detached_projection(isolated):
    _, owner, controller, calls = isolated
    data = body(owner)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: owner.browser_intention(**data), range(20)))
    assert all(r == results[0] for r in results) and len(owner._reviews) == 1
    review = owner._reviews[results[0]['review_id']]
    owner._reviews[review.review_id] = replace(review, deadline=0)
    count = len(owner._audit.entries())
    with pytest.raises(AuthorizationError):
        owner.browser_intention(**data)
    assert len(owner._audit.entries()) == count and not owner._poisoned
    snapshot = owner.evidence()
    snapshot['reviews'][0]['state'] = 'APPROVED'
    assert owner.evidence()['reviews'][0]['state'] == 'PENDING'
    assert controller.authorization.state == 'DISARMED' and not calls


@pytest.mark.parametrize('operation', ['ARM', 'EXECUTE'])
def test_browser_cannot_reach_arm_execute(isolated, operation):
    client, owner, controller, calls = isolated
    review = post(client, body(owner)).json()
    with pytest.raises(AuthorizationError, match='NATIVE_OPERATOR_REQUIRED'):
        asyncio.run(owner.handle_verified({'reviewer': 'browser'}, command(review, operation)))
    assert client.post('/v1/control-plane/'+operation.lower()).status_code == 404
    assert controller.authorization.state == 'DISARMED' and owner._permit is None and not calls


def test_atomic_material_change_and_storage_failure(isolated, monkeypatch):
    _, owner, controller, calls = isolated
    data = body(owner)
    original = owner._material
    monkeypatch.setattr(owner, '_material', lambda: {**original(), 'pid': 999})
    with pytest.raises(AuthorizationError):
        owner.browser_intention(**data)
    assert not owner._audit.entries() and not owner._reviews
    monkeypatch.setattr(owner, '_material', original)
    monkeypatch.setattr(owner._queue, 'submit', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('fixture')))
    with pytest.raises(AuthorizationError):
        owner.browser_intention(**data)
    assert owner._poisoned and owner._permit is None and not calls


def test_binding_changes_between_validation_and_creation(isolated, monkeypatch):
    _, owner, _, _ = isolated
    data = body(owner)
    original = owner._material
    count = 0
    def changing():
        nonlocal count
        count += 1
        value = original()
        return value if count == 1 else {**value, 'runtime_instance': 'changed'}
    monkeypatch.setattr(owner, '_material', changing)
    with pytest.raises(AuthorizationError, match='STALE_BROWSER_CONTEXT'):
        owner.browser_intention(**data)
    assert not owner._audit.entries() and not owner._queue._items and not owner._poisoned


def test_capacity_rejects_without_poisoning(isolated):
    _, owner, _, _ = isolated
    data = body(owner)
    owner._browser_reviews.update({str(i): 'irrelevant' for i in range(32)})
    with pytest.raises(AuthorizationError, match='BROWSER_CAPACITY'):
        owner.browser_intention(**data)
    assert not owner._poisoned and not owner._audit.entries()


@pytest.mark.parametrize('operation', ['ARM', 'EXECUTE'])
def test_live_lock_even_after_trusted_peer_validation(isolated, monkeypatch, operation):
    _, owner, controller, calls = isolated
    review = owner.browser_intention(**body(owner))
    # Unit seam only: test the post-native-validation live lock, no pipe/listener/proof minted.
    from app.security.local_operator import Windows
    monkeypatch.setattr(owner, '_peer', lambda proof: Windows().current_actor())
    with pytest.raises(AuthorizationError, match='TRANSITION_FAILED_CLOSED'):
        asyncio.run(owner.handle_verified(object(), command(review, operation)))
    assert owner._poisoned and owner._permit is None and controller.authorization.dispatch_count == 0 and not calls


def test_guarded_application_composition_no_network_or_protected_state(tmp_path):
    root = Path(__file__).parents[1]
    script = r'''
import builtins, io, json, socket, sqlite3, sys, importlib.abc
class Boundary(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('app.knowledge','app.rag','app.language')) or fullname in ('app.api.routes','app.api.v2_routes'):
            raise AssertionError('protected import')
sys.meta_path.insert(0, Boundary())
def forbidden(*a, **k): raise AssertionError('forbidden operation')
sqlite3.connect = forbidden
original_connect = socket.socket.connect
def no_application_connect(sock, address):
    # Windows asyncio uses stdlib socketpair internally; this is not application HTTP.
    if sys._getframe(1).f_code is socket._fallback_socketpair.__code__:
        return original_connect(sock, address)
    return forbidden()
socket.socket.connect = no_application_connect
def guard(original):
    def opened(file, mode='r', *a, **k):
        name = str(file).lower().replace('\\','/')
        assert not name.endswith(('.db','.db-wal','.db-shm')) and '/data/knowledge/' not in name
        assert not any(flag in mode for flag in ('w','a','x','+'))
        return original(file, mode, *a, **k)
    return opened
builtins.open, io.open = guard(builtins.open), guard(io.open)
import httpx
httpx.HTTPTransport.handle_request = forbidden
httpx.AsyncHTTPTransport.handle_async_request = forbidden
from app.security.local_operator import LocalOperatorChannel
LocalOperatorChannel.__enter__ = forbidden
from app.models.ollama import OllamaProvider
OllamaProvider.health_check = forbidden
OllamaProvider.list_models = forbidden
from app.main import app
import app.api.control_plane as routes
routes.project = forbidden
from fastapi.testclient import TestClient
owner = app.state.runtime_authorization
with TestClient(app,base_url='http://127.0.0.1:8000',client=('127.0.0.1',1)) as client:
    state = client.get('/v1/control-plane/snapshot').json()
    response = client.post('/v1/control-plane/intention',json={'scope':state['scope'],'evidence_version':state['evidence_version']},headers={'Origin':'http://127.0.0.1:5173'})
    assert response.status_code == 200 and response.json()['state'] == 'PENDING'
assert owner._policy is None and owner._isolated_transport is None and owner._audit.path is None
assert app.state.runtime_verification.authorization.state == 'DISARMED'
assert app.state.runtime_verification.authorization.dispatch_count == 0
assert owner._permit is None and owner.evidence()['live_actions'] == 'LOCKED'
print(json.dumps({'isolated_in_process':True,'live_http':False,'dispatch_count':0,'state':'PENDING','live_actions':'LOCKED',
    'snapshot':state,'intention':response.json()}))
'''
    env = {**os.environ,'PYTHONPATH':str(root),'PYTHONDONTWRITEBYTECODE':'1',
        'NUSANTARA_RUNTIME_PROFILE':'ATTESTATION','NUSANTARA_CONTROL_PLANE_READ_ONLY':'0','PORT':'8000'}
    env.pop('NUSANTARA_RUNTIME_PORT', None)
    result = json.loads(subprocess.check_output([sys.executable,'-B','-c',script],cwd=tmp_path,env=env,text=True))
    assert result['dispatch_count'] == 0 and result['live_http'] is False
    evidence_path = os.environ.get('R2_CPLANE_ISOLATED_EVIDENCE')
    if evidence_path:
        Path(evidence_path).write_text(json.dumps(result, indent=2), encoding='utf-8')
