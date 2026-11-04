"""Readiness distinguishes API, inventory, storage and observed inference."""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_inventory_without_model_is_not_chat_ready_and_no_inference_is_dispatched(tmp_path, monkeypatch):
    from test_sop_review import engine_at

    from app.api.runtime_readiness import (
        get_provider_factory,
        get_readiness_knowledge,
        get_runtime_owner,
        router,
    )
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'readiness-fixture')
    config = SimpleNamespace(llm=SimpleNamespace(provider='ollama', model='fixture'))
    owner = SimpleNamespace(configuration_snapshot=lambda: (config, 1),
        model_control_status=lambda: {'revision': 1, 'status': 'NOT_VERIFIED', 'verified_at': None})
    calls = []
    class Provider:
        def __init__(self, **kwargs):
            calls.append('construct')
        async def health_check(self):
            return {'available': False, 'status': 'degraded', 'model': 'fixture'}
        async def close(self):
            calls.append('close')
    app = FastAPI()
    app.include_router(router, prefix='/v1')
    app.dependency_overrides[get_runtime_owner] = lambda: owner
    app.dependency_overrides[get_readiness_knowledge] = lambda: engine_at(tmp_path / 'readiness.db')
    app.dependency_overrides[get_provider_factory] = lambda: Provider
    with TestClient(app) as client:
        assert client.get('/v1/runtime/readiness').status_code == 403
        assert calls == []
        result = client.get('/v1/runtime/readiness', headers={'X-Admin-Token': 'readiness-fixture'})
    assert result.status_code == 200
    data = result.json()
    assert data['status'] == 'BLOCKED'
    assert data['checks']['storage']['status'] == 'READABLE'
    assert data['checks']['model']['status'] == 'MISSING'
    assert data['checks']['inference']['status'] == 'NOT_VERIFIED'
    assert data['operational_acceptance'] == 'NOT_VERIFIED'
    assert calls == ['construct', 'close']


@pytest.mark.parametrize('provider_name,available,inference,changed,expected', [
    ('ollama', True, 'NOT_VERIFIED', False, 'PREREQUISITES_READY'),
    ('ollama', True, 'INFERENCE_VERIFIED', False, 'PREREQUISITES_READY'),
    ('openrouter', True, 'INFERENCE_VERIFIED', False, 'BLOCKED'),
    ('ollama', True, 'INFERENCE_VERIFIED', True, 'CONFIGURATION_CHANGED'),
])
def test_readiness_preserves_inventory_inference_and_configuration_distinctions(
        tmp_path, monkeypatch, provider_name, available, inference, changed, expected):
    from test_sop_review import engine_at

    from app.api.runtime_readiness import (
        get_provider_factory,
        get_readiness_knowledge,
        get_runtime_owner,
        router,
    )
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'readiness-fixture')
    configuration = SimpleNamespace(llm=SimpleNamespace(provider=provider_name, model='fixture'))
    snapshots = iter([1, 2 if changed else 1])
    owner = SimpleNamespace(configuration_snapshot=lambda: (configuration, next(snapshots)),
        model_control_status=lambda: {'revision': 1, 'status': inference, 'verified_at': 'fixture-time'})
    calls = []
    class Provider:
        def __init__(self, **kwargs):
            calls.append('local-inventory')
        async def health_check(self):
            return {'available': available, 'status': 'ok', 'model': 'fixture'}
        async def close(self):
            pass
    app = FastAPI()
    app.include_router(router, prefix='/v1')
    app.dependency_overrides[get_runtime_owner] = lambda: owner
    app.dependency_overrides[get_readiness_knowledge] = lambda: engine_at(tmp_path / 'fixture.db')
    app.dependency_overrides[get_provider_factory] = lambda: Provider
    with TestClient(app) as client:
        data = client.get('/v1/runtime/readiness', headers={'X-Admin-Token': 'readiness-fixture'}).json()
    assert data['status'] == expected
    assert data['operational_acceptance'] == 'NOT_VERIFIED'
    assert data['checks']['document']['status'] == 'NOT_CHECKED'
    assert data['checks']['inference']['status'] == ('OBSERVED' if inference == 'INFERENCE_VERIFIED' and not changed else 'NOT_VERIFIED')
    assert calls == ([] if provider_name == 'openrouter' else ['local-inventory'])


@pytest.mark.parametrize('failure', ['missing_db', 'unreviewed_document', 'provider_failure'])
def test_readiness_fails_closed_without_creating_missing_storage_or_review_tables(tmp_path, monkeypatch, failure):
    import sqlite3

    from test_sop_review import engine_at

    from app.api.runtime_readiness import (
        get_provider_factory,
        get_readiness_knowledge,
        get_runtime_owner,
        router,
    )
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'readiness-fixture')
    configuration = SimpleNamespace(llm=SimpleNamespace(provider='ollama', model='fixture'))
    owner = SimpleNamespace(configuration_snapshot=lambda: (configuration, 1),
        model_control_status=lambda: {'revision': 1, 'status': 'NOT_VERIFIED', 'verified_at': None})
    engine = engine_at(tmp_path / 'existing.db')
    identifier = engine.process_knowledge_source('fixture.txt', b'Persyaratan surat permohonan dalam dokumen pengujian.')['document_id']
    if failure == 'missing_db':
        engine = SimpleNamespace(rag=SimpleNamespace(_store=SimpleNamespace(db_path=tmp_path / 'missing.db')))
    class Provider:
        def __init__(self, **kwargs):
            pass
        async def health_check(self):
            if failure == 'provider_failure':
                raise RuntimeError('fixture transport failure')
            return {'available': True, 'status': 'ok', 'model': 'fixture'}
        async def close(self):
            if failure == 'provider_failure':
                raise RuntimeError('fixture close failure')
    app = FastAPI()
    app.include_router(router, prefix='/v1')
    app.dependency_overrides[get_runtime_owner] = lambda: owner
    app.dependency_overrides[get_readiness_knowledge] = lambda: engine
    app.dependency_overrides[get_provider_factory] = lambda: Provider
    with TestClient(app) as client:
        result = client.get('/v1/runtime/readiness', params={'document_id': identifier},
            headers={'X-Admin-Token': 'readiness-fixture'})
    assert result.status_code == 200
    assert result.json()['status'] == 'BLOCKED'
    assert not (tmp_path / 'missing.db').exists()
    with sqlite3.connect(tmp_path / 'existing.db') as connection:
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='sop_review_events'").fetchone() is None
