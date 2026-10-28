"""Local, GET-only process observation; no configuration, provider or DB access."""
from __future__ import annotations

import hashlib
import json
import marshal
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request

from app.core.runtime_identity import BUILD_ID, current_runtime_instance

ATTESTATION_PATH = '/v1/runtime/attestation'
_LOOPBACK = {'127.0.0.1', '::1', 'localhost'}


def _process_identity() -> dict:
    """Capture OS start/image once; unavailable metadata is never fabricated."""
    identity = {
        'process_id': os.getpid(), 'parent_process_id': os.getppid(),
        'process_start_time': None, 'working_directory': None,
        'executable_path': None, 'interpreter_path': sys.executable,
        'os_metadata_source': 'UNAVAILABLE',
    }
    try:
        identity['working_directory'] = os.getcwd()
    except OSError:
        pass
    try:
        if sys.platform == 'win32':
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            handle = kernel.GetCurrentProcess()
            kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
            kernel.GetProcessTimes.restype = wintypes.BOOL
            times = [wintypes.FILETIME() for _ in range(4)]
            if kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
                ticks = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
                started = datetime.fromtimestamp((ticks - 116444736000000000) / 10000000, timezone.utc)
                identity['process_start_time'] = started.isoformat()
            kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                         wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
            kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                identity['executable_path'] = buffer.value
            identity['os_metadata_source'] = 'WINDOWS_CURRENT_PROCESS_API'
        elif sys.platform.startswith('linux'):
            stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
            boot = next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines()
                        if line.startswith('btime '))
            started = datetime.fromtimestamp(boot + int(stat[19]) / os.sysconf('SC_CLK_TCK'), timezone.utc)
            identity['process_start_time'] = started.isoformat()
            identity['executable_path'] = os.readlink('/proc/self/exe')
            identity['os_metadata_source'] = 'LINUX_CURRENT_PROCESS_PROCFS'
    except (OSError, ValueError, StopIteration, IndexError, AttributeError):
        pass
    return identity


def _loaded_code_manifest(application: FastAPI) -> tuple:
    """Hash actual code objects, not disk files; explicitly scoped/non-transitive."""
    manifest = []
    for route in application.routes:
        endpoint = getattr(route, 'endpoint', None)
        code = getattr(endpoint, '__code__', None)
        if code is not None:
            methods = ','.join(sorted(getattr(route, 'methods', ()) or ()))
            label = f"route:{methods}:{route.path}:{endpoint.__module__}.{endpoint.__qualname__}"
            manifest.append((label, hashlib.sha256(marshal.dumps(code)).hexdigest()))
    for middleware in application.user_middleware:
        dispatch = middleware.kwargs.get('dispatch')
        code = getattr(dispatch, '__code__', None)
        if code is not None:
            label = f'middleware:{dispatch.__module__}.{dispatch.__qualname__}'
            manifest.append((label, hashlib.sha256(marshal.dumps(code)).hexdigest()))
    for function in (current_runtime_instance, _process_identity, _loaded_code_manifest, _manifest_hash,
                     install_runtime_attestation):
        manifest.append((f'identity:{function.__module__}.{function.__qualname__}',
                         hashlib.sha256(marshal.dumps(function.__code__)).hexdigest()))
    return tuple(sorted(manifest))


def _manifest_hash(manifest: tuple) -> str:
    return 'sha256:' + hashlib.sha256(json.dumps(manifest, separators=(',', ':')).encode()).hexdigest()


def install_runtime_attestation(application: FastAPI, *, entrypoint: str) -> None:
    """Bind one observation surface to this initialized application/process."""
    if any(getattr(route, 'path', None) == ATTESTATION_PATH for route in application.routes):
        raise ValueError('ATTESTATION_ENDPOINT_ALREADY_REGISTERED')
    process = _process_identity()
    instance = current_runtime_instance()
    app_identity = {'service_name': application.title, 'service_version': application.version,
                    'application_entrypoint': entrypoint}

    @application.get(ATTESTATION_PATH, tags=['runtime-attestation'])
    async def runtime_attestation(request: Request):
        if (not request.client or request.client.host not in _LOOPBACK
                or request.url.hostname not in _LOOPBACK or request.url.port != 8000):
            raise HTTPException(403, 'Runtime attestation is restricted to the local runtime on port 8000')
        origin = request.headers.get('origin')
        if origin:
            try:
                parsed = urlsplit(origin)
                local_origin = parsed.scheme == 'http' and parsed.hostname in _LOOPBACK and parsed.port == 8000
            except ValueError:
                local_origin = False
            if not local_origin:
                raise HTTPException(403, 'Non-runtime origin rejected')
        current = current_runtime_instance()
        process_bound = (process['process_id'] == os.getpid()
                         and instance.runtime_instance_id == current.runtime_instance_id)
        current_manifest = _loaded_code_manifest(application)
        code_bound = current_manifest == startup_manifest
        return {
            'attestation': {
                'application': dict(app_identity),
                'process': {**process, 'observed_process_id': os.getpid(),
                            'valid_for_current_process': process_bound},
                'runtime_instance_id': current.runtime_instance_id,
                'instance_captured_at': current.captured_at,
                'build': {
                    'loaded_code_hash': _manifest_hash(startup_manifest),
                    'current_registered_code_hash': _manifest_hash(current_manifest),
                    'loaded_code_binding': 'MATCH' if code_bound and process_bound else 'NOT_VERIFIED',
                    'coverage': 'REGISTERED_PYTHON_HANDLERS_HTTP_DISPATCH_AND_IDENTITY_FUNCTIONS',
                    'limitations': 'Non-transitive code objects; excludes globals, closures, assets and provider dependencies',
                    'source_build_hash': BUILD_ID,
                    'source_build_evidence': 'IMPORT_TIME_SOURCE_SNAPSHOT_ONLY',
                    'full_application_build_verified': False,
                    'loaded_code_manifest': [{'symbol': name, 'code_sha256': value}
                                             for name, value in startup_manifest],
                },
                'provider_invocation': None,
                'provider_observation': 'NOT_OBSERVED',
                'correlation_readiness': {
                    'runtime_instance_id': current.runtime_instance_id,
                    'process_id': os.getpid(), 'source_build_hash': BUILD_ID,
                    'required_external_receipt_fields': ['runtime_instance_id', 'process_id', 'build_id',
                        'request_id', 'invocation_id', 'provider_id', 'actual_model', 'timestamp', 'identity_status'],
                    'provider_receipt_exposed': False,
                },
                'runtime_identity': 'NOT_VERIFIED',
            }
        }

    # Capture after registration, before this application starts serving.
    startup_manifest = _loaded_code_manifest(application)
