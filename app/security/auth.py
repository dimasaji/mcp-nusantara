"""Shared fail-closed authorization for privileged API operations."""
from __future__ import annotations

import hmac
import os
from pathlib import Path

from fastapi import HTTPException
from dotenv import dotenv_values


def require_admin(token: str | None) -> None:
    # Match V1 Settings' .env source even when Uvicorn was started without
    # --env-file. An explicit process value (including empty) takes precedence.
    expected = os.getenv("NUSANTARA_ADMIN_TOKEN")
    if expected is None:
        expected = dotenv_values(Path('.env'), encoding='utf-8').get('NUSANTARA_ADMIN_TOKEN')
    if not expected or not token or not hmac.compare_digest(
        token.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(status_code=403, detail="admin token diperlukan")
