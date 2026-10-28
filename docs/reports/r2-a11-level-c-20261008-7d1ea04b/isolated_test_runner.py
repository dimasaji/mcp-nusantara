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

from app.core.runtime_correlation import OneUseAuthorization
from app.models.ollama import OllamaProvider
from app.security.local_operator import LocalOperatorChannel
OneUseAuthorization.grant = forbidden
OllamaProvider.generate = forbidden
OllamaProvider.generate_structured = forbidden
OllamaProvider.health_check = forbidden
OllamaProvider.list_models = forbidden
LocalOperatorChannel.__enter__ = forbidden
OneUseAuthorization.reserve = forbidden
OneUseAuthorization.dispatch = forbidden
from app.api.runtime_verification import VerificationController

os.chdir(out)
prior=root/'docs/reports/r2-a11-phase-b2-20261008-9fb4e38a'
sys.path.insert(0,str(prior))
mode=sys.argv[1] if len(sys.argv)>1 else 'focused'
class Evidence:
    def pytest_collection_modifyitems(self,items):
        (out/(mode+'_IDS.json')).write_text(__import__('json').dumps([item.nodeid for item in items],indent=2),encoding='utf-8')
paths=[str(prior/'test_b2_integration.py'),str(out/'test_context_failure.py')]
extra=[]
if mode=='regression':
    paths=[str(root/p) for p in ['tests/test_runtime_correlation.py','tests/test_runtime_verification.py',
        'tests/test_runtime_attestation.py','tests/test_control_plane_attestation_binding.py']]
    extra=['-k','receipt_assessment or normal_app_composition or existing_public_v1_v2 or '
        'guarded_application_composition or live_handler_code_changes or endpoint_does_not_open or '
        'new_processes_have_distinct']
raise SystemExit(pytest.main(paths+extra+['-p','pytest_asyncio.plugin','-p','no:cacheprovider',
 '--basetemp',str(out/(mode+'-tmp')),'--junitxml',str(out/(mode+'.xml')),'-q'],plugins=[Evidence()]))
