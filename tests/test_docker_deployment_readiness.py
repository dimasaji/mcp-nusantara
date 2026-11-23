import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_healthcheck_checks_http_health() -> None:
    text = _read("scripts/healthcheck.py")
    assert text.strip()
    assert "/health" in text
    assert 'payload.get("status") == "ok"' in text


def test_runtime_requirements_are_pinned() -> None:
    lines = [line.strip() for line in _read("deploy/docker/requirements.txt").splitlines() if line.strip()]
    assert lines
    assert all(re.match(r"^[A-Za-z0-9_.-]+==[^;\s]+(\s*;.*)?$", line) for line in lines)
    assert "haystack-ai==3.4.1" in lines
    assert 'pywin32==312; sys_platform == "win32"' in lines


def test_dockerfile_uses_locked_requirements_and_18201() -> None:
    text = _read("deploy/docker/Dockerfile")
    assert "-r /tmp/requirements.txt" in text
    assert "pip install --no-cache-dir fastapi" not in text
    assert "torch==2.9.1+cpu" in text
    assert "-r /tmp/requirements-indobert.txt" in text
    assert "transformers==4.57.6" in _read("deploy/docker/requirements-indobert.txt")
    assert "EXPOSE 18201" in text
    assert '"--port","18201"' in text


def test_compose_is_v1_sqlite_only_and_loopback() -> None:
    text = _read("deploy/docker/docker-compose.yml").lower()
    assert "postgres" not in text
    assert "redis" not in text
    assert "127.0.0.1:${nusantara_api_port:-18201}:18201" in text
    assert "host.docker.internal:host-gateway" in text
    assert "read_only: true" in text
    assert "tmpfs: [/tmp]" in text


def test_indobert_worker_is_mounted_not_copied() -> None:
    dockerfile = _read("deploy/docker/Dockerfile")
    override = _read("deploy/docker/docker-compose.indobert.yml")
    assert "COPY nusantara-models/indobert_worker.py" not in dockerfile
    assert "NUSANTARA_INDOBERT_WORKER=/opt/indobert-worker/indobert_worker.py" in dockerfile
    assert "/opt/indobert-worker:ro" in override
    assert "NUSANTARA_INDOBERT_WORKER_DIR" in override


def test_docker_context_includes_frontend_dist() -> None:
    text = _read(".dockerignore")
    assert "!frontend/dist/" not in text
    assert not any(line.strip() == "dist" for line in text.splitlines())
