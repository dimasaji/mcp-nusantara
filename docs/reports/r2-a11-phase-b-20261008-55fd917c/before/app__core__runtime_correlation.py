"""Process-memory diagnostic correlation; no DB, RAG, configuration loader or arming API."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import ipaddress
import os
import secrets
import threading
import time
from urllib.parse import urlsplit

import httpx

from app.core.runtime_identity import BUILD_ID, current_runtime_instance


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class EndpointBinding:
    origin: str
    connection_origin: str

    @classmethod
    def from_configuration(cls, configuration):
        url = urlsplit(configuration.llm.base_url)
        host = url.hostname
        if (url.scheme != 'http' or not host or url.path not in ('', '/')
                or url.username or url.password or url.query or url.fragment):
            raise ValueError('ATTESTATION_ENDPOINT_NOT_BOUND')
        # Explicit loopback resolution policy, recorded separately from configured identity.
        connect_host = '127.0.0.1' if host == 'localhost' else host
        try:
            if '%' in connect_host or not ipaddress.ip_address(connect_host).is_loopback:
                raise ValueError('ATTESTATION_ENDPOINT_NOT_LOOPBACK')
        except ValueError:
            raise ValueError('ATTESTATION_ENDPOINT_NOT_LOOPBACK') from None
        port = url.port or 80
        origin = str(httpx.URL(scheme='http', host=host, port=port))
        connection = str(httpx.URL(scheme='http', host=connect_host, port=port))
        return cls(origin.rstrip('/'), connection.rstrip('/'))


@dataclass(frozen=True)
class CorrelationReceipt:
    request_id: str
    invocation_id: str | None
    runtime_instance_id: str
    pid: int
    source_snapshot: str
    scoped_loaded_code: str
    provider_id: str
    provider_endpoint: EndpointBinding
    actual_model: str | None
    started_at: str
    completed_at: str
    response_observed: bool
    application_response_sent: bool
    dispatch_count: int
    outcome: str
    external_client_observed: bool = False
    full_application_build_verified: bool = False


class OneUseAuthorization:
    """Trusted server-side grant only; no HTTP grant and no auto-grant on boot."""

    def __init__(self):
        instance = current_runtime_instance()
        self._pid = os.getpid()
        self._instance = instance.runtime_instance_id
        self._lock = threading.Lock()
        self._state = 'DISARMED'
        self._token_digest = None
        self._deadline = 0.0
        self._dispatches = 0

    def _bound(self):
        return (self._pid == os.getpid()
                and self._instance == current_runtime_instance().runtime_instance_id)

    def grant(self, *, ttl_s: float = 60.0) -> str:
        """A future trusted operator may call once; never publish/log this capability."""
        if isinstance(ttl_s, bool) or not 0 < ttl_s <= 120:
            raise ValueError('INVALID_GRANT_TTL')
        with self._lock:
            if self._state != 'DISARMED' or not self._bound():
                raise ValueError('GRANT_UNAVAILABLE')
            token = secrets.token_urlsafe(32)
            self._token_digest = hashlib.sha256(token.encode()).digest()
            self._deadline = time.monotonic() + ttl_s
            self._state = 'ARMED'
            return token

    def reserve(self, token: str):
        with self._lock:
            if self._state != 'ARMED' or not self._bound():
                raise ValueError('GENERATION_NOT_AUTHORIZED')
            if time.monotonic() >= self._deadline:
                self._state = 'EXPIRED'
                self._token_digest = None
                raise ValueError('GRANT_EXPIRED')
            if not isinstance(token, str) or not secrets.compare_digest(
                    hashlib.sha256(token.encode()).digest(), self._token_digest):
                raise ValueError('GENERATION_NOT_AUTHORIZED')
            self._state = 'RESERVED'
            self._token_digest = None

    def dispatch(self):
        with self._lock:
            if self._state != 'RESERVED' or self._dispatches or not self._bound():
                raise ValueError('SECOND_DISPATCH_REJECTED')
            if time.monotonic() >= self._deadline:
                self._state = 'TERMINAL'
                self._token_digest = None
                raise ValueError('GRANT_EXPIRED_BEFORE_DISPATCH')
            self._dispatches = 1
            self._state = 'DISPATCHED'

    def finish(self):
        with self._lock:
            if self._state in ('RESERVED', 'DISPATCHED'):
                self._state = 'TERMINAL'

    def abort(self):
        """Terminal revocation, including ARMED; cannot undo a prior dispatch."""
        with self._lock:
            self._state = 'TERMINAL'
            self._token_digest = None

    @property
    def dispatch_count(self):
        with self._lock:
            return self._dispatches

    @property
    def state(self):
        with self._lock:
            return self._state


class OneDispatchTransport(httpx.AsyncBaseTransport):
    def __init__(self, endpoint: EndpointBinding, authorization: OneUseAuthorization, *, isolated_transport=None):
        self.endpoint = endpoint
        self.authorization = authorization
        if isolated_transport is not None and type(isolated_transport) is not httpx.MockTransport:
            raise ValueError('ISOLATED_MOCK_TRANSPORT_REQUIRED')
        self._transport = isolated_transport if isolated_transport is not None else httpx.AsyncHTTPTransport(retries=0, trust_env=False)

    async def handle_async_request(self, request):
        expected = httpx.URL(self.endpoint.origin + '/api/generate')
        if request.method != 'POST' or request.url != expected:
            raise ValueError('UNEXPECTED_PROVIDER_REQUEST')
        self.authorization.dispatch()
        # Preserve configured Host/model; pin only the transport connection address.
        pinned = httpx.Request('POST', self.endpoint.connection_origin + '/api/generate',
                               headers=request.headers, content=await request.aread(),
                               extensions=request.extensions)
        return await self._transport.handle_async_request(pinned)

    async def aclose(self):
        await self._transport.aclose()


class ResponseObservationMiddleware:
    def __init__(self, app, controller):
        self.app = app
        self.controller = controller

    async def __call__(self, scope, receive, send):
        request_id = None
        success = False

        async def observed_send(message):
            nonlocal request_id, success
            if message['type'] == 'http.response.start':
                success = 200 <= message['status'] < 300
                request_id = dict(message.get('headers', [])).get(b'x-request-id', b'').decode()
            await send(message)
            if (success and message['type'] == 'http.response.body'
                    and not message.get('more_body', False)):
                self.controller.mark_response_sent(request_id)

        if scope['type'] == 'http' and scope.get('path') == '/v1/runtime/verification':
            await self.app(scope, receive, observed_send)
        else:
            await self.app(scope, receive, send)


def receipt_dump(receipt):
    return asdict(receipt) if receipt is not None else None
