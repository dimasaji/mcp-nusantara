"""Real ASGI preview requests, never the live application composition."""
import ast
import os
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.api.inspection_preview import router

GOALS = ["Perbaiki RAG Nusantara.", "Periksa kenapa jawaban AI kurang akurat.",
         "Buat Nusantara lebih cepat.", "Periksa konfigurasi provider.",
         "Cari masalah pada Developer Engine."]


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("NUSANTARA_ADMIN_TOKEN", "fixture-only-token")
    instance = FastAPI()
    instance.state.runtime_profile = "NORMAL"
    instance.include_router(router, prefix="/v1")
    from app.approval import AuditTrail
    from app.devcore import DevCore
    from app.devcore.workspace import Workspace
    def no_construction(*args, **kwargs):
        raise AssertionError("Preview must not construct execution or persistence owners")
    for owner in (DevCore, Workspace, AuditTrail):
        monkeypatch.setattr(owner, "__init__", no_construction)
    return instance


_DEFAULT_TOKEN = object()


async def post(app, body, token=_DEFAULT_TOKEN):
    if token is _DEFAULT_TOKEN:
        token = os.environ.get("NUSANTARA_ADMIN_TOKEN")
    headers = {"X-Admin-Token": token} if token is not None else {}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://fixture.invalid") as client:
        return await client.post("/v1/dev/inspection-preview", json=body, headers=headers)


@pytest.mark.parametrize("goal", GOALS)
async def test_supported_goals(app, goal):
    response = await post(app, {"user_input": goal})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    value = response.json()
    assert value["profile"] == "NORMAL" and value["scope"] == "inspection-preview"
    assert value["source"] == "/v1/dev/inspection-preview" and value["captured_at"]
    for name in ("runtime_identity", "active_process_build", "provider_model_correlation"):
        assert value[name] == "NOT_VERIFIED"
    preview = value["inspection_preview"]
    assert preview["status"] == "PREVIEW_READY" and preview["goal"] == goal
    assert preview["authorized_operations"] == [] and preview["root_cause"] == "UNKNOWN"
    assert preview["file_evidence"] == "CANDIDATES_NOT_INSPECTED"
    assert preview["goal_resolution_requirements"] == "UNKNOWN_PENDING_DISCOVERY"
    assert all(preview[n] == "NO" for n in (
        "write_required", "runtime_required", "provider_required", "database_required"))
    assert preview == (await post(app, {"user_input": goal})).json()["inspection_preview"]


@pytest.mark.parametrize("token", [None, "", "wrong", "fixture-only-token-wrong"])
async def test_invalid_auth(app, token):
    assert (await post(app, {"user_input": GOALS[0]}, token)).status_code == 403


async def test_absent_server_token(app, monkeypatch):
    monkeypatch.delenv("NUSANTARA_ADMIN_TOKEN")
    assert (await post(app, {"user_input": GOALS[0]})).status_code == 403


@pytest.mark.parametrize("profile", ["ATTESTATION", "UNKNOWN", None])
async def test_normal_only(app, profile):
    app.state.runtime_profile = profile
    assert (await post(app, {"user_input": GOALS[0]})).status_code == 403


@pytest.mark.parametrize("goal", ["restart nusantara", "generate jawaban AI", "hapus database",
    "deploy nusantara", "authorize runtime", "panggil provider", "jalankan model",
    "ARM", "EXECUTE", "Baca app/main.py", "List folder .", "halo", "perbaiki yang lain"])
async def test_non_preview_rejected(app, goal):
    response = await post(app, {"user_input": goal})
    assert response.status_code in (403, 422)
    assert "inspection_preview" not in response.json()


@pytest.mark.parametrize("body", [{}, {"user_input": ""}, {"user_input": "   "},
    {"user_input": "x" * 4001}, {"user_input": 42},
    {"user_input": GOALS[0], "execute": True}, {"user_input": GOALS[0], "session_id": "dev"},
    {"user_input": GOALS[0], "model": "override"}])
async def test_strict_payload(app, body):
    assert (await post(app, body)).status_code == 422


async def test_other_methods_and_paths_unavailable(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://fixture.invalid") as client:
        assert (await client.get("/v1/dev/inspection-preview")).status_code == 405
        assert (await client.post("/v1/dev/inspection-preview/execute")).status_code == 404


def test_preview_is_registered_in_v1_without_loading_v2():
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "app/main.py").read_text(encoding="utf-8-sig"))
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert "app.api.inspection_preview" in imports
    assert "app.api.v2_routes" not in imports
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "include_router"]
    assert any(call.args and isinstance(call.args[0], ast.Name)
               and call.args[0].id == "inspection_preview_router"
               and any(keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant)
                       and keyword.value.value == "/v1" for keyword in call.keywords)
               for call in calls)
