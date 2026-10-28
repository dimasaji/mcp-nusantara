"""Local Control Plane reads and ATTESTATION-only untrusted PENDING intentions."""
from urllib.parse import urlsplit
import json
from fastapi import APIRouter, HTTPException, Request
from app.approval.runtime_authorization import AuthorizationError, SCOPE
from app.core.control_plane_projection import project

router = APIRouter(prefix='/v1/control-plane', tags=['engineering-control-plane'])


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


@router.post('/intention')
async def intention(request: Request):
    """Local browser intention only; never an operator/authentication bridge."""
    if getattr(request.app.state, 'runtime_profile', None) != 'ATTESTATION':
        raise HTTPException(404, 'ATTESTATION_ONLY')
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
