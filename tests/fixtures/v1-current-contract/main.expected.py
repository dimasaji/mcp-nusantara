"""FastAPI application - Nusantara Core + Hermes."""
from contextlib import asynccontextmanager
import time
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Explicit local evidence-only boot; default runtime composition is preserved.
_READ_ONLY_EVIDENCE = os.environ.get('NUSANTARA_CONTROL_PLANE_READ_ONLY') == '1'
_configuration = None
_ATTESTATION = False
if not _READ_ONLY_EVIDENCE:
    from app.core.config import settings

    # Compose through the existing owner before either API constructs dependencies.
    _configuration = settings.effective_configuration
    _ATTESTATION = _configuration.runtime.profile == 'ATTESTATION'
    if not _ATTESTATION:
        from app.api.routes import router as api_router
        from app.api.v2_routes import router as v2_router
from app.api.control_plane import router as control_plane_router
from app.observability import configure_logging, request_context, metrics
from app.exceptions import register_exception_handlers
from app.core.runtime_identity import BUILD_ID
from app.core.runtime_attestation import install_runtime_attestation

UI_FILE = Path(__file__).parent / "ui" / "index.html"
CONTROL_PLANE_BUNDLE = Path(__file__).resolve().parents[1] / 'control-plane' / 'dist'


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Nusantara Core + Hermes API",
    description="AI Core Engine and Agent/Orchestrator API",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.effective_configuration = _configuration
app.state.configuration_owner = settings if not _READ_ONLY_EVIDENCE and not _ATTESTATION else None
app.state.runtime_profile = 'ATTESTATION' if _ATTESTATION else 'NORMAL'
if not _READ_ONLY_EVIDENCE and not _ATTESTATION:
    from fastapi.staticfiles import StaticFiles
    app.mount('/assets', StaticFiles(directory=CONTROL_PLANE_BUNDLE / 'assets', check_dir=False), name='user-assets')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8765", "http://127.0.0.1:8765", "http://localhost:5179", "http://127.0.0.1:5179"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
register_exception_handlers(app)
if not _READ_ONLY_EVIDENCE and not _ATTESTATION:
    app.include_router(api_router)
    app.include_router(v2_router)
app.include_router(control_plane_router)
if not _READ_ONLY_EVIDENCE and not _ATTESTATION:
    configure_logging(_configuration.runtime.log_level)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    """Correlation ID + V1 HTTP observability."""
    incoming = '' if getattr(request.app.state, 'runtime_profile', 'NORMAL') == 'ATTESTATION' else request.headers.get("x-request-id", "")[:64]
    rid = incoming if incoming.replace("-", "").replace("_", "").isalnum() else None

    started = time.perf_counter()
    metrics.incr("requests_total")

    with request_context(request_id=rid or None) as ids:
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = ids["request_id"]
            return response
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            metrics.observe("http_request", elapsed_ms)


@app.get("/health")
async def health_check():
    if _READ_ONLY_EVIDENCE:
        return {'status': 'evidence_only', 'runtime': 'NOT_VERIFIED', 'mode': 'READ_ONLY'}
    return {"status": "ok", "version": "0.1.0", "build_id": BUILD_ID}


@app.get("/", include_in_schema=False)
@app.get("/ui", include_in_schema=False)
async def dashboard():
    if _READ_ONLY_EVIDENCE:
        from fastapi import HTTPException
        raise HTTPException(404, 'Legacy runtime UI is unavailable in evidence-only mode')
    if _ATTESTATION:
        return FileResponse(UI_FILE)
    if not (CONTROL_PLANE_BUNDLE / 'index.html').is_file():
        from fastapi import HTTPException
        raise HTTPException(503, 'User UI build belum tersedia.')
    return FileResponse(CONTROL_PLANE_BUNDLE / 'index.html')


for ui_path in ('console', 'review-execute', 'overview', 'system', 'evidence', 'test', 'review', 'decision',
                'engineering-overview', 'roadmap', 'architecture', 'engineering',
                'governance', 'verification', 'runtime', 'knowledge'):
    if not _READ_ONLY_EVIDENCE and not _ATTESTATION:
        app.add_api_route('/' + ui_path, dashboard, methods=['GET'], include_in_schema=False)


if _ATTESTATION:
    from app.api.runtime_verification import install_runtime_verification
    from app.approval.runtime_authorization import install_authorization_foundation
    controller = install_runtime_verification(app, _configuration)
    # No policy provisioning, IPC listener, live grant or deployment authorization.
    install_authorization_foundation(app, controller)

install_runtime_attestation(app, entrypoint='app.main:app')
