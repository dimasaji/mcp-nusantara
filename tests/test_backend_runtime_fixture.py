"""Real backend subprocess/HTTP/SQLite with synthetic model and embedding I/O."""

import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

import httpx


def test_backend_process_ingestion_retrieval_chat_and_history(tmp_path):
    observed = []

    class Model(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, payload):
            raw = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            self.reply({"models": [{"name": "fixture-local"}]})

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            observed.append((self.path, payload))
            self.reply({"model": "fixture-local", "done": True,
                        "response": "Persyaratan layanan fixture adalah Surat Permohonan.",
                        "eval_count": 8, "prompt_eval_count": 10})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Model)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    bootstrap = tmp_path / "runtime_app.py"
    bootstrap.write_text(
        "from app.core.config import settings\n"
        "settings.compose_configuration(project_root=" + repr(str(tmp_path)) + ","
        "dotenv_environment={},environment={},overrides=" + repr({
            "llm": {"model": "fixture-local", "base_url": f"http://127.0.0.1:{server.server_port}"},
            "knowledge": {"root": str(tmp_path / "knowledge"),
                          "database": str(tmp_path / "knowledge/fixture.db")}}) + ")\n"
        "from app.language.semantic.indobert_client import IndoBERTClient\n"
        "IndoBERTClient.encode=lambda self,text:{'ok':True,'embedding':[1.0]+[0.0]*767}\n"
        "from app.main import app\n"
        "from app.api import routes\n"
        "routes._language.semantic_intent_engine=None\n"
        "import uvicorn\n"
        f"uvicorn.run(app,host='127.0.0.1',port={port},log_level='warning',access_log=False)\n",
        encoding="utf-8")
    environment = dict(os.environ, NUSANTARA_ADMIN_TOKEN="runtime-fixture-token")
    process = None
    try:
        with (tmp_path / "runtime.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen([sys.executable, "-B", str(bootstrap)], env=environment,
                                       stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False, timeout=15) as client:
                deadline = time.monotonic() + 20
                while True:
                    try:
                        if client.get("/v1/health").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    assert process.poll() is None, (tmp_path / "runtime.log").read_text()
                    assert time.monotonic() < deadline, "fixture runtime did not start"
                    time.sleep(.05)
                token = {"X-Admin-Token": "runtime-fixture-token"}
                body = {"id": "runtime-source", "title": "Layanan fixture",
                        "content": "Persyaratan layanan fixture adalah Surat Permohonan. " * 8}
                assert client.post("/v1/documents/ingest", json=body).status_code == 403
                first = client.post("/v1/documents/ingest", json=body, headers=token)
                assert first.status_code == 200, first.text
                assert first.json()["success"]
                repeat = client.post("/v1/documents/ingest", json=body, headers=token)
                assert repeat.status_code == 200 and repeat.json()["success"]
                assert client.post("/v1/knowledge/search", json={"query": "Surat Permohonan"}).status_code == 403
                search = client.post("/v1/knowledge/search", json={"query": "Surat Permohonan"}, headers=token)
                assert search.status_code == 200, search.text
                assert search.json()["results"]
                session = "web-" + str(uuid4())
                answer = client.post("/v1/chat", json={"session_id": session,
                    "user_input": "Apa persyaratan layanan fixture?"}, headers=token)
                assert answer.status_code == 200, answer.text
                data = answer.json()
                assert data["session_id"] == session
                assert data["grounding"]["grounded"] is True
                assert data["evidence"]
                assert all(item["chunk"] == "" for item in data["evidence"])
                history = client.get("/v1/chat/history", headers={**token, "X-Chat-Session": session})
                assert history.status_code == 200 and len(history.json()["turns"]) == 1
                public = client.get("/v1/chat/history", headers={"X-Chat-Session": session})
                assert public.status_code == 200 and public.json()["turns"] == []
                # Actual Ollama HTTP dispatch must occur, not merely application boot.
                assert any(path == "/api/generate" and payload.get("model") == "fixture-local"
                           and payload.get("prompt") for path, payload in observed), (
                               "real Ollama generation transport was not exercised")
                smoke = subprocess.run([
                    sys.executable, "-B", "-m", "pytest",
                    "-p", "no:cacheprovider", "-o", "addopts=",
                    "-p", "no:asyncio", "-q",
                    "--log-file", str(tmp_path / "live-smoke.log"),
                    "--junitxml", str(tmp_path / "live-smoke.xml"),
                    "tests/test_v1_live_smoke.py"],
                    env={**environment, "NUSANTARA_BASE_URL": f"http://127.0.0.1:{port}",
                         "NUSANTARA_TEST_ADMIN_TOKEN": "runtime-fixture-token"},
                    capture_output=True, text=True, timeout=30)
                assert smoke.returncode == 0, smoke.stdout + smoke.stderr
    finally:
        if process is not None:
            process.terminate()
            process.wait(timeout=10)
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
