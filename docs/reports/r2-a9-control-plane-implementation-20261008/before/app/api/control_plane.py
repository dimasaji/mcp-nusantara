"""Local-only, GET-only Control Plane projections on the existing FastAPI app."""
from urllib.parse import urlsplit
from fastapi import APIRouter, HTTPException, Request
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
