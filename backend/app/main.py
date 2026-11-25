"""FastAPI application - Nusantara Core + Hermes."""
from contextlib import asynccontextmanager
import time
import os
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

os.environ['HAYSTACK_TELEMETRY_ENABLED'] = 'False'

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
        from app.api.inspection_preview import router as inspection_preview_router
        from app.api.routes import router as api_router
        # V1-only runtime: keep V2 code archived in place without importing its
        # model/index services or registering any /v2 endpoints.
from app.api.control_plane import router as control_plane_router
from app.observability import configure_logging, request_context, metrics
from app.exceptions import register_exception_handlers
from app.core.runtime_identity import BUILD_ID
from app.core.runtime_attestation import install_runtime_attestation

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT.name == 'backend':
    PROJECT_ROOT = PROJECT_ROOT.parent
UI_FILE = Path(__file__).parent / "ui" / "index.html"
CONTROL_PLANE_BUNDLE = Path(os.getenv('NUSANTARA_FRONTEND_DIST', str(PROJECT_ROOT / 'frontend' / 'dist')))
_LOCAL_SERVICES_FILE = PROJECT_ROOT / 'config' / 'local-services.json'
_LOCAL_SERVICES = json.loads(_LOCAL_SERVICES_FILE.read_text(encoding='utf-8')) if _LOCAL_SERVICES_FILE.exists() else {'frontendPort': 5180}
_SERVE_BUNDLE = os.environ.get('NUSANTARA_SERVE_BUNDLE') == '1'


@asynccontextmanager
async def lifespan(app: FastAPI):
    watcher = None
    if not _READ_ONLY_EVIDENCE and not _ATTESTATION:
        import asyncio
        import logging
        from app.api.routes import _knowledge
        logger=logging.getLogger(__name__)
        async def monitor():
            while True:
                try:
                    await asyncio.to_thread(_knowledge.scan_knowledge_watch)
                    if hasattr(_knowledge, 'rag') and callable(getattr(_knowledge, '_pipeline_db', None)):
                        from app.knowledge.document_tools import DocumentTools
                        await asyncio.to_thread(lambda: DocumentTools(_knowledge, operator=True).resume_queued())
                except Exception:
                    # Pipeline failures are retained per source; service stays available.
                    logger.exception('Knowledge folder monitor failed')
                await asyncio.sleep(5)
        watcher=asyncio.create_task(monitor())
    try:
        yield
    finally:
        if watcher:
            watcher.cancel()


app = FastAPI(
    title="Nusantara Core + Hermes API",
    description="AI Core Engine and Agent/Orchestrator API",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.effective_configuration = _configuration
app.state.configuration_owner = settings if not _READ_ONLY_EVIDENCE and not _ATTESTATION else None
app.state.runtime_profile = 'ATTESTATION' if _ATTESTATION else 'NORMAL'
if _SERVE_BUNDLE:
    if not (CONTROL_PLANE_BUNDLE / 'index.html').is_file():
        raise RuntimeError('FRONTEND_BUNDLE_MISSING')
    app.mount('/assets', StaticFiles(directory=CONTROL_PLANE_BUNDLE / 'assets'), name='frontend-assets')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8765", "http://127.0.0.1:8765",
                   f"http://localhost:{_LOCAL_SERVICES['frontendPort']}", f"http://127.0.0.1:{_LOCAL_SERVICES['frontendPort']}"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
register_exception_handlers(app)
if not _READ_ONLY_EVIDENCE and not _ATTESTATION:
    app.include_router(api_router)
    app.include_router(inspection_preview_router, prefix='/v1')
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


@app.get("/v1/metrics")
async def v1_metrics():
    """In-process counters and latency, projected into the V1 contract shape.

    `/health` reports process liveness only; this endpoint is what makes the
    difference between "the process is up" and "the product is being used".
    """
    snap = metrics.snapshot()
    return {
        "status": "ok",
        "metrics": {
            "version": "0.1.0",
            "uptime_seconds": snap["uptime_s"],
            "requests_total": snap["counters"].get("requests_total", 0),
            "latency": snap["latency"],
            "counters": snap["counters"],
        },
    }


@app.get("/v1/health/ready")
@app.get("/readyz")
async def readiness_check():
    """Readiness probe that exercises the two dependencies whose failure turned
    `/v1/chat` into a generic 500 while `/v1/health` still reported `ok`.

    It deliberately does not call the model: a readiness probe that generates
    tokens is a cost and latency trap. It verifies the knowledge database is
    queryable and the provider endpoint answers.
    """
    import urllib.request

    components: dict[str, object] = {}
    database: dict[str, object] = {"status": "unknown"}
    try:
        from app.api.routes import _knowledge

        # `_knowledge.list_documents()` is the public V1 accessor used by the
        # routes themselves; it performs a real read-only database query, so a
        # reachable-but-empty or corrupt database is distinguishable from a
        # healthy one without starting the embedding worker.
        listing = _knowledge.list_documents()
        total = getattr(listing, "total", None)
        if total is None:
            total = len(getattr(listing, "documents", None) or [])
        database = {
            "status": "ok" if total else "empty",
            "documents": int(total),
        }
    except Exception as exc:  # noqa: BLE001 - probe reports, never raises
        database = {"status": "error", "error": type(exc).__name__}
    components["knowledge_database"] = database

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    provider: dict[str, object] = {"status": "unknown"}
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=2) as response:  # noqa: S310 - fixed loopback URL
            provider = {"status": "ok" if response.status == 200 else "error", "http_status": response.status}
    except Exception as exc:  # noqa: BLE001
        provider = {"status": "unavailable", "error": type(exc).__name__}
    components["provider"] = provider

    ready = all(component.get("status") == "ok" for component in components.values())
    return {"status": "ready" if ready else "degraded", "components": components}


@app.get("/", include_in_schema=False)
@app.get("/ui", include_in_schema=False)
@app.get("/assistant", include_in_schema=False)
async def dashboard(request: Request):
    if _READ_ONLY_EVIDENCE:
        from fastapi import HTTPException
        raise HTTPException(404, 'Legacy runtime UI is unavailable in evidence-only mode')
    if _ATTESTATION:
        return FileResponse(UI_FILE)
    if _SERVE_BUNDLE:
        return FileResponse(CONTROL_PLANE_BUNDLE / 'index.html')
    target = request.url.replace(scheme='http', netloc=f"{_LOCAL_SERVICES.get('host', '127.0.0.1')}:{_LOCAL_SERVICES['frontendPort']}")
    return RedirectResponse(str(target), status_code=307)


for ui_path in ('console', 'review-execute', 'overview', 'system', 'evidence', 'test', 'review', 'decision',
                'engineering-overview', 'roadmap', 'architecture', 'engineering',
                'governance', 'verification', 'runtime', 'knowledge',
                'dashboard', 'workspace', 'tasks', 'blockers', 'approvals', 'costs', 'settings', 'technical'):
    if not _READ_ONLY_EVIDENCE and not _ATTESTATION:
        app.add_api_route('/' + ui_path, dashboard, methods=['GET'], include_in_schema=False)


if _ATTESTATION:
    from app.api.runtime_verification import install_runtime_verification
    from app.approval.runtime_authorization import install_authorization_foundation
    controller = install_runtime_verification(app, _configuration)
    # No policy provisioning, IPC listener, live grant or deployment authorization.
    install_authorization_foundation(app, controller)

install_runtime_attestation(app, entrypoint='app.main:app')

