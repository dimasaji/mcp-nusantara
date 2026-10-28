"""Run only two unchanged B2 acceptance cases and two bounded observer regressions."""
import builtins
import importlib.abc
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import sys

root=Path(__file__).resolve().parents[3]
out=Path(__file__).parent
prior=root/'docs/reports/r2-a11-phase-b2-20261008-9fb4e38a'
sys.path[:0]=[str(root),str(prior)]
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
violations=[]
def prohibited(*args,**kwargs):
    violations.append('FORBIDDEN_RUNTIME_OPERATION')
    raise AssertionError('FORBIDDEN_RUNTIME_OPERATION')
sqlite3.connect=prohibited
socket.socket.connect=prohibited
socket.socket.connect_ex=prohibited
socket.socket.bind=prohibited
socket.socket.listen=prohibited
def guarded(original):
    def opened(file,*args,**kwargs):
        name=str(file).lower().replace('\\','/')
        if name.endswith(('.db','.db-wal','.db-shm')) or '/data/knowledge/' in name:
            prohibited()
        return original(file,*args,**kwargs)
    return opened
builtins.open=guarded(builtins.open)
io.open=guarded(io.open)
class ProtectedImports(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith(('app.knowledge','app.rag','app.language','app.api.control_plane',
            'app.api.v2_routes','app.security.local_operator','app.approval.runtime_authorization')):
            prohibited()
sys.meta_path.insert(0,ProtectedImports())
import httpx
httpx.HTTPTransport.handle_request=prohibited
httpx.AsyncHTTPTransport.handle_async_request=prohibited
from app.models.ollama import OllamaProvider
for method in ('generate','generate_structured','health_check','list_models'):
    setattr(OllamaProvider,method,prohibited)
from app.core.runtime_correlation import OneUseAuthorization
for method in ('grant','reserve','dispatch'):
    setattr(OneUseAuthorization,method,prohibited)
import pytest
class Evidence:
    def pytest_collection_modifyitems(self,items):
        (out/'SELECTED_IDS.json').write_text(json.dumps([item.nodeid for item in items],indent=2))
os.chdir(out)
selected=[str(prior/'test_b2_integration.py')+'::test_incomplete_process_observer_fails_closed[result0]',
          str(prior/'test_b2_integration.py')+'::test_incomplete_process_observer_fails_closed[None]',
          str(out/'test_observer_regression.py')]
result=pytest.main(selected+['-p','pytest_asyncio.plugin','-p','no:cacheprovider',
    '--basetemp',str(out/'pytest-tmp'),'--junitxml',str(out/'RESULTS.xml'),'-q'],plugins=[Evidence()])
(out/'GUARDS.json').write_text(json.dumps({'violations':violations,'pytest_exit':int(result),
    'live_http':False,'provider_dispatch':False,'test_selection':'2 original B2 + 2 bounded observer regression cases'},indent=2))
raise SystemExit(result if not violations else 1)
