"""Local Control Plane reads and ATTESTATION-only untrusted PENDING intentions."""
from urllib.parse import urlsplit
import json
import os
from enum import Enum
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from app.core.control_plane_projection import project
from app.core.evidence_registry import (EvidenceRegistryError, append_decision_audit,
    collect_review_package, read_decision_audit)

router = APIRouter(prefix='/v1/control-plane', tags=['engineering-control-plane'])


def _model_control_owner(request: Request):
    """Local NORMAL runtime only; evidence and ATTESTATION profiles stay inert."""
    loopback = {'127.0.0.1', '::1', 'localhost'}
    origin = request.headers.get('origin')
    if (not request.client or request.client.host not in loopback
            or request.url.hostname not in loopback
            or (origin and urlsplit(origin).hostname not in loopback)):
        raise HTTPException(403, 'LOCAL_MODEL_CONTROL_REQUIRED')
    owner = getattr(request.app.state, 'configuration_owner', None)
    if getattr(request.app.state, 'runtime_profile', None) != 'NORMAL' or owner is None:
        raise HTTPException(503, 'NORMAL_CONFIGURATION_OWNER_REQUIRED')
    return owner


@router.get('/model-status')
def model_status(request: Request):
    from app.core.runtime_identity import BUILD_ID
    return {**_model_control_owner(request).model_control_status(), 'source_build_id': BUILD_ID,
            'memory': 'LEGACY_BEHAVIOR_PRESERVED_TEMPORARILY', 'memory_governance': 'REVIEW_REQUIRED',
            'knowledge': 'NOT_VERIFIED', 'official_oracle': 'REVIEW_REQUIRED',
            'approval': 'REVIEW_REQUIRED', 'execution_mode': 'V1_DEFAULT'}


async def _available_model_names(configuration):
    import asyncio
    import re
    from app.models.ollama import OllamaProvider
    provider = OllamaProvider(nusantara_config=configuration)
    try:
        inventory = await asyncio.wait_for(provider.list_models(), timeout=min(10.0, configuration.llm.connection_timeout_s))
        if not isinstance(inventory, list):
            raise ValueError('invalid inventory')
        return sorted({item['name'] for item in inventory if isinstance(item, dict)
                       and isinstance(item.get('name'), str)
                       and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}', item['name'])})
    except Exception:
        raise HTTPException(503, 'MODEL_INVENTORY_UNAVAILABLE') from None
    finally:
        await provider.close()


@router.get('/models')
async def available_models(request: Request):
    from app.security.auth import require_admin
    require_admin(request.headers.get('x-admin-token'))
    owner = _model_control_owner(request)
    configuration, revision = owner.configuration_snapshot()
    names = await _available_model_names(configuration)
    return {'models': names, 'provider': configuration.llm.provider,
            'observed_revision': revision, 'availability': 'INVENTORY_OBSERVED',
            'consistency_scope': 'CURRENT_PROCESS_ONLY'}


from pydantic import BaseModel, ConfigDict, Field


class OperatorModelSelection(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    model: str = Field(min_length=1, max_length=256, pattern=r'^[A-Za-z0-9][A-Za-z0-9._:/-]*$')
    expected_revision: int = Field(ge=0)


@router.post('/model-selection')
async def select_model(body: OperatorModelSelection, request: Request):
    from app.core.nusantara_config import ConfigurationError
    from app.security.auth import require_admin
    require_admin(request.headers.get('x-admin-token'))
    owner = _model_control_owner(request)
    configuration, revision = owner.configuration_snapshot()
    if configuration.runtime.workers != 1 or configuration.runtime.profile != 'NORMAL':
        raise HTTPException(409, 'MODEL_CONTROL_SINGLE_NORMAL_WORKER_REQUIRED')
    if revision != body.expected_revision:
        raise HTTPException(409, 'MODEL_SELECTION_CONFLICT')
    names = await _available_model_names(configuration)
    if body.model not in names:
        raise HTTPException(422, 'MODEL_NOT_AVAILABLE')
    try:
        updated, _ = owner.select_operator_model(body.model, expected_revision=revision,
                                                validated_configuration=configuration)
    except ConfigurationError:
        raise HTTPException(409, 'MODEL_SELECTION_CONFLICT') from None
    request.app.state.effective_configuration = updated
    return {**owner.model_control_status(), 'change_status': 'APPLIED',
            'availability': 'INVENTORY_VALIDATED_AT_SELECTION'}


@router.get('/snapshot')
def snapshot(request: Request):
    loopback = {'127.0.0.1','::1','localhost'}
    if not request.client or request.client.host not in loopback or request.url.hostname not in loopback:
        raise HTTPException(403, 'Control Plane is restricted to local engineering access')
    origin = request.headers.get('origin')
    if origin and urlsplit(origin).hostname not in loopback:
        raise HTTPException(403, 'Non-local origin rejected')
    if getattr(request.app.state, 'runtime_profile', None) == 'ATTESTATION':
        owner = getattr(request.app.state, 'runtime_authorization', None)
        if owner is None:
            raise HTTPException(503, 'ATTESTATION_AUTHORIZATION_UNAVAILABLE')
        return owner.evidence()  # Never execute legacy DB/WAL/SHM digest projection.
    return project()


class HumanDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    HOLD = "HOLD"


class EvidenceDecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    package_id: str = Field(pattern=r"^evp_sha256_[a-f0-9]{64}$")
    # FastAPI validates decoded JSON through Pydantic's Python path. Keep the
    # request strict, but allow the JSON string enum value used by the UI.
    decision: HumanDecision = Field(strict=False)
    notes: str = Field(default="", max_length=2000)


def _human_acceptance_boundary(request: Request):
    origin = request.headers.get("origin")
    if (
        not request.client
        or request.client.host not in {"127.0.0.1", "::1"}
        or request.url.hostname not in {"127.0.0.1", "::1", "localhost"}
        or (origin and urlsplit(origin).hostname not in {"127.0.0.1", "::1", "localhost"})
        or (request.method == "POST" and request.headers.get("content-type", "").split(";", 1)[0] != "application/json")
    ):
        raise HTTPException(403, "BROWSER_BOUNDARY_REJECTED")


def _admin_reviewer(request: Request) -> str:
    from app.security.auth import require_admin
    require_admin(request.headers.get("x-admin-token"))
    # The existing shared credential authenticates the admin principal, not a personal name.
    return "admin-token-holder"


def _decision_audit_file() -> Path:
    return Path(os.getenv("NUSANTARA_DATA_DIR", "data")) / "control_plane" / "evidence_decisions.jsonl"


@router.get("/evidence-package")
def evidence_package(request: Request):
    _human_acceptance_boundary(request)
    try:
        return collect_review_package()
    except EvidenceRegistryError as exc:
        raise HTTPException(503, str(exc)) from None


@router.post("/decisions")
def record_evidence_decision(body: EvidenceDecisionInput, request: Request):
    _human_acceptance_boundary(request)
    reviewer = _admin_reviewer(request)
    try:
        package = collect_review_package()
        if body.package_id != package["package_id"]:
            raise HTTPException(409, "EVIDENCE_PACKAGE_CHANGED; refresh and review the new package")
        if body.decision is HumanDecision.PASS and not package["pass_allowed"]:
            raise HTTPException(409, {"code": "PASS_BLOCKED", "blockers": package["blockers"]})
        test_refs = sorted({test for criterion in package["criteria"] if criterion["status"] == "VALID"
                            for test in criterion["tests"]})
        return append_decision_audit(
            _decision_audit_file(), package_id=package["package_id"],
            decision=body.decision.value, notes=body.notes, reviewer_principal=reviewer,
            test_evidence=test_refs, blockers=package["blockers"],
        )
    except EvidenceRegistryError as exc:
        raise HTTPException(503, str(exc)) from None


@router.get("/decisions")
def evidence_decisions(request: Request, package_id: str | None = None):
    _human_acceptance_boundary(request)
    _admin_reviewer(request)
    try:
        records = read_decision_audit(_decision_audit_file())
    except EvidenceRegistryError as exc:
        raise HTTPException(503, str(exc)) from None
    if package_id is not None:
        records = [record for record in records if record["package_id"] == package_id]
    return {"records": records, "audit_status": "VALIDATED_HASH_CHAIN"}


@router.api_route("/human-acceptance", methods=["POST"])
@router.api_route("/human-acceptance/read", methods=["POST"])
async def reject_legacy_human_acceptance():
    raise HTTPException(410, "LEGACY_DECISION_ROUTE_RETIRED; use evidence package and authorized decisions")


@router.post('/intention')
async def intention(request: Request):
    """Local browser intention only; never an operator/authentication bridge."""
    if getattr(request.app.state, 'runtime_profile', None) != 'ATTESTATION':
        raise HTTPException(404, 'ATTESTATION_ONLY')
    # Evidence-only/NORMAL imports must not pull in the private authorization owner.
    from app.approval.runtime_authorization import AuthorizationError, SCOPE
    if (not request.client or request.client.host not in {'127.0.0.1', '::1'}
            or request.headers.get('host') != '127.0.0.1:8000'
            or request.headers.get('origin') not in {'http://127.0.0.1:5173', 'http://127.0.0.1:8000'}
            or request.headers.get('content-type') != 'application/json'):
        raise HTTPException(403, 'BROWSER_BOUNDARY_REJECTED')
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 512:
            raise HTTPException(413, 'BOUNDED_INTENTION_REQUIRED')
    try:
        def unique_fields(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError('duplicate')
                result[key] = value
            return result
        body = json.loads(raw, object_pairs_hook=unique_fields)
        if (not isinstance(body, dict) or set(body) != {'scope', 'evidence_version'}
                or body['scope'] != SCOPE or not isinstance(body['evidence_version'], str)
                or len(body['evidence_version']) != 64
                or any(c not in '0123456789abcdef' for c in body['evidence_version'])):
            raise ValueError('invalid')
    except (ValueError, UnicodeError):
        raise HTTPException(422, 'BOUNDED_INTENTION_REQUIRED') from None
    owner = getattr(request.app.state, 'runtime_authorization', None)
    if owner is None:
        raise HTTPException(503, 'ATTESTATION_AUTHORIZATION_UNAVAILABLE')
    try:
        return owner.browser_intention(**body)
    except AuthorizationError:
        raise HTTPException(409, 'INTENTION_REJECTED_NO_AUTHORITY_GRANTED') from None
