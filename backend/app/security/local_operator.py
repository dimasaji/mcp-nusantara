"""Windows local peer attribution. Disabled until a trusted policy is supplied.

No HTTP credentials, client reviewer field, application imports or storage access.
"""
from __future__ import annotations

import ctypes as c
from ctypes import wintypes as w
from dataclasses import dataclass
import json
import os
import re
import sys
import secrets
import threading
import time
from contextlib import contextmanager


class ActorError(ValueError):
    pass


_PEER_SEAL = object()


class VerifiedPeer:
    """Internal capability minted only after native IPC proof; never serialized."""
    __slots__ = ('_actor', '_server_pid', '_server_start', '_deadline', '_identity', '_seal')

    def __init__(self, actor, seal):
        if seal is not _PEER_SEAL:
            raise ActorError('NATIVE_IPC_PROOF_REQUIRED')
        object.__setattr__(self, '_actor', actor)
        object.__setattr__(self, '_server_pid', os.getpid())
        object.__setattr__(self, '_server_start', Windows().process_start(os.getpid()))
        object.__setattr__(self, '_deadline', time.monotonic() + 30)
        object.__setattr__(self, '_identity', object())
        object.__setattr__(self, '_seal', seal)

    def __setattr__(self, name, value):
        raise ActorError('IMMUTABLE_NATIVE_IPC_PROOF')

    def validate(self):
        if (self._seal is not _PEER_SEAL or self._server_pid != os.getpid()
                or self._server_start != Windows().process_start(os.getpid())
                or time.monotonic() >= self._deadline
                or Windows().process_actor(self._actor.pid) != self._actor):
            raise ActorError('STALE_NATIVE_IPC_PROOF')
        return self._actor

    def __repr__(self):
        return '<VerifiedPeer internal>'


@dataclass(frozen=True)
class Actor:
    sid: str
    logon_id: str
    session: int
    pid: int
    process_start: int
    interactive: bool


@dataclass(frozen=True)
class OperatorPolicy:
    sid: str
    logon_id: str
    session: int

    def permits(self, actor):
        return (actor.interactive and self.session > 0 and actor.session == self.session
                and actor.sid == self.sid and actor.logon_id == self.logon_id)


class Luid(c.Structure):
    _fields_ = [('low', w.DWORD), ('high', w.LONG)]


class Statistics(c.Structure):
    _fields_ = [('token_id', Luid), ('authentication_id', Luid), ('expires', c.c_longlong),
               ('token_type', w.DWORD), ('impersonation', w.DWORD), ('charged', w.DWORD),
               ('available', w.DWORD), ('groups', w.DWORD), ('privileges', w.DWORD), ('modified', Luid)]


class SidAttributes(c.Structure):
    _fields_ = [('sid', w.LPVOID), ('attributes', w.DWORD)]


class Groups(c.Structure):
    _fields_ = [('count', w.DWORD), ('first', SidAttributes)]


class SecurityAttributes(c.Structure):
    _fields_ = [('length', w.DWORD), ('descriptor', w.LPVOID), ('inherit', w.BOOL)]


class ProcessEntry(c.Structure):
    _fields_ = [('size', w.DWORD), ('usage', w.DWORD), ('pid', w.DWORD),
               ('heap', c.c_size_t), ('module', w.DWORD), ('threads', w.DWORD),
               ('parent_pid', w.DWORD), ('priority', w.LONG), ('flags', w.DWORD),
               ('exe', w.WCHAR * 260)]


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    parent_pid: int
    executable: str
    start: int



class Windows:
    def __init__(self):
        if sys.platform != 'win32':
            raise ActorError('WINDOWS_REQUIRED')
        self.k = c.WinDLL('kernel32', use_last_error=True)
        self.a = c.WinDLL('advapi32', use_last_error=True)
        signatures = {
            'GetCurrentProcess': ([], w.HANDLE), 'GetCurrentThread': ([], w.HANDLE),
            'CloseHandle': ([w.HANDLE], w.BOOL), 'LocalFree': ([w.HANDLE], w.HANDLE),
            'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            'GetProcessTimes': ([w.HANDLE] + [c.POINTER(w.FILETIME)] * 4, w.BOOL),
            'ProcessIdToSessionId': ([w.DWORD, c.POINTER(w.DWORD)], w.BOOL),
            'CreateNamedPipeW': ([w.LPCWSTR, w.DWORD, w.DWORD, w.DWORD, w.DWORD, w.DWORD,
                                  w.DWORD, c.POINTER(SecurityAttributes)], w.HANDLE),
            'ConnectNamedPipe': ([w.HANDLE, w.LPVOID], w.BOOL),
            'DisconnectNamedPipe': ([w.HANDLE], w.BOOL),
            'CreateFileW': ([w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.DWORD, w.HANDLE], w.HANDLE),
            'ReadFile': ([w.HANDLE, w.LPVOID, w.DWORD, c.POINTER(w.DWORD), w.LPVOID], w.BOOL),
            'WriteFile': ([w.HANDLE, w.LPVOID, w.DWORD, c.POINTER(w.DWORD), w.LPVOID], w.BOOL),
            'GetNamedPipeClientProcessId': ([w.HANDLE, c.POINTER(w.DWORD)], w.BOOL),
            'GetNamedPipeServerProcessId': ([w.HANDLE, c.POINTER(w.DWORD)], w.BOOL),
            'SetNamedPipeHandleState': ([w.HANDLE, c.POINTER(w.DWORD), w.LPVOID, w.LPVOID], w.BOOL),
            'QueryFullProcessImageNameW': ([w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)], w.BOOL),
            'CreateToolhelp32Snapshot': ([w.DWORD, w.DWORD], w.HANDLE),
            'Process32FirstW': ([w.HANDLE, c.POINTER(ProcessEntry)], w.BOOL),
            'Process32NextW': ([w.HANDLE, c.POINTER(ProcessEntry)], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            method = getattr(self.k, name)
            method.argtypes, method.restype = args, result
        auth = {
            'OpenProcessToken': ([w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)], w.BOOL),
            'OpenThreadToken': ([w.HANDLE, w.DWORD, w.BOOL, c.POINTER(w.HANDLE)], w.BOOL),
            'GetTokenInformation': ([w.HANDLE, c.c_int, w.LPVOID, w.DWORD, c.POINTER(w.DWORD)], w.BOOL),
            'ConvertSidToStringSidW': ([w.LPVOID, c.POINTER(w.LPWSTR)], w.BOOL),
            'ConvertStringSecurityDescriptorToSecurityDescriptorW':
                ([w.LPCWSTR, w.DWORD, c.POINTER(w.LPVOID), w.LPVOID], w.BOOL),
            'ImpersonateNamedPipeClient': ([w.HANDLE], w.BOOL),
            'RevertToSelf': ([], w.BOOL),
        }
        for name, (args, result) in auth.items():
            method = getattr(self.a, name)
            method.argtypes, method.restype = args, result

    @staticmethod
    def check(ok):
        if not ok:
            raise ActorError('WINDOWS_API_FAILURE_' + str(c.get_last_error()))

    def information(self, handle, kind):
        length = w.DWORD()
        self.a.GetTokenInformation(handle, kind, None, 0, c.byref(length))
        if not 0 < length.value < 1048576:
            raise ActorError('TOKEN_INFORMATION_UNAVAILABLE')
        buffer = c.create_string_buffer(length.value)
        self.check(self.a.GetTokenInformation(handle, kind, buffer, length, c.byref(length)))
        return buffer

    def sid_text(self, pointer):
        text = w.LPWSTR()
        self.check(self.a.ConvertSidToStringSidW(pointer, c.byref(text)))
        try:
            return text.value
        finally:
            self.k.LocalFree(c.cast(text, w.HANDLE))

    def process_start(self, pid):
        handle = self.k.OpenProcess(0x1000, False, pid)
        self.check(handle)
        try:
            times = [w.FILETIME() for _ in range(4)]
            self.check(self.k.GetProcessTimes(handle, *(c.byref(t) for t in times)))
            return (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        finally:
            self.k.CloseHandle(handle)

    def process_identity(self, pid):
        """Targeted OS metadata, independent of client PID/executable assertions."""
        handle = self.k.OpenProcess(0x1000, False, pid)
        self.check(handle)
        snapshot = None
        try:
            times = [w.FILETIME() for _ in range(4)]
            self.check(self.k.GetProcessTimes(handle, *(c.byref(t) for t in times)))
            start = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
            size = w.DWORD(32768)
            image = c.create_unicode_buffer(size.value)
            self.check(self.k.QueryFullProcessImageNameW(handle, 0, image, c.byref(size)))
            snapshot = self.k.CreateToolhelp32Snapshot(2, 0)
            if snapshot == c.c_void_p(-1).value:
                raise ActorError('PROCESS_SNAPSHOT_UNAVAILABLE')
            entry = ProcessEntry()
            entry.size = c.sizeof(entry)
            found = self.k.Process32FirstW(snapshot, c.byref(entry))
            while found:
                if entry.pid == pid:
                    return ProcessIdentity(pid, entry.parent_pid, image.value, start)
                found = self.k.Process32NextW(snapshot, c.byref(entry))
            raise ActorError('ACTUAL_PROCESS_NOT_FOUND')
        finally:
            if snapshot not in (None, c.c_void_p(-1).value):
                self.k.CloseHandle(snapshot)
            self.k.CloseHandle(handle)

    def process_actor(self, pid):
        handle = self.k.OpenProcess(0x1000, False, pid)
        self.check(handle)
        token = w.HANDLE()
        try:
            self.check(self.a.OpenProcessToken(handle, 8, c.byref(token)))
            return self.actor(token, pid)
        finally:
            if token.value:
                self.k.CloseHandle(token)
            self.k.CloseHandle(handle)

    def actor(self, token, pid, *, impersonated=False):
        user = self.information(token, 1)
        sid = self.sid_text(c.cast(user, c.POINTER(SidAttributes)).contents.sid)
        stats_buffer = self.information(token, 10)
        stats = c.cast(stats_buffer, c.POINTER(Statistics)).contents
        if impersonated and (stats.token_type != 2 or stats.impersonation < 2):
            raise ActorError('IMPERSONATION_IDENTITY_NOT_PROVEN')
        logon = f'{stats.authentication_id.high & 0xffffffff:08x}:{stats.authentication_id.low:08x}'
        session_buffer = self.information(token, 12)
        session = c.cast(session_buffer, c.POINTER(w.DWORD)).contents.value
        actual_session = w.DWORD()
        self.check(self.k.ProcessIdToSessionId(pid, c.byref(actual_session)))
        if session == 0 or session != actual_session.value or logon == '00000000:00000000':
            raise ActorError('INTERACTIVE_SESSION_NOT_PROVEN')
        buffer = self.information(token, 2)
        count = c.cast(buffer, c.POINTER(w.DWORD)).contents.value
        if count > 4096:
            raise ActorError('GROUP_COUNT_UNBOUNDED')
        groups = (SidAttributes * count).from_address(c.addressof(buffer) + Groups.first.offset)
        interactive = any(self.sid_text(g.sid) == 'S-1-5-4' and g.attributes & 4
                          and not g.attributes & 0x10 for g in groups)
        if not interactive:
            raise ActorError('INTERACTIVE_GROUP_REQUIRED')
        return Actor(sid, logon, session, pid, self.process_start(pid), True)

    def current_actor(self):
        handle = w.HANDLE()
        self.check(self.a.OpenProcessToken(self.k.GetCurrentProcess(), 8, c.byref(handle)))
        try:
            return self.actor(handle, os.getpid())
        finally:
            self.k.CloseHandle(handle)

    def write(self, handle, data):
        raw = json.dumps(data, separators=(',', ':'), allow_nan=False).encode()
        if len(raw) > 4096:
            raise ActorError('BOUNDED_MESSAGE_REQUIRED')
        sent = w.DWORD()
        self.check(self.k.WriteFile(handle, raw, len(raw), c.byref(sent), None))
        if sent.value != len(raw):
            raise ActorError('INCOMPLETE_MESSAGE')

    def read(self, handle):
        raw = c.create_string_buffer(4096)
        read = w.DWORD()
        self.check(self.k.ReadFile(handle, raw, 4096, c.byref(read), None))
        data = json.loads(raw.raw[:read.value])
        if not isinstance(data, dict):
            raise ActorError('OBJECT_REQUIRED')
        return data


def validate_name(name):
    if not re.fullmatch(r'\\\\\.\\pipe\\nusantara-r2-a9-[a-f0-9]{32}', name):
        raise ActorError('LOCAL_PIPE_REQUIRED')


class LocalOperatorChannel:
    """Explicitly constructed trusted channel; no policy discovery or auto-start."""
    def __init__(self, name, policy, *, challenge_ttl=30.0):
        validate_name(name)
        if not isinstance(policy, OperatorPolicy) or not re.fullmatch(r'S-1-(?:\d+-)*\d+', policy.sid):
            raise ActorError('EXPLICIT_OPERATOR_POLICY_REQUIRED')
        if policy.session <= 0 or not policy.logon_id:
            raise ActorError('EXPLICIT_OPERATOR_POLICY_REQUIRED')
        if isinstance(challenge_ttl, bool) or not 0 < challenge_ttl <= 30:
            raise ActorError('INVALID_CHALLENGE_TTL')
        self.api, self.name, self.policy = Windows(), name, policy
        self.handle = None
        self._ttl = challenge_ttl
        self._lock = threading.Lock()
        self._state = 'NEW'
        self._nonce = None
        self._deadline = 0.0
        self._actor = None

    def __enter__(self):
        if self._state != 'NEW' or self.handle is not None:
            raise ActorError('CHANNEL_ALREADY_USED')
        descriptor = w.LPVOID()
        self.api.check(self.api.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            'D:P(A;;GA;;;' + self.policy.sid + ')', 1, c.byref(descriptor), None))
        try:
            attributes = SecurityAttributes(c.sizeof(SecurityAttributes), descriptor, False)
            # Duplex, first-instance anti-squatting, message mode, reject remote clients.
            handle = self.api.k.CreateNamedPipeW(self.name, 3 | 0x80000, 4 | 2 | 8,
                                                 1, 4096, 4096, 1000, c.byref(attributes))
            if handle == c.c_void_p(-1).value:
                raise ActorError('PIPE_CREATION_FAILED')
            self.handle = handle
            return self
        finally:
            self.api.k.LocalFree(descriptor)

    def __exit__(self, *error):
        if self.handle is not None:
            self.api.k.DisconnectNamedPipe(self.handle)
            self.api.k.CloseHandle(self.handle)
            self.handle = None
        with self._lock:
            self._state, self._nonce, self._actor = 'TERMINAL', None, None

    @contextmanager
    def peer(self):
        pid = w.DWORD()
        self.api.check(self.api.k.GetNamedPipeClientProcessId(self.handle, c.byref(pid)))
        self.api.check(self.api.a.ImpersonateNamedPipeClient(self.handle))
        actor = None
        try:
            token = w.HANDLE()
            self.api.check(self.api.a.OpenThreadToken(self.api.k.GetCurrentThread(), 8, True, c.byref(token)))
            try:
                actor = self.api.actor(token, pid.value, impersonated=True)
            finally:
                self.api.k.CloseHandle(token)
        finally:
            self.api.check(self.api.a.RevertToSelf())
        if not self.policy.permits(actor):
            raise ActorError('OPERATOR_POLICY_MISMATCH')
        # Correlate impersonated identity to the actual OS pipe process primary token.
        # Client PID/identity fields are never a source of authority.
        if self.api.process_actor(actor.pid) != actor:
            raise ActorError('PEER_PROCESS_ACTOR_MISMATCH')
        # Handler runs only AFTER impersonation has been reverted.
        yield actor

    def serve_once(self, handler):
        with self._lock:
            if self._state != 'NEW' or self.handle is None:
                raise ActorError('CHANNEL_ALREADY_USED')
            self._state = 'CONNECTING'
        try:
            connected = self.api.k.ConnectNamedPipe(self.handle, None)
            if not connected and c.get_last_error() != 535:
                self.api.check(False)
            if self.api.read(self.handle) != {'protocol': 'R2-A9-IPC-1', 'phase': 'HELLO'}:
                raise ActorError('INVALID_HELLO')
            with self.peer() as actor:
                challenge = self._challenge(actor)
            self.api.write(self.handle, challenge)
            proof = self.api.read(self.handle)
            with self.peer() as actor:
                body = self._consume(actor, proof)
                reply = handler(actor, body)
            self.api.write(self.handle, reply)
        finally:
            with self._lock:
                self._state, self._nonce, self._actor = 'TERMINAL', None, None

    def serve_authenticated_once(self, handler):
        """The only adapter entry to backend authority; no caller-provided Actor."""
        return self.serve_once(lambda actor, body: handler(VerifiedPeer(actor, _PEER_SEAL), body))

    def _challenge(self, actor):
        with self._lock:
            if self._state != 'CONNECTING':
                raise ActorError('CHALLENGE_NOT_AVAILABLE')
            self._actor = actor
            self._nonce = secrets.token_hex(32)
            self._deadline = time.monotonic() + self._ttl
            self._state = 'CHALLENGED'
            return {'protocol': 'R2-A9-IPC-1', 'phase': 'CHALLENGE', 'nonce': self._nonce,
                    'server_pid': os.getpid(), 'server_start': self.api.process_start(os.getpid())}

    def _consume(self, actor, proof):
        with self._lock:
            valid = (self._state == 'CHALLENGED' and actor == self._actor
                     and time.monotonic() < self._deadline and isinstance(proof, dict)
                     and set(proof) == {'phase', 'nonce', 'body'} and proof['phase'] == 'PROOF'
                     and isinstance(proof['nonce'], str) and self._nonce is not None
                     and secrets.compare_digest(proof['nonce'], self._nonce))
            self._state, self._nonce, self._actor = 'TERMINAL', None, None
            if not valid:
                raise ActorError('IPC_PROOF_REJECTED')
            body = proof['body']
            if (not isinstance(body, dict) or set(body) & {
                    'reviewer', 'actor', 'sid', 'pid', 'session', 'logon_id',
                    'process_start', 'server_pid', 'authorization', 'token'}):
                raise ActorError('CLIENT_IDENTITY_CLAIM_REJECTED')
            return body


def operator_exchange(name, expected_pid, expected_start, body):
    validate_name(name)
    api = Windows()
    handle = api.k.CreateFileW(name, 0xc0000000, 0, None, 3, 0x120000, None)
    if handle == c.c_void_p(-1).value:
        raise ActorError('LOCAL_SERVER_UNAVAILABLE')
    try:
        pid = w.DWORD()
        api.check(api.k.GetNamedPipeServerProcessId(handle, c.byref(pid)))
        if pid.value != expected_pid or api.process_start(pid.value) != expected_start:
            raise ActorError('SERVER_PROCESS_NOT_BOUND')
        mode = w.DWORD(2)
        api.check(api.k.SetNamedPipeHandleState(handle, c.byref(mode), None, None))
        api.write(handle, {'protocol': 'R2-A9-IPC-1', 'phase': 'HELLO'})
        challenge = api.read(handle)
        if (set(challenge) != {'protocol', 'phase', 'nonce', 'server_pid', 'server_start'}
                or challenge['protocol'] != 'R2-A9-IPC-1' or challenge['phase'] != 'CHALLENGE'
                or challenge['server_pid'] != expected_pid or challenge['server_start'] != expected_start
                or not isinstance(challenge['nonce'], str)
                or not re.fullmatch('[a-f0-9]{64}', challenge['nonce'])):
            raise ActorError('SERVER_CHALLENGE_NOT_BOUND')
        api.write(handle, {'phase': 'PROOF', 'nonce': challenge['nonce'], 'body': body})
        return api.read(handle)
    finally:
        api.k.CloseHandle(handle)
