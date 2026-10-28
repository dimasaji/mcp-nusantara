"""Process-memory diagnostic correlation; no DB, RAG, configuration loader or arming API."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import ipaddress
import math
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


@dataclass(frozen=True)
class ReceiptObservation:
    """Private server context, never an authorization or client receipt assertion."""
    receipt: CorrelationReceipt
    process_start: str | None
    observed_at: str
    expires_at: str
    evidence_class: str


def _aware_time(value):
    if not isinstance(value, str):
        raise ValueError('MISSING_TIMESTAMP')
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError('UNBOUND_TIMESTAMP')
    return parsed.astimezone(timezone.utc)


def assess_receipt(receipt, observation, *, pid, process_start, runtime_instance,
                   source_snapshot, scoped_loaded_code, provider_id, endpoint,
                   now=None, max_age_s=60):
    """Assess trusted server context only; never import client claims or promote gates.

    A copied fixture labelled PROVIDER_RESPONSE is not authenticated by this pure
    function. Callers must supply observation from their private invocation owner.
    """
    result = {'status': 'NOT_VERIFIED', 'correlation_valid': False,
              'reason': 'MISSING_OR_INVALID_RECEIPT', 'application_response_sent': False,
              'external_client_observed': False}
    if type(receipt) is not CorrelationReceipt or type(observation) is not ReceiptObservation:
        return result
    try:
        if (isinstance(max_age_s, bool) or not isinstance(max_age_s, (int, float))
                or not math.isfinite(max_age_s) or not 0 < max_age_s <= 120):
            raise ValueError('INVALID_FRESHNESS_BOUND')
        if observation.evidence_class != 'PROVIDER_RESPONSE':
            raise ValueError('NO_GENUINE_PROVIDER_OBSERVATION')
        # Only the later successful ASGI send flag may differ from the stored copy.
        if replace(receipt, application_response_sent=observation.receipt.application_response_sent) != observation.receipt:
            raise ValueError('CONFLICTING_RECEIPT')
        if (type(pid) is not int or pid <= 0 or type(receipt.pid) is not int
                or receipt.pid != pid or not runtime_instance or receipt.runtime_instance_id != runtime_instance
                or not source_snapshot or receipt.source_snapshot != source_snapshot
                or not scoped_loaded_code or receipt.scoped_loaded_code != scoped_loaded_code
                or not provider_id or receipt.provider_id != provider_id
                or type(endpoint) is not EndpointBinding or receipt.provider_endpoint != endpoint
                or _aware_time(observation.process_start) != _aware_time(process_start)):
            raise ValueError('PROCESS_OR_CODE_BINDING_MISMATCH')
        if (not isinstance(receipt.request_id, str) or not receipt.request_id
                or not isinstance(receipt.invocation_id, str) or not receipt.invocation_id
                or not isinstance(receipt.actual_model, str) or not receipt.actual_model.strip()
                or any(ord(c) < 32 for c in receipt.actual_model) or len(receipt.actual_model) > 256
                or receipt.response_observed is not True or type(receipt.dispatch_count) is not int
                or receipt.dispatch_count != 1 or receipt.outcome != 'PROVIDER_RESPONSE_CORRELATED'
                or type(receipt.application_response_sent) is not bool
                or receipt.external_client_observed is not False
                or receipt.full_application_build_verified is not False):
            raise ValueError('INCOMPLETE_PROVIDER_EVIDENCE')
        current = datetime.now(timezone.utc) if now is None else now
        if not isinstance(current, datetime) or current.tzinfo is None:
            raise ValueError('UNBOUND_OBSERVATION_TIME')
        start, complete = _aware_time(receipt.started_at), _aware_time(receipt.completed_at)
        observed, expires = _aware_time(observation.observed_at), _aware_time(observation.expires_at)
        if (not _aware_time(process_start) <= start <= complete <= observed <= current < expires
                or not 0 < (expires-observed).total_seconds() <= max_age_s
                or (current-start).total_seconds() >= max_age_s):
            raise ValueError('STALE_OR_INSUFFICIENT_FRESHNESS')
    except (ValueError, TypeError, AttributeError, OverflowError) as error:
        safe_reasons = {'INVALID_FRESHNESS_BOUND', 'NO_GENUINE_PROVIDER_OBSERVATION',
            'CONFLICTING_RECEIPT', 'PROCESS_OR_CODE_BINDING_MISMATCH',
            'INCOMPLETE_PROVIDER_EVIDENCE', 'UNBOUND_OBSERVATION_TIME',
            'STALE_OR_INSUFFICIENT_FRESHNESS', 'MISSING_TIMESTAMP', 'UNBOUND_TIMESTAMP'}
        result['reason'] = str(error) if str(error) in safe_reasons else 'MALFORMED_RECEIPT_CONTEXT'
        return result
    return {**result, 'correlation_valid': True, 'reason': 'SCOPED_SERVER_RECEIPT_BOUND',
            'application_response_sent': receipt.application_response_sent}


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
