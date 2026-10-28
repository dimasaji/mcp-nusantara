"""Local-only projection and guarded evidence-only startup tests."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.control_plane import router
from app.core.control_plane_projection import project


def client(host='127.0.0.1',base_url='http://127.0.0.1'):
    app=FastAPI();app.include_router(router)
    return TestClient(app,base_url=base_url,client=(host,12345))


def test_real_projection_no_database_worker_or_mutating_git():
    import subprocess
    run=subprocess.run
    seen=[]
    def read_git(args,**kwargs):
        assert args[-1] in ['--short','--show-current','HEAD']
        seen.append(args)
        return run(args,**kwargs)
    with patch('sqlite3.connect',side_effect=AssertionError('database forbidden')),patch('app.core.control_plane_projection.subprocess.run',side_effect=read_git):
        state=project()
    assert seen
    assert next(p for p in state['phases'] if p['id']=='R2')['status']=='CLOSED_PASS'
    assert next(p for p in state['phases'] if p['id']=='R3')['status']=='R3_IMPLEMENTATION_PASS_WITH_CONDITIONS'
    assert state['runtime']['current_status']=='NOT_VERIFIED'
    assert state['runtime']['scope']=='HISTORICAL_CONTROLLED_RUNTIME'
    assert 'executable' not in state['runtime']
    assert state['rag']['status']=='FIXTURE_EVIDENCE'
    assert state['governance']['read_only'] is True


@pytest.mark.parametrize('method',['post','put','delete','patch'])
def test_mutation_methods_rejected(method):
    assert getattr(client(),method)('/v1/control-plane/snapshot').status_code==405


@pytest.mark.parametrize('host,url,origin',[('10.0.0.2','http://127.0.0.1',None),('127.0.0.1','http://evil.example',None),('127.0.0.1','http://127.0.0.1','https://evil.example')])
def test_remote_origin_and_dns_rebinding_rejected(host,url,origin):
    response=client(host,url).get('/v1/control-plane/snapshot',headers={'Origin':origin} if origin else {})
    assert response.status_code==403


def test_local_snapshot_route():
    response=client().get('/v1/control-plane/snapshot')
    assert response.status_code==200
    assert response.json()['schema_version']==1


def test_missing_evidence_is_not_pass(tmp_path):
    state=project(tmp_path)
    assert state['current_phase']=='UNKNOWN'
    assert state['rag']['status']=='NOT_VERIFIED'
    assert all(p['status'] in ('UNKNOWN','NOT_VERIFIED') for p in state['phases'])
    assert state['verification'][0]['status']=='NOT_VERIFIED'


def test_tampered_r3_evidence_rejected(tmp_path):
    root=Path(__file__).parents[1]
    sources=json.loads((root/'control-plane/evidence-sources.json').read_text(encoding='utf-8-sig'))
    (tmp_path/'control-plane').mkdir()
    sources['r3_audit']=str(tmp_path/'fake-audit')
    (tmp_path/'fake-audit').mkdir()
    (tmp_path/'fake-audit/closure-manifest.json').write_text('{"status":"R3_PASS"}')
    (tmp_path/'control-plane/evidence-sources.json').write_text(json.dumps(sources))
    state=project(tmp_path)
    assert state['rag']['status']=='NOT_VERIFIED'
    assert any('r3:' in warning for warning in state['warnings'])


def test_evidence_only_real_entrypoint_skips_production_owners():
    import os
    import subprocess
    import sys
    script = r'''
import importlib.abc, sqlite3, sys
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in ('app.core.config', 'app.api.routes', 'app.api.v2_routes') or fullname.startswith(('app.knowledge', 'app.models')):
            raise AssertionError('Production owner imported: ' + fullname)
sys.meta_path.insert(0, Guard())
sqlite3.connect = lambda *a, **k: (_ for _ in ()).throw(AssertionError('Database forbidden'))
from app.main import app
from fastapi.testclient import TestClient
with TestClient(app, base_url='http://127.0.0.1', client=('127.0.0.1', 12345)) as client:
    response = client.get('/v1/control-plane/snapshot')
    assert response.status_code == 200, response.text
    assert response.json()['runtime']['current_status'] == 'NOT_VERIFIED'
    assert client.post('/v1/control-plane/snapshot').status_code == 405
    assert client.post('/v1/chat', json={}).status_code == 404
    assert client.post('/v2/chat', json={}).status_code == 404
    assert client.get('/ui').status_code == 404
    assert client.get('/health').json() == {'status': 'evidence_only', 'runtime': 'NOT_VERIFIED', 'mode': 'READ_ONLY'}
assert app.state.effective_configuration is None
'''
    result = subprocess.run([sys.executable, '-B', '-c', script],
                            cwd=Path(__file__).parents[1], capture_output=True,
                            text=True, timeout=30,
                            env=dict(os.environ, NUSANTARA_CONTROL_PLANE_READ_ONLY='1',
                                     PYTHONDONTWRITEBYTECODE='1'))
    assert result.returncode == 0, result.stdout + result.stderr
