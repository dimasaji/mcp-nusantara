"""Controlled ATTESTATION-only diagnostic surface using the genuine existing provider."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import os
import threading
from uuid import uuid4
from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import httpx

from app.core.runtime_correlation import (CorrelationReceipt, EndpointBinding,
    OneDispatchTransport, OneUseAuthorization, ResponseObservationMiddleware,
    receipt_dump, utc_now)
from app.core.runtime_correlation import ReceiptObservation, assess_receipt, _aware_time
from app.core.runtime_attestation import _process_identity
from app.core.runtime_identity import (BUILD_ID, ModelExecutionIdentity,
    capture_model_identity, current_runtime_instance)
from app.models.ollama import OllamaProvider
from app.observability.context import current_ids, request_context

VERIFICATION_PATH = '/v1/runtime/verification'


class VerificationController:
    def __init__(self, configuration):
        if (configuration.runtime.profile != 'ATTESTATION'
                or configuration.runtime.workers != 1
                or configuration.runtime.port != 8000
                or configuration.runtime.host not in {'127.0.0.1', '::1', 'localhost'}
                or configuration.llm.provider != 'ollama'):
            raise ValueError('UNSAFE_ATTESTATION_PROFILE')
        self.configuration = configuration
        self.endpoint = EndpointBinding.from_configuration(configuration)
        self.authorization = OneUseAuthorization()
        self._receipt = None
        self._receipt_observation = None
        self._lock = threading.Lock()
        self._code_observer = None
        self._code_hash = None
        self._authority_functions = None

    def bind_loaded_code(self, observer):
        self._code_observer = observer
        self._code_hash = observer()

    def code_functions(self):
        return (VerificationController.__init__, VerificationController.invoke,
                VerificationController.bind_loaded_code, VerificationController.code_functions,
                VerificationController._store, VerificationController.mark_response_sent,
                VerificationController.receipt_assessment, assess_receipt, _aware_time,
                ReceiptObservation.__init__,
                OneUseAuthorization.__init__, OneUseAuthorization._bound, OneUseAuthorization.grant,
                OneUseAuthorization.reserve, OneUseAuthorization.dispatch, OneUseAuthorization.finish,
                OneUseAuthorization.abort,
                OneDispatchTransport.__init__, OneDispatchTransport.handle_async_request,
                OneDispatchTransport.aclose, ResponseObservationMiddleware.__init__,
                ResponseObservationMiddleware.__call__, receipt_dump, utc_now,
                EndpointBinding.from_configuration.__func__, capture_model_identity,
                ModelExecutionIdentity.with_response, OllamaProvider.__init__,
                OllamaProvider.generate, OllamaProvider._capture_identity, OllamaProvider._get_client,
                OllamaProvider._options, OllamaProvider._emit_identity, OllamaProvider.close) + (
                    self._authority_functions() if self._authority_functions is not None else ())

    @property
    def receipt(self):
        with self._lock:
            return self._receipt

    def _store(self, receipt, *, process_start=None, evidence_class='UNVERIFIED'):
        observed = datetime.now(timezone.utc)
        observation = ReceiptObservation(receipt, process_start, observed.isoformat(),
            (observed + timedelta(seconds=60)).isoformat(), evidence_class)
        with self._lock:
            if self._receipt is not None:
                raise ValueError('CONFLICTING_RECEIPT_REPLACEMENT')
            self._receipt = receipt
            self._receipt_observation = observation

    def receipt_assessment(self, *, now=None):
        """Detached internal assessment; no public schema/authority change."""
        with self._lock:
            receipt, observation = self._receipt, self._receipt_observation
        try:
            process = _process_identity()
            instance = current_runtime_instance()
            code = self._code_observer() if self._code_observer else None
            return assess_receipt(receipt, observation, pid=os.getpid(),
                process_start=process['process_start_time'], runtime_instance=instance.runtime_instance_id,
                source_snapshot=BUILD_ID, scoped_loaded_code=code,
                provider_id=self.configuration.llm.provider, endpoint=self.endpoint, now=now)
        except Exception:
            return {'status': 'NOT_VERIFIED', 'correlation_valid': False,
                    'reason': 'CURRENT_CONTEXT_UNAVAILABLE',
                    'application_response_sent': False, 'external_client_observed': False}

    def mark_response_sent(self, request_id):
        with self._lock:
            if (self._receipt is not None and self._receipt.request_id == request_id
                    and self._receipt.outcome == 'PROVIDER_RESPONSE_CORRELATED'):
                self._receipt = replace(self._receipt, application_response_sent=True)

    async def invoke(self, token, *, isolated_transport=None):
        if not self._code_observer or self._code_observer() != self._code_hash:
            raise ValueError('SCOPED_CODE_NOT_BOUND')
        self.authorization.reserve(token)  # atomic, before all awaits and client construction
        instance = current_runtime_instance()
        request_id = current_ids()['request_id']
        if request_id == '-':
            request_id = 'r2_' + uuid4().hex
        started = utc_now()
        process_start = _process_identity()['process_start_time']
        provider = None
        evidence_class = 'UNVERIFIED'
        try:
            transport = OneDispatchTransport(self.endpoint, self.authorization, isolated_transport=isolated_transport)
            evidence_class = ('PROVIDER_RESPONSE' if type(transport._transport) is httpx.AsyncHTTPTransport
                              else 'TEST_ISOLATED')
            client = httpx.AsyncClient(base_url=self.endpoint.origin, transport=transport,
                timeout=self.configuration.llm.connection_timeout_s,
                follow_redirects=False, trust_env=False)
            provider = OllamaProvider(nusantara_config=self.configuration, http_client=client)
            with request_context(request_id=request_id):
                # Fixed public diagnostic input; request cannot select prompt/model/options.
                result = await provider.generate({'prompt': 'Reply with the word READY.'})
            identity = result.get('execution_identity', {})
            required = {'request_id': request_id, 'runtime_instance_id': instance.runtime_instance_id,
                'process_id': os.getpid(), 'build_id': BUILD_ID, 'provider_id': self.configuration.llm.provider,
                'payload_model': self.configuration.llm.model, 'actual_model': self.configuration.llm.model,
                'identity_status': 'RUNTIME_CONFIRMED', 'confirmation_source': 'PROVIDER_RESPONSE'}
            if (not isinstance(identity, dict) or any(identity.get(k) != v for k, v in required.items())
                    or not isinstance(identity.get('invocation_id'), str) or not identity['invocation_id']
                    or identity.get('request_id_source') != 'REQUEST_CONTEXT'
                    or not isinstance(result.get('content'), str)
                    or self._code_observer() != self._code_hash):
                raise ValueError('PROVIDER_CORRELATION_NOT_VERIFIED')
            receipt = CorrelationReceipt(request_id, identity['invocation_id'], instance.runtime_instance_id,
                os.getpid(), BUILD_ID, self._code_hash, self.configuration.llm.provider, self.endpoint,
                identity['actual_model'], started, utc_now(), True, False,
                self.authorization.dispatch_count, 'PROVIDER_RESPONSE_CORRELATED')
            self._store(receipt, process_start=process_start, evidence_class=evidence_class)
            return receipt
        except BaseException:
            # No prompt/content/raw exception, and no invented successful invocation/model receipt.
            if self.receipt is None:
                self._store(CorrelationReceipt(request_id, None, instance.runtime_instance_id, os.getpid(),
                    BUILD_ID, self._code_hash, self.configuration.llm.provider, self.endpoint, None,
                    started, utc_now(), False, False, self.authorization.dispatch_count, 'FAILED_OR_CANCELLED'),
                    process_start=process_start, evidence_class=evidence_class)
            raise
        finally:
            self.authorization.finish()
            if provider is not None:
                await provider.close()


def install_runtime_verification(application, configuration):
    controller = VerificationController(configuration)
    application.state.runtime_verification = controller
    application.add_middleware(ResponseObservationMiddleware, controller=controller)

    @application.post(VERIFICATION_PATH, tags=['runtime-verification'])
    async def verification(request: Request):
        if (not request.client or request.client.host not in {'127.0.0.1', '::1'}
                or request.url.hostname not in {'127.0.0.1', '::1', 'localhost'}
                or request.url.port != 8000):
            raise HTTPException(403, 'LOCAL_RUNTIME_ONLY')
        origin = request.headers.get('origin')
        if origin:
            try:
                parsed = urlsplit(origin)
                valid = parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', '::1', 'localhost'} and parsed.port == 8000
            except ValueError:
                valid = False
            if not valid:
                raise HTTPException(403, 'LOCAL_RUNTIME_ONLY')
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 128:
                raise HTTPException(400, 'BOUNDED_DIAGNOSTIC_INPUT_REQUIRED')
        try:
            data = json.loads(body)
        except (ValueError, UnicodeError):
            raise HTTPException(400, 'BOUNDED_DIAGNOSTIC_INPUT_REQUIRED') from None
        if data != {'probe': 'runtime-correlation'}:
            raise HTTPException(400, 'DIAGNOSTIC_OVERRIDE_REJECTED')
        header = request.headers.get('authorization', '')
        if not header.startswith('Bearer ') or len(header) > 128:
            raise HTTPException(403, 'GENERATION_NOT_AUTHORIZED')
        try:
            receipt = await controller.invoke(header[7:])
        except ValueError:
            raise HTTPException(403, 'VERIFICATION_REJECTED') from None
        except Exception:
            raise HTTPException(502, 'PROVIDER_VERIFICATION_FAILED') from None
        return JSONResponse({'receipt': receipt_dump(receipt), 'runtime_identity': 'NOT_VERIFIED'},
                            headers={'X-Request-ID': receipt.request_id})

    return controller
