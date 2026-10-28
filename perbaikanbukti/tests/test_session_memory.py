from pathlib import Path

import pytest

from app.memory.session_adapter import SessionMemory


def test_isolation_restart_retention_and_delete(tmp_path):
    now = [100]
    memory = SessionMemory(tmp_path, retention_s=10, clock=lambda: now[0])
    first, second = memory.new_session(), memory.new_session()
    memory.write(first, "Hello", "private first response")
    assert memory.read(second) == ""
    restarted = SessionMemory(tmp_path, retention_s=10, clock=lambda: now[0])
    assert "private first" in restarted.read(first)
    now[0] = 111
    with pytest.raises(ValueError, match="expired"):
        restarted.read(first)
    assert not restarted.delete(second)  # expired sessions were purged on access
    with pytest.raises(ValueError):
        restarted.read(second)


@pytest.mark.parametrize("operation", ["restart", "create", "read", "write"])
def test_expired_histories_removed_from_disk(operation, tmp_path):
    now = [100]
    memory = SessionMemory(tmp_path, retention_s=10, clock=lambda: now[0])
    expired = memory.new_session()
    memory.write(expired, "old question", "old private history")
    expired_path = memory.store._path(memory._key(expired))
    now[0] = 105
    active = memory.new_session()
    memory.write(active, "active question", "active history")
    memory.store.save("other-purpose", {"keep": True})
    now[0] = 110  # expiry boundary, active session still has five seconds left

    if operation == "restart":
        memory = SessionMemory(tmp_path, retention_s=10, clock=lambda: now[0])
    elif operation == "create":
        memory.new_session()
    elif operation == "read":
        assert "active history" in memory.read(active)
    else:
        memory.write(active, "follow-up", "new answer")

    assert not expired_path.exists()
    assert memory.store.get("other-purpose") == {"keep": True}
    assert "active history" in memory.read(active)
    assert memory.store.get(memory._key(active))["expires_at"] == 115
    with pytest.raises(ValueError, match="expired"):
        memory.read(expired)


def test_bounded_and_redacted(tmp_path):
    memory = SessionMemory(tmp_path, max_chars=350, max_turns=2)
    session = memory.new_session()
    for i in range(8):
        memory.write(session, str(i) + " NIK 1234567890123456", "answer " * 10)
    history = memory.read(session)
    assert "1234567890123456" not in history
    assert len(history) <= 350
    assert history.count("User:") <= 2
    for value in ["web", "../private", "mem-" + "a" * 63]:
        with pytest.raises(ValueError):
            memory.read(value)


def test_http_opt_in_and_delete(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api import v2_routes as routes

    memory = SessionMemory(tmp_path)
    monkeypatch.setattr(routes, "_memory", memory)
    prompts = []

    class Provider:
        name = "fixture"
        def __init__(self, **kwargs):
            pass

        async def generate(self, request):
            prompts.append(request["prompt"])
            return {"content": "Jawaban sesi", "tokens_used": 3}

        async def close(self):
            pass

    class Adapter:
        def __init__(self, **kwargs):
            pass

        async def run(self, *args):
            return {}

    monkeypatch.setattr(routes, "OllamaProvider", Provider)
    monkeypatch.setattr(routes, "HermesV2Adapter", Adapter)
    monkeypatch.setattr(routes._knowledge, "search_knowledge", lambda *args, **kwargs: [])
    with TestClient(app) as client:
        session = client.post("/v2/memory/sessions").json()["session_id"]
        response = client.post("/v2/chat", json={"session_id": session, "user_input": "pertama", "remember": True})
        assert response.status_code == 200
        assert "pertama" in memory.read(session)
        assert client.post("/v2/chat", json={"session_id": session, "user_input": "kedua", "remember": True}).status_code == 200
        assert "pertama" in prompts[-1]
        assert client.post("/v2/chat", json={"session_id": "web", "user_input": "q", "remember": True}).status_code == 422
        assert client.post("/v2/memory/delete", json={"session_id": session}).json()["deleted"]
        assert client.post("/v2/chat", json={"session_id": session, "user_input": "q", "remember": True}).status_code == 422
