"""Current-source checks; writes restricted to this fresh evidence directory."""
import ast
import builtins
import hashlib
import importlib.abc
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
mode = sys.argv[1]
assert mode in ('targeted', 'regression')
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
temporary = OUT / (mode + '-temporary')
temporary.mkdir(exist_ok=False)
os.environ['TEMP'] = os.environ['TMP'] = str(temporary)
violations = []

def prohibited(*args, **kwargs):
    violations.append('PROHIBITED_EXTERNAL_EFFECT')
    raise AssertionError('PROHIBITED_EXTERNAL_EFFECT')

sqlite3.connect = prohibited
os.system = prohibited
subprocess.Popen.__init__ = prohibited
original_connect = socket.socket.connect

def socketpair_only(self, address):
    frame = sys._getframe(1)
    listener = frame.f_locals.get('lsock')
    if (frame.f_code is socket._fallback_socketpair.__code__ and listener is not None
            and address == listener.getsockname() and address[0] in ('127.0.0.1', '::1')):
        return original_connect(self, address)
    return prohibited()

socket.socket.connect = socketpair_only
socket.socket.connect_ex = prohibited

def guarded(original):
    def opened(file, mode='r', *args, **kwargs):
        if isinstance(file, (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(file)).resolve()
            if path.is_relative_to(ROOT / 'data') or path.is_relative_to(ROOT / '.dev'):
                prohibited()
            if any(c in str(mode) for c in 'wax+') and not path.is_relative_to(OUT):
                prohibited()
        return original(file, mode, *args, **kwargs)
    return opened

builtins.open = guarded(builtins.open)
io.open = guarded(io.open)

class ForbiddenOwners(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'app.main' or fullname.startswith(('app.api', 'app.language', 'app.knowledge', 'app.core.control_plane_projection')):
            prohibited()

sys.meta_path.insert(0, ForbiddenOwners())
import httpx
httpx.HTTPTransport.handle_request = prohibited
httpx.AsyncHTTPTransport.handle_async_request = prohibited

route_path = ROOT / 'app/api/routes.py'
test_path = ROOT / 'tests/test_v1_response_projection.py'
nodes = ast.parse(route_path.read_text(encoding='utf-8')).body
selected = [n for n in nodes if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and
            (n.name.startswith('_PublicChat') or n.name == '_project_v1_chat_response')]
tests = []
for node in ast.parse(test_path.read_text(encoding='utf-8')).body:
    if isinstance(node, ast.FunctionDef) and node.name == 'controlled_pipeline':
        break
    if isinstance(node, (ast.FunctionDef, ast.Assign)):
        tests.append(node)
projection = OUT / ('test_projection_' + mode + '.py')
prefix = 'from copy import deepcopy\nfrom types import SimpleNamespace\nfrom typing import Literal\nimport json\nimport pytest\nfrom pydantic import BaseModel, ConfigDict, Field, ValidationError\n'
source = prefix + ast.unparse(ast.Module(body=selected, type_ignores=[])) + '\nroutes = SimpleNamespace(_project_v1_chat_response=_project_v1_chat_response)\n' + ast.unparse(ast.Module(body=tests, type_ignores=[]))
with projection.open('x', encoding='utf-8') as stream:
    stream.write(source)

import pytest
paths = [projection]
if mode == 'regression':
    paths += [ROOT / p for p in ('tests/test_configuration_contract.py',
        'tests/test_model_router_configuration.py', 'tests/test_gate_integration.py',
        'tests/test_gates_8_16.py', 'tests/v2/test_devcore_grounding_response.py')]
os.chdir(OUT)
result = pytest.main([str(p) for p in paths] + ['-q', '-p', 'no:cacheprovider',
    '-o', 'log_file=' + str(OUT / (mode + '-log.txt')),
    '--basetemp', str(temporary / 'pytest'), '--junitxml', str(OUT / (mode + '-results.xml'))])
with (OUT / (mode + '-guards.json')).open('x', encoding='utf-8') as stream:
    json.dump({'pytest_exit': int(result), 'violations': violations,
        'real_application_startup': 'BLOCKED', 'network': 'BLOCKED_EXCEPT_STDLIB_SOCKETPAIR',
        'database': 'BLOCKED', 'subprocess': 'BLOCKED', 'writes': 'NEW_EVIDENCE_DIRECTORY_ONLY',
        'projection_method': 'Existing public classes/function and existing pure tests extracted with AST; no HTTP route composition',
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (route_path, test_path)},
        'full_v1_regression': 'NOT_RUN; selected pure regression only; no provider/worker/store/runtime E2E proof'}, stream, indent=2)
raise SystemExit(result if not violations else 1)
