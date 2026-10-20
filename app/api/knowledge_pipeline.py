"""Knowledge operations HTTP boundary with an overridable storage owner."""
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.security.auth import require_admin


def get_knowledge_engine():
    # Resolve the existing Chat owner only on a real application request.
    # Tests override this dependency without importing the live composition.
    from app.api.routes import _knowledge
    return _knowledge


def create_knowledge_pipeline_router(run_sync):
    router = APIRouter(prefix='/knowledge/pipeline')

    @router.post('/documents')
    async def add_knowledge_source(
        request: Request,
        x_admin_token: str | None = Header(default=None),
        x_document_name: str | None = Header(default=None),
        knowledge=Depends(get_knowledge_engine),
    ):
        require_admin(x_admin_token)
        filename = unquote(x_document_name or 'document.txt').replace('\\', '/').split('/')[-1]
        if int(request.headers.get('content-length', '0') or 0) > 20 * 1024 * 1024:
            raise HTTPException(413, 'FILE_TOO_LARGE_MAX_20MB')
        raw = await request.body()
        if not raw:
            raise HTTPException(422, 'DOCUMENT_EMPTY')
        try:
            return await run_sync(knowledge.process_knowledge_source, filename, raw, timeout_s=90)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(500, f'KNOWLEDGE_PIPELINE_FAILED:{type(exc).__name__}') from exc

    @router.post('/runs/{run_id}/retry')
    async def retry_knowledge_source(run_id: str, x_admin_token: str | None = Header(default=None),
                                     knowledge=Depends(get_knowledge_engine)):
        require_admin(x_admin_token)
        try:
            return await run_sync(knowledge.retry_knowledge_source,run_id,timeout_s=90)
        except ValueError as exc:
            raise HTTPException(409,str(exc)) from None

    @router.get('/status')
    def knowledge_pipeline_status(
        x_admin_token: str | None = Header(default=None),
        knowledge=Depends(get_knowledge_engine),
    ):
        require_admin(x_admin_token)
        return knowledge.knowledge_pipeline_status()

    @router.post('/watch')
    def configure_knowledge_watch(
        enabled: bool,
        x_admin_token: str | None = Header(default=None),
        knowledge=Depends(get_knowledge_engine),
    ):
        require_admin(x_admin_token)
        return knowledge.set_knowledge_watch(enabled)

    return router
