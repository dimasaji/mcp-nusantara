"""NUS-V1-LLAMA-RAG-001 Defect C class — the IndoBERT worker subprocess must not
inherit ambient proxy variables.

Runtime evidence (reports/repro/diag_worker_stderr.py): with ambient
NO_PROXY='...,[::1],::1' the worker dies at import time — huggingface_hub builds
a global httpx client that parses NO_PROXY mounts and raises
httpx.InvalidURL: Invalid port: ':1]'. Every embedding then fails (Stage A
warmup 503). The worker is local/offline with a cached model; proxy env is
never needed, so the spawn environment must strip it (general, not host-specific).
"""
import subprocess

from app.language.semantic.indobert_client import IndoBERTClient


def test_worker_spawn_env_strips_proxy_variables(monkeypatch):
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
                "http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        monkeypatch.setenv(key, "http://proxy.invalid:8080" if key.lower() != "no_proxy"
                           else "localhost,[::1],::1")
    captured = {}

    class FakeProcess:
        stdin = stdout = None

        def poll(self):
            return None

    def fake_popen(args, **kwargs):
        captured["env"] = kwargs.get("env")
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    client = IndoBERTClient()
    client.start()
    env = captured["env"]
    assert env is not None, "spawn must pass an explicit environment"
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
                "http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        assert key not in env, f"proxy variable leaked to worker: {key}"
    assert env.get("PYTHONUTF8") == "1"
    assert env.get("PYTHONIOENCODING") == "utf-8"