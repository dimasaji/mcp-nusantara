"""Guarded V1 tests; never compose real worker/store/model dependencies."""
import builtins
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
mode = sys.argv[1]
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
run = OUT / (mode + '-' + stamp)
run.mkdir(exist_ok=False)
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['TEMP'] = os.environ['TMP'] = str(run)
violations = []
def prohibited(*args, **kwargs):
    violations.append('EXTERNAL_EFFECT_BLOCKED')
    raise AssertionError('EXTERNAL_EFFECT_BLOCKED')
sqlite3.connect = prohibited
os.system = prohibited
original_popen = subprocess.Popen.__init__
identity_script = ('import json; from app.core.runtime_identity import current_runtime_instance; '
                   'from dataclasses import asdict; print(json.dumps(asdict(current_runtime_instance())))')
def identity_subprocess_only(self, args, *positional, **kwargs):
    if args == [sys.executable, '-B', '-c', identity_script] and not kwargs.get('shell'):
        return original_popen(self, args, *positional, **kwargs)
    return prohibited()
subprocess.Popen.__init__ = identity_subprocess_only
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
            if path.is_relative_to(ROOT / 'data') or path.is_relative_to(ROOT / '.dev') and path.suffix in ('.db', '.db-wal', '.db-shm'):
                prohibited()
            if any(c in str(mode) for c in 'wax+') and not path.is_relative_to(OUT):
                prohibited()
        return original(file, mode, *args, **kwargs)
    return opened
builtins.open = guarded(builtins.open)
io.open = guarded(io.open)
import httpx
httpx.HTTPTransport.handle_request = prohibited
httpx.AsyncHTTPTransport.handle_async_request = prohibited
os.chdir(OUT)  # capture identity at the same working directory used by tests
import isolated_runtime
import pytest
paths = ['tests/test_v1_operator_control.py', 'tests/test_v1_response_projection.py']
if mode == 'regression':
    paths += ['tests/test_configuration_contract.py', 'tests/test_model_router_configuration.py',
        'tests/test_provider_identity.py', 'tests/test_configuration_integration.py',
        'tests/test_effective_rag_profile.py', 'tests/test_gate_integration.py', 'tests/test_gates_8_16.py',
        'tests/test_phase4_v1_chat_runtime.py', 'tests/test_phase3_v1_metrics_integration.py',
        'tests/test_phase4_trust_contract.py', 'tests/v2/test_devcore_grounding_response.py']
os.chdir(OUT)
result = pytest.main([str(ROOT / p) for p in paths] + ['-q', '-p', 'pytest_asyncio.plugin',
    '-p', 'no:cacheprovider', '-k', 'not guarded_api_assembly_and_public_regression',
    '-o', 'log_file=' + str(run / 'log.txt'), '--basetemp', str(run / 'temporary'),
    '--junitxml', str(run / 'results.xml')])
(run / 'guards.json').write_text(json.dumps({'pytest_exit': int(result), 'violations': violations,
    'network': 'BLOCKED_EXCEPT_STDLIB_SOCKETPAIR', 'sqlite': 'BLOCKED', 'subprocess': 'ONLY_EXACT_READ_ONLY_IDENTITY_PROBE',
    'writes': 'NEW_EVIDENCE_DIRECTORY_ONLY', 'semantic_and_retrieval': 'EXPLICIT_FIXTURES',
    'provider': 'ACTUAL_OLLAMA_ADAPTER_WITH_MOCK_TRANSPORT', 'v2': 'NOT_EXERCISED',
    'deselected': 'One pre-existing nested subprocess assembly test incompatible with this guard'}, indent=2))
print('EVIDENCE_RUN=' + str(run))
raise SystemExit(result if not violations else 1)
