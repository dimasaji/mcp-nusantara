"""ATTESTATION memory foundation reusing the existing audit/approval engines.

No live arming: ARM/EXECUTE require an explicitly injected MockTransport.
No HTTP mutation, file sink, auto-policy, automatic grant or actor JSON authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import asyncio
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import threading
import time
from uuid import uuid4

import httpx

from app.approval.audit_trail import AuditTrail
from app.approval.queue import ApprovalQueue, payload_hash
from app.core.runtime_identity import BUILD_ID, current_runtime_instance
from app.observability.logging import redact
from app.security.local_operator import (VerifiedPeer, OperatorPolicy, LocalOperatorChannel,
    Windows, Actor, ActorError)

SCOPE = 'R2-A8:ATTESTATION:ONE_GENERATION'
REASONS = frozenset({'REVIEWED', 'INSUFFICIENT_EVIDENCE', 'HOLD_FOR_REVIEW', 'OPERATOR_ABORT'})


class AuthorizationError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def safe_string(value):
    """Reversible encoding: no opaque 16-digit run can be altered by redaction."""
    raw = value.encode('utf-8').hex()
    return 'hex:' + ':'.join(raw[i:i + 8] for i in range(0, len(raw), 8))


def audit_projection(value, depth=0):
    if depth > 4:
        raise AuthorizationError('AUDIT_DEPTH_BOUNDARY')
    if isinstance(value, str):
        return safe_string(value)
    if isinstance(value, dict):
        return {key: audit_projection(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [audit_projection(item, depth + 1) for item in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise AuthorizationError('AUDIT_TYPE_BOUNDARY')


@dataclass(frozen=True)
class Binding:
    scope: str
    evidence_version: str
    material: str
    pid: int
    process_start: int
    runtime_instance: str
    source_snapshot: str
    scoped_loaded_code: str
    expires_at: str


@dataclass(frozen=True)
class Review:
    review_id: str
    approval_id: str
    binding: Binding
    deadline: float
    state: str = 'PENDING'
    actor_reference: str | None = None
    reason: str | None = None


class RuntimeAuthorization:
    def __init__(self, controller, *, policy=None, isolated_transport=None):
        if controller.configuration.runtime.profile != 'ATTESTATION':
            raise AuthorizationError('ATTESTATION_ONLY')
        if policy is not None and not isinstance(policy, OperatorPolicy):
            raise AuthorizationError('EXPLICIT_OPERATOR_POLICY_REQUIRED')
        if isolated_transport is not None and type(isolated_transport) is not httpx.MockTransport:
            raise AuthorizationError('ISOLATED_MOCK_TRANSPORT_REQUIRED')
        self._controller = controller
        self._policy = policy
        self._isolated_transport = isolated_transport
        self._lock = threading.RLock()
        self._reviews = {}
        self._browser_reviews = {}  # One bounded intention per exact evidence context.
        self._proofs = set()
        self._permit = None
        self._armed_review = None
        self._poisoned = False
        self._audit = AuditTrail()  # Existing class, single owner, no path/no persistence.
        self._native_record = self._audit.record
        # Projection adapter ONLY; native chain, timestamps, redaction and storage unchanged.
        self._audit.record = self._record
        self._queue = ApprovalQueue(self._audit, ttl_minutes=2)

    def _record(self, event, **fields):
        if len(self._audit.entries()) >= 1024:
            raise AuthorizationError('AUDIT_CAPACITY')
        expected = audit_projection(fields)
        if redact(expected) != expected:
            raise AuthorizationError('LOSSY_AUDIT_PROJECTION')
        entry = self._native_record(event, **expected)
        if entry['data'] != expected or not self._audit.verify():
            raise AuthorizationError('AUDIT_INTEGRITY_FAILURE')
        return entry

    def _material(self):
        controller = self._controller
        if not controller._code_observer or controller._code_observer() != controller._code_hash:
            raise AuthorizationError('SCOPED_CODE_NOT_BOUND')
        instance = current_runtime_instance()
        return {'scope': SCOPE, 'target': '127.0.0.1:8000', 'pid': os.getpid(),
            'process_start': Windows().process_start(os.getpid()),
            'runtime_instance': instance.runtime_instance_id, 'source_snapshot': BUILD_ID,
            'scoped_loaded_code': controller._code_hash,
            'configuration_digest': hashlib.sha256(controller.configuration.canonical_json().encode()).hexdigest(),
            'endpoint': asdict(controller.endpoint), 'profile': 'ATTESTATION',
            'active_process_build': 'NOT_DIRECTLY_VERIFIED', 'runtime_identity': 'NOT_VERIFIED'}

    def evidence(self):
        """Fresh detached, bounded projection; no queue/audit/token references."""
        with self._lock:
            material = self._material()
            encoded = canonical(material)
            return {'evidence_id': 'r2-a9-auth-process', 'evidence_type': 'SCOPED_IN_PROCESS',
                'projection_contract': 'ATTESTATION_FOUNDATION_V1',
                'source': 'ATTESTATION authorization foundation', 'scope': SCOPE,
                'created_at': datetime.now(timezone.utc).isoformat(), 'status': 'NOT_VERIFIED',
                'evidence_version': hashlib.sha256(encoded.encode()).hexdigest(),
                'binding': json.loads(encoded), 'live_actions': 'LOCKED',
                'operator_policy': 'NOT_PROVISIONED' if self._policy is None else 'EXPLICIT_LOCAL_POLICY',
                'reviews': [{'review_id': r.review_id, 'state': r.state, 'expires_at': r.binding.expires_at}
                            for r in self._reviews.values()],
                'provider_receipt': asdict(self._controller.receipt) if self._controller.receipt else None}

    def browser_intention(self, *, scope, evidence_version):
        """Untrusted browser context: validate atomically, then PENDING only.

        Duplicate submission cannot add queue/audit entries or extend expiry.
        Expired/terminal context cannot be renewed from the browser.
        """
        with self._lock:
            material = canonical(self._material())
            version = hashlib.sha256(material.encode()).hexdigest()
            if self._poisoned or scope != SCOPE or evidence_version != version:
                raise AuthorizationError('BROWSER_CONTEXT_REJECTED')
            existing = self._browser_reviews.get(version)
            if existing is not None:
                review = self._reviews[existing]
                if (review.state != 'PENDING' or time.monotonic() >= review.deadline
                        or datetime.now(timezone.utc) >= datetime.fromisoformat(review.binding.expires_at)):
                    raise AuthorizationError('BROWSER_CONTEXT_CLOSED')
                return {'review_id': review.review_id, 'scope': review.binding.scope,
                    'evidence_version': version, 'state': 'PENDING', 'expires_at': review.binding.expires_at}
            if len(self._browser_reviews) >= 32 or len(self._reviews) >= 32:
                raise AuthorizationError('BROWSER_CAPACITY')
            result = self.intention(scope=scope, expected_version=version)  # Still under lock.
            self._browser_reviews[version] = result['review_id']
            return result

    def intention(self, *, scope=SCOPE, ttl=120, expected_version=None):
        """Server-generated pending intention; never approval or arming."""
        with self._lock:
            if (self._poisoned or scope != SCOPE or isinstance(ttl, bool)
                    or not 0 < ttl <= 120 or len(self._reviews) >= 32):
                raise AuthorizationError('INTENTION_REJECTED')
            material = canonical(self._material())
            if expected_version is not None and hashlib.sha256(material.encode()).hexdigest() != expected_version:
                raise AuthorizationError('STALE_BROWSER_CONTEXT')
            data = json.loads(material)
            binding = Binding(scope, hashlib.sha256(material.encode()).hexdigest(), material,
                data['pid'], data['process_start'], data['runtime_instance'], data['source_snapshot'],
                data['scoped_loaded_code'], (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat())
            try:
                request = self._queue.submit('R2-A9-AUTH', asdict(binding), risk='LEVEL_C',
                    requested_by='SERVER:ATTESTATION', summary={'scope': scope})
                review = Review(uuid4().hex, request.approval_id, binding, time.monotonic() + ttl)
                self._reviews[review.review_id] = review
                self._record('runtime.intention', review=review.review_id, binding=canonical(asdict(binding)))
                return {'review_id': review.review_id, 'scope': scope,
                        'evidence_version': binding.evidence_version, 'state': 'PENDING',
                        'expires_at': binding.expires_at}
            except BaseException:
                self._poison()
                raise AuthorizationError('INTENTION_FAILED_CLOSED') from None

    def _poison(self):
        self._poisoned = True
        self._permit = None
        self._controller.authorization.abort()
        for key, review in list(self._reviews.items()):
            if review.state not in {'COMPLETED', 'REJECTED', 'HOLD', 'ABORTED'}:
                self._reviews[key] = replace(review, state='ABORTED')

    def _peer(self, proof):
        if type(proof) is not VerifiedPeer or self._policy is None or self._poisoned:
            raise AuthorizationError('NATIVE_OPERATOR_REQUIRED')
        actor = proof.validate()
        if not self._policy.permits(actor) or proof._identity in self._proofs or len(self._proofs) >= 1024:
            raise AuthorizationError('ACTOR_OR_REPLAY_REJECTED')
        self._proofs.add(proof._identity)
        return actor

    @staticmethod
    def _actor_reference(actor):
        return hashlib.sha256(canonical({'sid': actor.sid, 'logon': actor.logon_id,
                                        'session': actor.session}).encode()).hexdigest()

    def _validate(self, actor, body):
        if (not isinstance(body, dict) or set(body) != {'operation', 'review_id', 'scope', 'evidence_version', 'reason'}
                or body['operation'] not in {'APPROVE', 'REJECT', 'HOLD', 'ABORT', 'ARM', 'EXECUTE'}
                or body['scope'] != SCOPE or body['reason'] not in REASONS):
            raise AuthorizationError('BOUNDED_COMMAND_REQUIRED')
        review = self._reviews.get(body['review_id'])
        if not review or body['evidence_version'] != review.binding.evidence_version:
            raise AuthorizationError('EVIDENCE_REFERENCE_REJECTED')
        if (time.monotonic() >= review.deadline
                or datetime.now(timezone.utc) >= datetime.fromisoformat(review.binding.expires_at)
                or canonical(self._material()) != review.binding.material):
            raise AuthorizationError('STALE_OR_EXPIRED_BINDING')
        reference = self._actor_reference(actor)
        if review.actor_reference not in (None, reference):
            raise AuthorizationError('WRONG_DECISION_ACTOR')
        queue = self._queue.get(review.approval_id)
        expected_status = {'PENDING': 'pending', 'APPROVED': 'approved', 'ARMED': 'consumed'}.get(review.state)
        if (queue is None or expected_status is None or queue.status != expected_status
                or queue.payload_hash != payload_hash(asdict(review.binding))
                or queue.requested_by != 'SERVER:ATTESTATION'
                or (review.actor_reference is not None and queue.reviewer != safe_string(review.actor_reference))
                or not self._audit.verify()):
            raise AuthorizationError('QUEUE_OR_AUDIT_STATE_REJECTED')
        return review, reference

    async def handle_verified(self, proof, body):
        """Private trusted IPC caller only. No HTTP/frontend path exposes this."""
        with self._lock:
            actor = self._peer(proof)  # Unauthenticated caller cannot poison/revoke another review.
            review = None
            try:
                review, reference = self._validate(actor, body)
                operation = body['operation']
                if operation in {'APPROVE', 'REJECT', 'HOLD', 'ABORT'}:
                    if operation in {'ABORT', 'HOLD'} and review.state in {'APPROVED', 'ARMED'}:
                        self._controller.authorization.abort()
                        self._permit = None
                    elif review.state != 'PENDING':
                        raise AuthorizationError('DECISION_REPLAY')
                    else:
                        decision = {'APPROVE': 'approved', 'REJECT': 'rejected',
                                    'HOLD': 'request_changes', 'ABORT': 'rejected'}[operation]
                        self._queue.decide(review.approval_id, reviewer=safe_string(reference),
                                           decision=decision, reason=body['reason'])
                    state = {'APPROVE': 'APPROVED', 'REJECT': 'REJECTED', 'HOLD': 'HOLD', 'ABORT': 'ABORTED'}[operation]
                    self._record('runtime.decision', review=review.review_id, action=operation,
                        reason=body['reason'], actor_ref=reference, peer_pid=actor.pid,
                        binding=canonical(asdict(review.binding)), result=state)
                    self._reviews[review.review_id] = replace(review, state=state, actor_reference=reference, reason=body['reason'])
                    return {'review_id': review.review_id, 'state': state}
                # Live grants cannot be issued even with a native proof; only isolated mock.
                if self._isolated_transport is None:
                    raise AuthorizationError('LIVE_ACTIONS_NOT_AUTHORIZED')
                if operation == 'ARM':
                    if review.state != 'APPROVED' or self._armed_review is not None:
                        raise AuthorizationError('ARM_REPLAY')
                    if not self._queue.consume(review.approval_id, asdict(review.binding)):
                        raise AuthorizationError('QUEUE_CONSUME_REJECTED')
                    self._record('runtime.arm_prepared', review=review.review_id, actor_ref=reference,
                                 binding=canonical(asdict(review.binding)))
                    remaining = min(review.deadline - time.monotonic(),
                        (datetime.fromisoformat(review.binding.expires_at) - datetime.now(timezone.utc)).total_seconds())
                    self._permit = self._controller.authorization.grant(ttl_s=min(120, remaining))
                    self._armed_review = review.review_id
                    self._record('runtime.armed', review=review.review_id, actor_ref=reference, result='ISOLATED_ONLY')
                    self._reviews[review.review_id] = replace(review, state='ARMED')
                    return {'review_id': review.review_id, 'state': 'ARMED', 'scope': 'ISOLATED_MOCK_ONLY'}
                if review.state != 'ARMED' or self._armed_review != review.review_id or not self._permit:
                    raise AuthorizationError('EXECUTION_REPLAY')
                self._record('runtime.execution_claimed', review=review.review_id, actor_ref=reference,
                             binding=canonical(asdict(review.binding)))
                permit, self._permit = self._permit, None
                self._reviews[review.review_id] = replace(review, state='EXECUTING')
            except BaseException:
                self._poison()
                self._failure_event(actor, review, 'TRANSITION_FAILED')
                raise AuthorizationError('TRANSITION_FAILED_CLOSED') from None
        try:
            receipt = await self._controller.invoke(permit, isolated_transport=self._isolated_transport)
            with self._lock:
                if self._poisoned:
                    raise AuthorizationError('REVOKED_DURING_EXECUTION')
                self._record('runtime.completed', review=review.review_id, request=receipt.request_id,
                    invocation=receipt.invocation_id, model=receipt.actual_model, result=receipt.outcome)
                self._reviews[review.review_id] = replace(review, state='COMPLETED')
                return {'review_id': review.review_id, 'state': 'COMPLETED', 'receipt': asdict(receipt),
                        'runtime_identity': 'NOT_VERIFIED'}
        except BaseException:
            with self._lock:
                self._poison()
                self._failure_event(actor, review, 'EXECUTION_FAILED_OR_UNCERTAIN')
            raise AuthorizationError('EXECUTION_FAILED_CLOSED') from None

    def _failure_event(self, actor, review, result):
        """Attempt existing ledger only; audit failure can never release permission."""
        try:
            self._record('runtime.failed_closed', actor_ref=self._actor_reference(actor),
                review=review.review_id if review else None, result=result,
                dispatch_count=self._controller.authorization.dispatch_count)
        except BaseException:
            pass  # Owner is already poisoned/revoked; no alternative sink or retry.

    def serve_operator_once(self, channel):
        """Explicit native-channel integration for a trusted IPC worker thread only.

        No listener creation, loop, activation policy or app startup call is included.
        """
        if (self._policy is None or type(channel) is not LocalOperatorChannel
                or channel.policy != self._policy):
            raise AuthorizationError('EXPLICIT_MATCHING_OPERATOR_CHANNEL_REQUIRED')
        def handle(proof, body):
            return asyncio.run(self.handle_verified(proof, body))
        return channel.serve_authenticated_once(handle)

    def code_functions(self):
        from app.api.control_plane import snapshot, intention
        return (canonical, safe_string, audit_projection, RuntimeAuthorization.__init__,
            RuntimeAuthorization._record, RuntimeAuthorization._material, RuntimeAuthorization.evidence,
            RuntimeAuthorization.browser_intention,
            RuntimeAuthorization.intention, RuntimeAuthorization._poison, RuntimeAuthorization._peer,
            RuntimeAuthorization._actor_reference, RuntimeAuthorization._validate,
            RuntimeAuthorization.handle_verified, RuntimeAuthorization.code_functions,
            RuntimeAuthorization._failure_event, RuntimeAuthorization.serve_operator_once, snapshot, intention,
            install_authorization_foundation, AuditTrail.__init__, AuditTrail._digest,
            AuditTrail.record, AuditTrail.entries, AuditTrail.verify, ApprovalQueue.__init__,
            ApprovalQueue._persist, ApprovalQueue.submit, ApprovalQueue.get, ApprovalQueue.decide,
            ApprovalQueue.consume, payload_hash, redact,
            VerifiedPeer.__init__, VerifiedPeer.__setattr__, VerifiedPeer.validate, LocalOperatorChannel.__init__,
            LocalOperatorChannel.__enter__, LocalOperatorChannel.__exit__, LocalOperatorChannel.peer.__wrapped__,
            LocalOperatorChannel.serve_once, LocalOperatorChannel.serve_authenticated_once,
            LocalOperatorChannel._challenge, LocalOperatorChannel._consume, OperatorPolicy.permits,
            Windows.__init__, Windows.check, Windows.actor, Windows.information, Windows.sid_text,
            Windows.process_actor, Windows.process_identity, Windows.process_start,
            Windows.current_actor, Windows.read, Windows.write)


def install_authorization_foundation(application, controller, **kwargs):
    if application.state.runtime_profile != 'ATTESTATION':
        raise AuthorizationError('ATTESTATION_ONLY')
    if hasattr(application.state, 'runtime_authorization'):
        raise AuthorizationError('FOUNDATION_ALREADY_INSTALLED')
    owner = RuntimeAuthorization(controller, **kwargs)
    application.state.runtime_authorization = owner
    controller._authority_functions = owner.code_functions
    return owner
