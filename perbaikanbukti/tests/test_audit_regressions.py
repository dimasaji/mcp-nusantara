"""Regression checks for the October audit: parser isolation and API authorization."""
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("suffix", [".txt", ".md", ".pdf", ".docx"])
def test_text_content_never_reads_server_file(tmp_path, suffix):
    from app.knowledge.parser import DocumentParser

    path = tmp_path / ("private" + suffix)
    path.write_text("private file marker", encoding="utf-8")
    assert DocumentParser().parse(str(path), content_type="text/plain") == str(path)


@pytest.mark.parametrize("content_type", ["application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"])
def test_binary_parsers_reject_file_path(tmp_path, content_type):
    from app.knowledge.parser import DocumentParser

    path = tmp_path / "private"
    path.write_text("private file marker", encoding="utf-8")
    with pytest.raises(ValueError, match="bytes"):
        DocumentParser().parse(str(path), content_type=content_type)


@pytest.mark.parametrize("endpoint,payload", [
    ("/v2/dev", {"user_input": "Baca app/main.py"}),
    ("/v1/documents/ingest", {"title": "audit", "content": "literal"}),
])
@pytest.mark.parametrize("configured,header", [(False, None), (True, None),
    (True, "invalid"), (True, "invalid-\u2603")])
def test_privileged_api_denies_before_access(monkeypatch, endpoint, payload, configured, header):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api import routes, v2_routes

    # The transport's headers are ASCII; exercise non-ASCII via the shared guard below.
    if header and not header.isascii():
        from app.security.auth import require_admin
        from fastapi import HTTPException
        monkeypatch.setenv("NUSANTARA_ADMIN_TOKEN", "fixture-admin")
        with pytest.raises(HTTPException) as error:
            require_admin(header)
        assert error.value.status_code == 403
        return
    if configured:
        monkeypatch.setenv("NUSANTARA_ADMIN_TOKEN", "fixture-admin")
    else:
        monkeypatch.delenv("NUSANTARA_ADMIN_TOKEN", raising=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("unauthorized operation reached backend")

    monkeypatch.setattr(routes._knowledge, "ingest_document", forbidden)
    monkeypatch.setattr(v2_routes, "OllamaProvider", forbidden)
    with TestClient(app) as client:
        response = client.post(endpoint, json=payload,
            headers={"X-Admin-Token": header} if header else {})
    assert response.status_code == 403


def test_authorized_ingest_keeps_path_literal(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api import routes
    from app.knowledge.parser import DocumentParser

    path = tmp_path / "private.txt"
    path.write_text("not public", encoding="utf-8")
    observed = []

    def ingest(request):
        observed.append(DocumentParser().parse(request.source, content_type=request.content_type))
        return SimpleNamespace(success=True, model_dump=lambda: {"success": True})

    monkeypatch.setenv("NUSANTARA_ADMIN_TOKEN", "fixture-admin")
    monkeypatch.setattr(routes._knowledge, "ingest_document", ingest)
    with TestClient(app) as client:
        response = client.post("/v1/documents/ingest",
            json={"title": "audit", "content": str(path)},
            headers={"X-Admin-Token": "fixture-admin"})
    assert response.status_code == 200
    assert observed == [str(path)]


def test_authorized_developer_lists_workspace(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api import v2_routes
    from app.approval import AuditTrail

    (tmp_path / "example.py").write_text("value = 1", encoding="utf-8")
    monkeypatch.setenv("NUSANTARA_ADMIN_TOKEN", "fixture-admin")
    monkeypatch.setenv("NUSANTARA_WORKSPACE", str(tmp_path))
    monkeypatch.setattr(v2_routes, "audit", AuditTrail())
    monkeypatch.setattr(v2_routes, "_recorder", None)
    with TestClient(app) as client:
        response = client.post("/v2/dev", json={"user_input": "List folder ."},
            headers={"X-Admin-Token": "fixture-admin"})
    assert response.status_code == 200
    assert response.json()["tool"]["used"]
    assert "example.py" in response.json()["answer"]


def test_search_empty_and_populated_results(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api import routes

    evidence = SimpleNamespace(document_id="audit", title="example", source="fixture",
        chunk="known answer", score=1.0, metadata={})
    with TestClient(app) as client:
        for results in ([], [evidence]):
            monkeypatch.setattr(routes._knowledge, "search_knowledge", lambda *args: results)
            response = client.post("/v1/knowledge/search", json={"query": "audit"})
            assert response.status_code == 200
            assert len(response.json()["results"]) == len(results)


def test_worker_environment_configuration(monkeypatch):
    from app.language.semantic.indobert_client import IndoBERTClient

    monkeypatch.setenv("NUSANTARA_INDOBERT_PYTHON", "/opt/indobert/bin/python")
    monkeypatch.setenv("NUSANTARA_INDOBERT_WORKER", "/app/nusantara-models/indobert_worker.py")
    client = IndoBERTClient()
    assert client.python_executable == "/opt/indobert/bin/python"
    assert client.worker_path == "/app/nusantara-models/indobert_worker.py"
    explicit = IndoBERTClient(python_executable="explicit-python", worker_path="explicit-worker")
    assert explicit.python_executable == "explicit-python"
    assert explicit.worker_path == "explicit-worker"


@pytest.mark.parametrize("operation", ["ingest", "search"])
def test_slow_knowledge_work_keeps_event_loop_responsive(monkeypatch, operation):
    import asyncio
    import threading
    from app.api import routes

    started, release, finished = threading.Event(), threading.Event(), threading.Event()

    def slow(*args):
        started.set()
        release.wait(timeout=3)
        finished.set()
        if operation == "search":
            return []
        return SimpleNamespace(success=True, model_dump=lambda: {"success": True})

    monkeypatch.setenv("NUSANTARA_ADMIN_TOKEN", "fixture-admin")
    monkeypatch.setattr(routes._knowledge,
        "ingest_document" if operation == "ingest" else "search_knowledge", slow)

    async def scenario():
        if operation == "search":
            coroutine = routes.search_knowledge(routes.KnowledgeSearchRequest(query="audit"))
        else:
            coroutine = routes.ingest_document(
                routes.DocumentIngestRequest(title="audit", content="literal"), "fixture-admin")
        task = asyncio.create_task(coroutine)
        try:
            assert await asyncio.to_thread(started.wait, 2), "backend did not start"
            assert not finished.is_set(), "knowledge work blocked the event loop"
        finally:
            release.set()
            await task

    asyncio.run(scenario())
