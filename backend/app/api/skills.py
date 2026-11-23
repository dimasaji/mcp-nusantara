"""Authenticated discovery and invocation of core skills."""
from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.knowledge_pipeline import get_knowledge_engine
from app.security.auth import require_admin
from app.skills.composition import OPERATOR_PERMISSIONS


class SkillInvocation(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    arguments: dict = Field(default_factory=dict)


def create_skill_router(run_sync):
    router = APIRouter(prefix='/skills', tags=['skills'])

    @router.get('')
    def list_skills(x_admin_token: str | None = Header(default=None), knowledge=Depends(get_knowledge_engine)):
        require_admin(x_admin_token)
        return {'skills': knowledge.skills.catalog(role='operator', permissions=set(OPERATOR_PERMISSIONS))}

    @router.post('/{name}/run')
    async def run_skill(body: SkillInvocation, name: str = Path(pattern=r'^[a-z][a-z0-9_.-]{0,63}$'),
                        x_admin_token: str | None = Header(default=None), knowledge=Depends(get_knowledge_engine)):
        require_admin(x_admin_token)
        def invoke():
            return knowledge.skills.execute(name, body.arguments, role='operator',
                permissions=set(OPERATOR_PERMISSIONS), requested_by='operator-api')
        result = await run_sync(invoke, timeout_s=35)
        code = {'executed': 200, 'unknown_tool': 404, 'invalid_input': 422,
                'denied': 403, 'failed': 503, 'pending_approval': 409}[result.status]
        return JSONResponse(status_code=code, content=asdict(result))

    return router
