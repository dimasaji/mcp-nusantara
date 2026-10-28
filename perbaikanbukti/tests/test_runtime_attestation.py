"""R2-A7 isolated observation tests: no live service or model generation."""
import ast
import builtins
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx
import pytest

from app.core.runtime_attestation import ATTESTATION_PATH, install_runtime_attestation
from app.core.runtime_identity import BUILD_ID, current_runtime_instance


def application():
    app = FastAPI(title='isolated-attestation', version='fixture-version')

    @app.get('/fixture')
    async def fixture():
        return {'value': 'original'}

    install_runtime_attestation(app, entrypoint='isolated.fixture:app')
    return app


def client(app, *, peer='127.0.0.1', url='http://127.0.0.1:8000'):
    return TestClient(app, base_url=url, client=(peer, 43210))


def test_attestation_is_stable_and_uses_current_process_os_identity():
    with client(application()) as session:
        first = session.get(ATTESTATION_PATH)
        second = session.get(ATTESTATION_PATH)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    evidence = first.json()['attestation']
    assert evidence['application'] == {'service_name': 'isolated-attestation',
        'service_version': 'fixture-version', 'application_entrypoint': 'isolated.fixture:app'}
    process = evidence['process']
    assert process['process_id'] == process['observed_process_id'] == os.getpid()
    assert process['parent_process_id'] == os.getppid()
    assert process['working_directory'] == os.getcwd()
    assert process['interpreter_path'] == sys.executable
    assert process['valid_for_current_process'] is True
    if sys.platform == 'win32' or sys.platform.startswith('linux'):
        assert process['executable_path']
        start = datetime.fromisoformat(process['process_start_time'])
        captured = datetime.fromisoformat(evidence['instance_captured_at'])
        assert start <= captured <= datetime.now(timezone.utc)
    assert evidence['runtime_instance_id'] == current_runtime_instance().runtime_instance_id
    assert evidence['build']['loaded_code_binding'] == 'MATCH'
    assert evidence['build']['source_build_hash'] == BUILD_ID
    assert evidence['build']['source_build_evidence'] == 'IMPORT_TIME_SOURCE_SNAPSHOT_ONLY'
    assert evidence['build']['full_application_build_verified'] is False
    assert evidence['provider_invocation'] is None and evidence['provider_observation'] == 'NOT_OBSERVED'
    assert evidence['runtime_identity'] == 'NOT_VERIFIED'
    assert {'request_id', 'invocation_id', 'actual_model', 'runtime_instance_id'} <= set(
        evidence['correlation_readiness']['required_external_receipt_fields'])


@pytest.mark.parametrize('peer,url,origin', [
    ('192.0.2.1', 'http://127.0.0.1:8000', None),
    ('127.0.0.1', 'http://example.com:8000', None),
    ('127.0.0.1', 'http://127.0.0.1:5173', None),
    ('127.0.0.1', 'http://127.0.0.1:8000', 'http://example.com:8000'),
    ('127.0.0.1', 'http://127.0.0.1:8000', 'http://127.0.0.1:5173'),
    ('127.0.0.1', 'http://127.0.0.1:8000', 'null'),
    ('127.0.0.1', 'http://127.0.0.1:8000', 'http://localhost:invalid'),
    ('127.0.0.1', 'http://127.0.0.1:8000', 'http://[invalid'),
])
def test_nonlocal_or_nonruntime_access_is_denied(peer, url, origin):
    with client(application(), peer=peer, url=url) as session:
        headers = {'origin': origin} if origin else {}
        response = session.get(ATTESTATION_PATH, headers=headers)
    assert response.status_code == 403
    assert 'attestation' not in response.json()


def test_local_runtime_origin_is_allowed_and_post_is_not():
    with client(application()) as session:
        assert session.get(ATTESTATION_PATH, headers={'origin': 'http://localhost:8000'}).status_code == 200
        assert session.post(ATTESTATION_PATH).status_code == 405


def test_live_handler_code_changes_are_detected_without_reading_source(monkeypatch):
    app = application()
    fixture = next(route.endpoint for route in app.routes if route.path == '/fixture')
    with client(app) as session:
        before = session.get(ATTESTATION_PATH).json()['attestation']['build']

        async def replacement():
            return {'value': 'actually-changed-loaded-code'}

        monkeypatch.setattr(fixture, '__code__', replacement.__code__)
        after = session.get(ATTESTATION_PATH).json()['attestation']['build']
    assert before['loaded_code_hash'] == after['loaded_code_hash']
    assert after['current_registered_code_hash'] != before['loaded_code_hash']
    assert after['loaded_code_binding'] == 'NOT_VERIFIED'
    assert after['full_application_build_verified'] is False


def test_endpoint_does_not_open_files_databases_network_or_configuration(monkeypatch):
    app = application()
    before_env = dict(os.environ)

    def forbidden(*args, **kwargs):
        raise AssertionError('attestation attempted external I/O')

    with client(app) as session:
        with monkeypatch.context() as guards:
            guards.setattr(builtins, 'open', forbidden)
            guards.setattr(Path, 'read_bytes', forbidden)
            guards.setattr(Path, 'read_text', forbidden)
            guards.setattr(Path, 'write_bytes', forbidden)
            guards.setattr(Path, 'write_text', forbidden)
            guards.setattr(sqlite3, 'connect', forbidden)
            guards.setattr(socket, 'create_connection', forbidden)
            guards.setattr(httpx.AsyncClient, 'send', forbidden)
            response = session.get(ATTESTATION_PATH)
    assert response.status_code == 200
    assert dict(os.environ) == before_env


def test_duplicate_endpoint_registration_is_rejected():
    app = application()
    with pytest.raises(ValueError, match='ALREADY_REGISTERED'):
        install_runtime_attestation(app, entrypoint='other:app')


def test_unavailable_os_identity_is_not_fabricated(monkeypatch):
    import app.core.runtime_attestation as owner
    actual = owner._process_identity()
    actual.update(process_start_time=None, executable_path=None, os_metadata_source='UNAVAILABLE')
    monkeypatch.setattr(owner, '_process_identity', lambda: dict(actual))
    with client(application()) as session:
        process = session.get(ATTESTATION_PATH).json()['attestation']['process']
    assert process['process_start_time'] is None
    assert process['executable_path'] is None
    assert process['os_metadata_source'] == 'UNAVAILABLE'


def test_new_processes_have_distinct_instances_and_actual_main_integration(tmp_path):
    root = Path(__file__).parents[1]
    script = '''
import json, os, sys
from fastapi.testclient import TestClient
from app.main import app
from app.core.runtime_attestation import ATTESTATION_PATH
with TestClient(app, base_url='http://127.0.0.1:8000', client=('127.0.0.1', 43210)) as client:
    first = client.get(ATTESTATION_PATH)
    second = client.get(ATTESTATION_PATH)
assert first.status_code == 200 and first.json() == second.json()
for name in sys.modules:
    assert not name.startswith(('app.knowledge', 'app.models', 'app.language', 'app.approval'))
assert 'app.api.routes' not in sys.modules and 'app.api.v2_routes' not in sys.modules
print(json.dumps(first.json()))
'''
    environment = {**os.environ, 'NUSANTARA_CONTROL_PLANE_READ_ONLY': '1',
                   'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(root)}
    results = [json.loads(subprocess.check_output([sys.executable, '-B', '-c', script],
                cwd=tmp_path, env=environment, text=True)) for _ in range(2)]
    first, second = [result['attestation'] for result in results]
    assert first['process']['process_id'] != second['process']['process_id']
    assert first['runtime_instance_id'] != second['runtime_instance_id']
    assert first['application']['application_entrypoint'] == 'app.main:app'
    assert first['application']['service_name'] == 'Nusantara Core + Hermes API'
    assert first['process']['working_directory'] == str(tmp_path)
    assert first['build']['loaded_code_hash'] == second['build']['loaded_code_hash']
    assert first['runtime_identity'] == second['runtime_identity'] == 'NOT_VERIFIED'
    evidence_path = os.environ.get('R2_A7_TEST_EVIDENCE')
    if evidence_path:
        Path(evidence_path).write_text(json.dumps({'verification_type': 'ISOLATED_APPLICATION_BOOT',
            'existing_live_service_verified': False, 'applications': results}, indent=2), encoding='utf-8')


def test_main_change_only_installs_attestation_and_preserves_existing_handlers():
    root = Path(__file__).parents[1]
    before = ast.parse((root/'docs/reports/r2-a7-runtime-attestation-20261008/main.py.before').read_text(encoding='utf-8-sig'))
    after = ast.parse((root/'app/main.py').read_text(encoding='utf-8-sig'))

    def original_nodes(module):
        # Authorized composition/profile changes; original handler semantics stay intact.
        functions = [node for node in module.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for node in functions:
            if node.name == 'request_id_middleware':
                for statement in node.body:
                    if (isinstance(statement, ast.Assign) and isinstance(statement.value, ast.IfExp)
                            and any(isinstance(target, ast.Name) and target.id == 'incoming'
                                    for target in statement.targets)):
                        statement.value = statement.value.orelse
        return [ast.dump(node) for node in functions]

    assert original_nodes(before) == original_nodes(after)
