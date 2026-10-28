"""Pre-implementation OS/session feasibility only; no application imports or IPC."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
import sys


def probe():
    if sys.platform != 'win32':
        return {'feasible': False, 'blocker': 'WINDOWS_REQUIRED'}
    kernel = c.WinDLL('kernel32', use_last_error=True)
    advapi = c.WinDLL('advapi32', use_last_error=True)
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.LocalFree.argtypes = [w.HANDLE]
    advapi.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)]
    advapi.GetTokenInformation.argtypes = [w.HANDLE, c.c_int, w.LPVOID, w.DWORD, c.POINTER(w.DWORD)]
    advapi.ConvertSidToStringSidW.argtypes = [w.LPVOID, c.POINTER(w.LPWSTR)]
    kernel.ProcessIdToSessionId.argtypes = [w.DWORD, c.POINTER(w.DWORD)]

    class Luid(c.Structure):
        _fields_ = [('low', w.DWORD), ('high', w.LONG)]

    class Statistics(c.Structure):
        _fields_ = [('token_id', Luid), ('authentication_id', Luid),
                   ('expires', c.c_longlong), ('token_type', w.DWORD),
                   ('impersonation', w.DWORD), ('charged', w.DWORD),
                   ('available', w.DWORD), ('groups', w.DWORD),
                   ('privileges', w.DWORD), ('modified', Luid)]

    class SidAttributes(c.Structure):
        _fields_ = [('sid', w.LPVOID), ('attributes', w.DWORD)]

    class Groups(c.Structure):
        _fields_ = [('count', w.DWORD), ('first', SidAttributes)]

    def checked(ok):
        if not ok:
            raise c.WinError(c.get_last_error())

    def information(handle, kind):
        needed = w.DWORD()
        advapi.GetTokenInformation(handle, kind, None, 0, c.byref(needed))
        if not 0 < needed.value < 1048576:
            raise RuntimeError('TOKEN_INFORMATION_UNAVAILABLE')
        buffer = c.create_string_buffer(needed.value)
        checked(advapi.GetTokenInformation(handle, kind, buffer, needed, c.byref(needed)))
        return buffer

    def sid_text(pointer):
        value = w.LPWSTR()
        checked(advapi.ConvertSidToStringSidW(pointer, c.byref(value)))
        try:
            return value.value
        finally:
            kernel.LocalFree(c.cast(value, w.HANDLE))

    handle = w.HANDLE()
    checked(advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, c.byref(handle)))
    try:
        user = information(handle, 1)
        sid = sid_text(c.cast(user, c.POINTER(SidAttributes)).contents.sid)
        stats = c.cast(information(handle, 10), c.POINTER(Statistics)).contents
        logon_id = f'{stats.authentication_id.high & 0xffffffff:08x}:{stats.authentication_id.low:08x}'
        token_session = c.cast(information(handle, 12), c.POINTER(w.DWORD)).contents.value
        process_session = w.DWORD()
        checked(kernel.ProcessIdToSessionId(os.getpid(), c.byref(process_session)))
        groups = information(handle, 2)
        count = c.cast(groups, c.POINTER(w.DWORD)).contents.value
        if count > 4096:
            raise RuntimeError('GROUP_COUNT_UNBOUNDED')
        entries = (SidAttributes * count).from_address(c.addressof(groups) + Groups.first.offset)
        interactive = any(sid_text(item.sid) == 'S-1-5-4' and
                          item.attributes & 0x4 and not item.attributes & 0x10 for item in entries)
        feasible = bool(sid and logon_id != '00000000:00000000' and interactive and
                        token_session > 0 and token_session == process_session.value)
        return {'feasible': feasible, 'source': 'WINDOWS_PROCESS_TOKEN_API',
                'isolated_probe_pid': os.getpid(), 'actor_sid_sha256': hashlib.sha256(sid.encode()).hexdigest(),
                'token_session': token_session, 'process_session': process_session.value,
                'logon_session_observed': bool(logon_id != '00000000:00000000'),
                'interactive_group_enabled': bool(interactive),
                'blocker': None if feasible else 'TRUSTED_INTERACTIVE_SESSION_NOT_PROVEN',
                'live_application_observed': False, 'named_pipe_peer_observed': False}
    finally:
        kernel.CloseHandle(handle)


if __name__ == '__main__':
    try:
        result = probe()
    except Exception as error:
        result = {'feasible': False, 'blocker': 'WINDOWS_TOKEN_PROBE_FAILED',
                  'error_type': type(error).__name__, 'winerror': getattr(error, 'winerror', None)}
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result['feasible'] else 3)
