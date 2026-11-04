"""Knowledge operations HTTP boundary with an overridable storage owner."""
from typing import Literal
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.knowledge.sop_review import SOPReview
from app.knowledge.sop_metadata import SOPMetadata
from app.security.auth import require_admin

CorrectionCategory = Literal['unknown', 'extraction', 'retrieval', 'context', 'answer', 'claim_check', 'citation_viewer']


class ReviewDecision(BaseModel):
    version_id: str = Field(min_length=64, max_length=64)
    action: Literal['content_ok', 'problem', 'resolve', 'approve', 'reject', 'defer', 'revoke']
    note: str = Field(default='', max_length=2000)
    problem_id: str | None = None
    category: CorrectionCategory = 'unknown'


class TrialRating(BaseModel):
    version_id: str = Field(min_length=64, max_length=64)
    ok: bool
    note: str = Field(default='', max_length=2000)
    category: CorrectionCategory = 'unknown'


class ExtractionRequest(BaseModel):
    version_id: str = Field(pattern=r'^[a-f0-9]{64}$')


class MetadataConfirmation(BaseModel):
    version_id: str = Field(pattern=r'^[a-f0-9]{64}$')
    expected_event_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    metadata: SOPMetadata


def get_knowledge_engine():
    # Resolve the existing Chat owner only on a real application request.
    # Tests override this dependency without importing the live composition.
    from app.api.routes import _knowledge
    return _knowledge


def get_chat_memory():
    from app.api.routes import _gate_integration
    return _gate_integration.memory


def get_chat_source_provider():
    from app.core.config import settings
    return settings.configuration_snapshot()[0].llm.provider


def create_knowledge_pipeline_router(run_sync):
    router = APIRouter(prefix='/knowledge/pipeline')

    @router.get('/reviews/{document_id}/citation')
    def chat_citation(document_id: str, request_id: str = Query(pattern=r'^[a-f0-9]{32}$'),
                      page_number: int = Query(ge=1), x_chat_session: str = Header(default=''),
                      x_admin_token: str | None = Header(default=None),
                      knowledge=Depends(get_knowledge_engine), memory=Depends(get_chat_memory),
                      provider=Depends(get_chat_source_provider)):
        from fastapi.responses import Response

        from app.security.v1_knowledge import V1KnowledgeBoundary, v1_session_id, valid_chat_session

        require_admin(x_admin_token)
        if not valid_chat_session(x_chat_session):
            raise HTTPException(403, 'CHAT_SESSION_CAPABILITY_REQUIRED')
        session = v1_session_id(x_chat_session, operator=True)
        turn = next((item for item in memory.chat_history(session)
                     if item.get('request_id') == request_id and item.get('status') == 'SUCCEEDED'), None)
        answer = turn.get('answer') if turn else None
        if not isinstance(answer, dict) or not any(
                item.get('document_id') == document_id and page_number in item.get('pages', [])
                for item in answer.get('evidence', [])):
            raise HTTPException(404, 'CHAT_CITATION_NOT_FOUND')
        review = SOPReview(knowledge)
        access = turn.get('source_access', {'mode': 'approved'})
        if not isinstance(access, dict) or access.get('mode') not in {'approved', 'review_trial'}:
            raise HTTPException(409, 'CHAT_SOURCE_ACCESS_CHANGED')
        trial = access['mode'] == 'review_trial'
        boundary = V1KnowledgeBoundary(knowledge, operator=True, provider=provider,
            review_trial=trial, sop_version=access.get('version') if trial else None)
        versions = turn.get('source_versions')
        boundary.validate_response(answer, versions)
        path, raw, _ = review.source(document_id)
        if path is None:
            raise HTTPException(404, 'File sumber belum ditemukan')
        if path.suffix.lower() != '.pdf':
            raise HTTPException(415, 'Sitasi halaman hanya tersedia untuk PDF')
        import pymupdf

        with pymupdf.open(stream=raw, filetype='pdf') as pdf:
            if page_number > len(pdf):
                raise HTTPException(422, 'DOCUMENT_PAGE_INVALID')
        boundary.validate_response(answer, versions)
        return Response(raw, media_type='application/pdf', headers={'Cache-Control': 'no-store',
            'X-Content-Type-Options': 'nosniff', 'X-Source-Page': str(page_number),
            'Content-Disposition': 'inline; filename="source.pdf"'})

    @router.get('/reviews/{document_id}')
    def review_detail(document_id: str, x_admin_token: str | None = Header(default=None), knowledge=Depends(get_knowledge_engine)):
        require_admin(x_admin_token)
        try:
            review = SOPReview(knowledge)
            from app.knowledge.document_tools import DocumentReadError, DocumentTools
            tools = DocumentTools(knowledge, operator=True)
            for _ in range(3):
                detail = review.detail(document_id)
                try:
                    status = tools.status(document_id, detail['version_id'])
                    try:
                        extracted = tools.inspect(document_id, detail['version_id'])
                    except DocumentReadError as exc:
                        if str(exc).startswith(('DOCUMENT_VERSION_CHANGED', 'DOCUMENT_VERSION_NOT_FOUND')):
                            continue
                        extracted = None
                except DocumentReadError as exc:
                    if str(exc).startswith(('DOCUMENT_VERSION_CHANGED', 'DOCUMENT_VERSION_NOT_FOUND')):
                        continue
                    raise
                current = review.detail(document_id)
                if (current['version_id'] != detail['version_id']
                        or current['extraction_job_id'] != status.get('job_id')):
                    continue
                current['extraction'] = status
                current['extracted_blocks'] = extracted['blocks'] if extracted else []
                current['comparison'] = (tools.compare_previous(document_id, detail['version_id'])
                    if extracted and extracted['status'] == 'COMPLETE' else None)
                if extracted:
                    current['extraction']['warnings'] = extracted.get('warnings', [])
                return current
            raise ValueError('Hasil pembacaan berubah. Muat ulang pemeriksaan versi terbaru.')
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None

    @router.post('/reviews/{document_id}/process')
    def process_review(document_id: str, body: ExtractionRequest, x_admin_token: str | None = Header(default=None), knowledge=Depends(get_knowledge_engine)):
        require_admin(x_admin_token)
        from app.knowledge.document_tools import DocumentTools
        try:
            return DocumentTools(knowledge, operator=True).process(document_id, body.version_id, force=True)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None

    @router.post('/reviews/{document_id}/metadata')
    def confirm_metadata(document_id: str, body: MetadataConfirmation, x_admin_token: str | None = Header(default=None), knowledge=Depends(get_knowledge_engine)):
        require_admin(x_admin_token)
        try:
            return SOPReview(knowledge).confirm_metadata(document_id, body.version_id,
                body.metadata.model_dump(), 'shared-admin-token', expected_event_id=body.expected_event_id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None

    @router.get('/reviews/{document_id}/source')
    def review_source(document_id: str, version_id: str | None = None, page_number: int | None = None, x_admin_token: str | None = Header(default=None), knowledge=Depends(get_knowledge_engine)):
        from fastapi.responses import Response
        require_admin(x_admin_token)
        try:
            review = SOPReview(knowledge)
            if version_id is not None:
                review._check(document_id, version_id)
            path, raw, digest = review.source(document_id)
        except ValueError:
            path = None
        if path is None:
            raise HTTPException(404, 'File sumber belum ditemukan')
        if page_number is not None:
            if path.suffix.lower() != '.pdf':
                raise HTTPException(415, 'Pratinjau halaman hanya tersedia untuk PDF')
            import pymupdf
            with pymupdf.open(stream=raw, filetype='pdf') as pdf:
                if not 1 <= page_number <= len(pdf):
                    raise HTTPException(422, 'DOCUMENT_PAGE_INVALID')
                page = pdf[page_number-1]
                scale = min(1.25, 1600 / max(1, page.rect.width, page.rect.height))
                preview = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).tobytes('png')
            return Response(preview, media_type='image/png', headers={'Cache-Control': 'no-store',
                'X-Content-Type-Options': 'nosniff', 'X-Source-SHA256': digest, 'X-Source-Page': str(page_number)})
        return Response(raw, media_type='application/pdf' if path.suffix.lower() == '.pdf' else 'application/octet-stream',
            headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})

    @router.post('/reviews/{document_id}/decision')
    def review_decision(document_id: str, body: ReviewDecision, x_admin_token: str | None = Header(default=None), knowledge=Depends(get_knowledge_engine)):
        require_admin(x_admin_token)
        try:
            return SOPReview(knowledge).decide(document_id, body.version_id, body.action,
                'shared-admin-token', body.note, body.problem_id, category=body.category)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None

    @router.post('/reviews/{document_id}/trials/{trial_id}/rating')
    def trial_rating(document_id: str, trial_id: str, body: TrialRating, x_admin_token: str | None = Header(default=None), knowledge=Depends(get_knowledge_engine)):
        require_admin(x_admin_token)
        try:
            return SOPReview(knowledge).rate(document_id, body.version_id, trial_id,
                body.ok, body.note, 'shared-admin-token', category=body.category)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None

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
        status = knowledge.knowledge_pipeline_status()
        pilot = next((doc for doc in status.get('documents', []) if doc['title'] == 'PERMOHONAN DATA PRIBADI'), None)
        if pilot:
            detail = SOPReview(knowledge).detail(pilot['document_id'])
            pilot['review_status'] = detail['status']
        return status

    @router.post('/watch')
    def configure_knowledge_watch(
        enabled: bool,
        x_admin_token: str | None = Header(default=None),
        knowledge=Depends(get_knowledge_engine),
    ):
        require_admin(x_admin_token)
        return knowledge.set_knowledge_watch(enabled)

    return router

