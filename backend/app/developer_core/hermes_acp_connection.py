"""ACP discovery only: no authenticate, session/new, prompt or tool execution.

No ACP dependency is added to the Nusantara interpreter. A server-owned path
selects the Hermes Python subprocess, avoiding the stale global launcher.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
from datetime import datetime, timezone

PROBE_TIMEOUT = 30.0
MAX_LINE = 65536
MAX_OUTPUT = 262144
_lock = threading.Lock()
_last = None


def _now():
    return datetime.now(timezone.utc).isoformat()


def state():
    with _lock:
        if _last is None:
            return {
                'status': 'NOT_CHECKED', 'checked_at': None,
                'reason': 'Koneksi ACP belum diperiksa oleh backend ini.',
                'scope': 'ACP_INITIALIZE_ONLY', 'task_execution_enabled': False,
                'integration_status': 'CONNECTION_ONLY',
            }
        return dict(_last)


def _command():
    # No command, arguments, environment or working directory from HTTP input.
    configured = os.environ.get('NUSANTARA_HERMES_ROOT', '')
    if configured:
        root = Path(configured).expanduser()
        if not root.is_absolute():
            raise ValueError('HERMES_ROOT_MUST_BE_ABSOLUTE')
    else:
        local = os.environ.get('LOCALAPPDATA')
        if os.name != 'nt' or not local:
            raise ValueError('HERMES_ROOT_NOT_CONFIGURED')
        root = Path(local) / 'hermes' / 'hermes-agent'
    root = root.resolve(strict=True)
    python = root / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    entry = root / 'hermes_cli' / 'main.py'
    if not python.is_file() or not entry.is_file():
        raise ValueError('HERMES_INSTALLATION_NOT_FOUND')
    return root, [str(python), '-c', 'from hermes_cli.main import main; main()', 'acp']


def _reader(stream, output):
    total = 0
    try:
        while True:
            line = stream.readline(MAX_LINE + 1)
            if not line:
                output.put(('closed', None))
                return
            total += len(line)
            if len(line) > MAX_LINE or total > MAX_OUTPUT:
                output.put(('limit', None))
                return
            output.put(('line', line))
    except (OSError, ValueError):
        output.put(('closed', None))


def _classify_stderr(stderr: str) -> str:
    """Convert subprocess diagnostics to a small safe public error vocabulary."""
    detail = stderr.casefold()
    if 'install state is not writable by this user' in detail or (
        '.prepare.lock' in detail and ('permission denied' in detail or 'access is denied' in detail)
    ):
        return 'HERMES_INSTALL_STATE_NOT_WRITABLE'
    if 'modulenotfounderror' in detail or 'no module named' in detail or 'cannot import name' in detail:
        return 'HERMES_DEPENDENCY_UNAVAILABLE'
    return 'ACP_CONNECTION_CLOSED'


def _drain_stderr(events) -> str:
    lines = []
    total = 0
    while True:
        try:
            kind, line = events.get_nowait()
        except queue.Empty:
            break
        if kind == 'line' and line is not None and total < MAX_OUTPUT:
            lines.append(line)
            total += len(line)
    return ''.join(lines)


def _cleanup(process):
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)
    for stream in (process.stdin, process.stdout, process.stderr):
        if stream:
            stream.close()


def _exchange(command, cwd, *, timeout=PROBE_TIMEOUT):
    """Read one matching initialize response while keeping stdin open."""
    env = os.environ.copy()
    # Do not hand Nusantara's operator/provider credentials to this subprocess.
    # Hermes uses its own installed config; no model request is made here.
    for key in tuple(env):
        if key.startswith('NUSANTARA_') or key in {
            'OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
            'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV',
        }:
            env.pop(key, None)
    process = subprocess.Popen(
        command, cwd=str(cwd), env=env, shell=False,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        # Never expose Hermes logs/config/secrets in a browser response.
        stderr=subprocess.PIPE,
        text=True, encoding='utf-8', errors='replace', bufsize=1,
    )
    events = queue.Queue()
    reader = threading.Thread(target=_reader, args=(process.stdout, events), daemon=True)
    stderr_events = queue.Queue()
    stderr_reader = threading.Thread(target=_reader, args=(process.stderr, stderr_events), daemon=True)
    reader.start()
    stderr_reader.start()
    request = {
        'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
        'params': {'protocolVersion': 1, 'clientCapabilities': {},
                   'clientInfo': {'name': 'nusantara-control-plane', 'version': '1.0'}},
    }
    try:
        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError('ACP_INITIALIZE_TIMEOUT')
            try:
                kind, line = events.get(timeout=min(0.25, remaining))
            except queue.Empty:
                if process.poll() is not None:
                    raise ValueError('ACP_PROCESS_EXITED')
                continue
            if kind == 'limit':
                raise ValueError('ACP_OUTPUT_LIMIT')
            if kind == 'closed':
                try:
                    process.wait(timeout=min(1.0, max(0.1, remaining)))
                except subprocess.TimeoutExpired:
                    pass
                stderr_reader.join(timeout=1)
                raise ValueError(_classify_stderr(_drain_stderr(stderr_events)))
            try:
                response = json.loads(line)
            except (ValueError, TypeError):
                raise ValueError('ACP_INVALID_JSON') from None
            if not isinstance(response, dict) or response.get('jsonrpc') != '2.0':
                raise ValueError('ACP_INVALID_RESPONSE')
            if response.get('id') != 1:
                # No requests from the agent are executed by this client.
                if 'method' in response and 'id' in response:
                    process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': response['id'],
                        'error': {'code': -32601, 'message': 'Discovery only; client capabilities disabled'}}) + '\n')
                    process.stdin.flush()
                continue
            if 'error' in response:
                raise ValueError('ACP_INITIALIZE_REJECTED')
            result = response.get('result')
            if not isinstance(result, dict) or type(result.get('protocolVersion')) is not int or result['protocolVersion'] != 1:
                raise ValueError('ACP_PROTOCOL_NOT_SUPPORTED')
            info = result.get('agentInfo')
            if not isinstance(info, dict) or info.get('name') != 'hermes-agent':
                raise ValueError('ACP_UNEXPECTED_AGENT')
            version = info.get('version')
            if not isinstance(version, str) or not version or len(version) > 80 or any(ord(c) < 32 for c in version):
                raise ValueError('ACP_INVALID_AGENT_VERSION')
            auth = result.get('authMethods', [])
            return {
                'agent_name': 'hermes-agent', 'agent_version': version,
                'protocol_version': 1,
                'openrouter_auth_advertised': isinstance(auth, list) and any(
                    isinstance(item, dict) and item.get('id') == 'openrouter' for item in auth),
                'response_sha256': hashlib.sha256(line.encode('utf-8')).hexdigest(),
            }
    finally:
        _cleanup(process)
        reader.join(timeout=1)
        stderr_reader.join(timeout=1)


def probe():
    global _last
    # Deliberate, user-triggered probe only. GET never spawns a process.
    if not _lock.acquire(blocking=False):
        return {'status': 'BUSY', 'reason': 'Pemeriksaan ACP lain masih berjalan.',
                'task_execution_enabled': False, 'scope': 'ACP_INITIALIZE_ONLY'}
    try:
        try:
            root, command = _command()
            observed = _exchange(command, root)
            record = {'status': 'CONNECTED', 'reason': 'Handshake ACP berhasil dari proses backend.', **observed}
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            known = str(exc)
            code = known if known.startswith(('ACP_', 'HERMES_')) and len(known) < 100 else 'HERMES_PROCESS_UNAVAILABLE'
            record = {'status': 'UNAVAILABLE', 'reason': code}
        _last = {**record, 'checked_at': _now(), 'scope': 'ACP_INITIALIZE_ONLY',
                 'source': 'backend ACP initialize response',
                 'task_execution_enabled': False, 'integration_status': 'CONNECTION_ONLY',
                 'runtime_identity': 'NOT_VERIFIED', 'cost_ledger_integrated': False}
        return dict(_last)
    finally:
        _lock.release()
