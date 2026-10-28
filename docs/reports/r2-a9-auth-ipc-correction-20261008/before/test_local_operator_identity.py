"""Real Windows local IPC in isolated test processes, never application service."""
import json
import os
import subprocess
import sys
from dataclasses import replace
from uuid import uuid4

import pytest

from app.security.local_operator import (ActorError, LocalOperatorChannel, OperatorPolicy,
                                         Windows, operator_exchange, validate_name)

pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Windows feasibility required')


def test_actual_windows_peer_session_and_server_binding():
    api = Windows()
    own = api.current_actor()
    assert own.interactive and own.session > 0 and own.process_start > 0
    name = r'\\.\pipe\nusantara-r2-a9-' + uuid4().hex
    policy = OperatorPolicy(own.sid, own.logon_id, own.session)
    child = None
    with LocalOperatorChannel(name, policy) as channel:
        # Child's claim is deliberately forged. Actual actor must come from impersonated OS peer.
        code = ('import json; from app.security.local_operator import operator_exchange; '
                f'print(json.dumps(operator_exchange({name!r},{os.getpid()},{own.process_start},'
                '{"reviewer":"FORGED","probe":"isolated"})))')
        child = subprocess.Popen([sys.executable, '-B', '-c', code], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
        try:
            def handle(actor, body):
                assert actor.pid == child.pid and actor.pid != os.getpid()
                assert policy.permits(actor) and body['reviewer'] == 'FORGED'
                assert actor.sid != body['reviewer']
                assert not replace(policy, session=own.session + 1).permits(actor)
                assert not replace(policy, sid='S-1-5-18').permits(actor)
                # No thread impersonation leaks into handler.
                from ctypes import wintypes as w
                import ctypes
                token = w.HANDLE()
                assert not api.a.OpenThreadToken(api.k.GetCurrentThread(), 8, True, ctypes.byref(token))
                assert ctypes.get_last_error() == 1008
                return {'os_peer_verified': True, 'session_bound': True, 'client_pid': actor.pid,
                        'server_pid': os.getpid(), 'impersonation_reverted': True}
            channel.serve_once(handle)
            out, err = child.communicate(timeout=5)
            assert child.returncode == 0, err
            assert json.loads(out)['os_peer_verified'] is True
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=5)


def test_local_only_names_and_explicit_policy():
    for name in [r'\\REMOTE\pipe\anything', r'\\.\pipe\anything', 'http://127.0.0.1:8000']:
        with pytest.raises(ActorError):
            validate_name(name)
    with pytest.raises(ActorError):
        LocalOperatorChannel(r'\\.\pipe\nusantara-r2-a9-' + uuid4().hex, None)


def test_pipe_first_instance_cannot_be_replaced():
    actor = Windows().current_actor()
    policy = OperatorPolicy(actor.sid, actor.logon_id, actor.session)
    name = r'\\.\pipe\nusantara-r2-a9-' + uuid4().hex
    with LocalOperatorChannel(name, policy):
        with pytest.raises(ActorError):
            with LocalOperatorChannel(name, policy):
                pass
