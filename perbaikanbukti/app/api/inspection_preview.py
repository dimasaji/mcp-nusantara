"""Authenticated NORMAL planning only; no DevCore, tools or persistence."""
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.devcore.inspection import inspection_preview
from app.security.auth import require_admin

router = APIRouter()
_NO_STORE = {"Cache-Control": "no-store"}


class InspectionPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    user_input: str = Field(min_length=1, max_length=4000)


@router.post("/dev/inspection-preview")
def preview(body: InspectionPreviewRequest, request: Request, response: Response,
            x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    require_admin(x_admin_token)
    if getattr(request.app.state, "runtime_profile", None) != "NORMAL":
        raise HTTPException(403, "NORMAL_PREVIEW_ONLY", headers=_NO_STORE)
    result = inspection_preview(body.user_input)
    if result is not None and result["status"] == "HUMAN_DECISION_REQUIRED":
        raise HTTPException(403, "PREVIEW_ONLY_OPERATION_REJECTED", headers=_NO_STORE)
    if result is None or result["status"] != "PREVIEW_READY":
        raise HTTPException(422, "SUPPORTED_PREVIEW_GOAL_REQUIRED", headers=_NO_STORE)
    response.headers.update(_NO_STORE)
    return {
        "scope": "inspection-preview", "profile": "NORMAL",
        "source": "/v2/dev/inspection-preview",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "runtime_identity": "NOT_VERIFIED", "active_process_build": "NOT_VERIFIED",
        "provider_model_correlation": "NOT_VERIFIED", "inspection_preview": result,
    }
