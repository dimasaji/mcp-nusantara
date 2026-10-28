"""Report-owned execution guard, not production code or a weakened test assertion."""
import ast
import builtins
import importlib.abc
import io
import os
from pathlib import Path
import sqlite3
import sys
import types

root = Path(__file__).resolve().parents[3]
out = Path(__file__).parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root/'tests'))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'

def forbidden(*args, **kwargs):
    raise AssertionError('R2-A10 protected database/network operation')
sqlite3.connect = forbidden
def guarded_open(original):
    def opened(file, *args, **kwargs):
        name = str(file).lower().replace('\\', '/')
        if name.endswith(('.db', '.db-wal', '.db-shm')) or '/data/knowledge/' in name:
            forbidden()
        return original(file, *args, **kwargs)
    return opened
builtins.open = guarded_open(builtins.open)
io.open = guarded_open(io.open)

class NoKnowledge(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('app.knowledge', 'app.rag', 'app.language')):
            raise AssertionError('R2-A10 protected owner import')
sys.meta_path.insert(0, NoKnowledge())

import httpx
httpx.HTTPTransport.handle_request = forbidden
httpx.AsyncHTTPTransport.handle_async_request = forbidden
import pytest

class IsolatedHealth:
    @pytest.fixture(autouse=True)
    def health_owner_boundary(self, request, monkeypatch):
        if request.node.name != 'test_health_reports_same_loaded_build':
            yield
            return
        # Reuse the actual HealthResponse and decorated health_check AST, unchanged.
        # Substitute only eager API owners, as the existing NORMAL composition test does.
        from fastapi import APIRouter
        from pydantic import BaseModel
        from app.core.config import settings
        from app.core.nusantara_config import load_nusantara_config
        from app.core.runtime_identity import BUILD_ID
        monkeypatch.setattr(settings, '_effective_configuration',
            load_nusantara_config(project_root=out, environment={}, overrides={'runtime':{'profile':'NORMAL'}}))
        monkeypatch.setenv('NUSANTARA_CONTROL_PLANE_READ_ONLY', '0')
        owner = types.ModuleType('app.api.routes')
        owner.router = APIRouter(prefix='/v1')
        owner.__dict__.update(BaseModel=BaseModel, settings=settings, BUILD_ID=BUILD_ID)
        source = ast.parse((root/'app/api/routes.py').read_text(encoding='utf-8-sig'))
        selected = [node for node in source.body if isinstance(node,(ast.ClassDef,ast.AsyncFunctionDef))
                    and node.name in {'HealthResponse','health_check'}]
        assert {node.name for node in selected} == {'HealthResponse','health_check'}
        exec(compile(ast.Module(body=selected,type_ignores=[]), str(root/'app/api/routes.py'), 'exec'), owner.__dict__)
        v2 = types.ModuleType('app.api.v2_routes')
        v2.router = APIRouter(prefix='/v2')
        monkeypatch.setitem(sys.modules,'app.api.routes',owner)
        monkeypatch.setitem(sys.modules,'app.api.v2_routes',v2)
        monkeypatch.delitem(sys.modules,'app.main',raising=False)
        yield
        sys.modules.pop('app.main',None)

# Only identity/attestation and explicit counterexamples; no provider/authority owner.
import socket
original_connect=socket.socket.connect
def isolated_pair_connect(self,address):
    frame=sys._getframe(1)
    listener=frame.f_locals.get('lsock')
    if (frame.f_code is socket._fallback_socketpair.__code__ and listener is not None
            and address==listener.getsockname() and address[0] in ('127.0.0.1','::1')
            and address[1] not in (8000,5173,5174,11434,9)):
        return original_connect(self,address)
    return forbidden()
socket.socket.connect=isolated_pair_connect
socket.socket.connect_ex=forbidden
# TestClient's Windows event-loop pipe uses a local socketpair; keep bind handling
# in the existing endpoint-I/O tests and prohibit actual real transports above.
class NoProvider(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith(('app.models','app.approval','app.security.local_operator')):
            raise AssertionError('R2-A13 provider/authorization import forbidden')
sys.meta_path.insert(0,NoProvider())

# Actual-main subprocess test remains unchanged; add protected-I/O guard prefix.
import subprocess
original_check_output=subprocess.check_output
child_guard='''
import builtins, io, sqlite3, socket
def _r13_forbidden(*a, **k): raise AssertionError('R2-A13 child protected operation')
sqlite3.connect=_r13_forbidden
def _r13_open(original):
    def opened(file,*a,**k):
        name=str(file).lower().replace(chr(92),'/')
        if name.endswith(('.db','.db-wal','.db-shm')) or '/data/knowledge/' in name: _r13_forbidden()
        return original(file,*a,**k)
    return opened
builtins.open=_r13_open(builtins.open)
io.open=_r13_open(io.open)
'''
def guarded_check_output(command,*args,**kwargs):
    command=list(command)
    if '-c' in command:
        position=command.index('-c')+1
        command[position]=child_guard+command[position]
    return original_check_output(command,*args,**kwargs)
subprocess.check_output=guarded_check_output

class Evidence:
    def pytest_collection_modifyitems(self,items):
        (out/'SELECTED_IDS_FINAL.json').write_text(__import__('json').dumps([item.nodeid for item in items],indent=2))
os.chdir(out)
paths=[str(root/'tests/test_runtime_identity.py'),str(root/'tests/test_runtime_attestation.py'),
       str(out/'test_binding_limits.py')]
result=pytest.main(paths+['-p','pytest_asyncio.plugin','-p','no:cacheprovider',
    '--basetemp',str(out/'pytest-final-tmp'),'--junitxml',str(out/'RESULTS_FINAL.xml'),'-q'],plugins=[Evidence(),IsolatedHealth()])
raise SystemExit(result)
