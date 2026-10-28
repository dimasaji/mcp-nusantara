"""Shared fail-closed authorization for privileged API operations."""
from __future__ import annotations

import hmac
import os

from fastapi import HTTPException


def require_admin(token: str | None) -> None:
    expected = os.getenv("NUSANTARA_ADMIN_TOKEN", "")
    if not expected or not token or not hmac.compare_digest(
        token.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(status_code=403, detail="admin token diperlukan")
