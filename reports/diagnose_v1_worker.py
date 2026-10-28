"""Recovery-only diagnostic: retain worker stderr from an actual V1 request."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
original_popen = subprocess.Popen
handles = []
workers = []
stamp = datetime.now(timezone.utc).strftime("%H%M%S%f")


def stop_workers():
    for worker in workers:
        if worker.poll() is None:
            if sys.platform == "win32":
                subprocess.run(["C:/Windows/System32/taskkill.exe", "/PID", str(worker.pid), "/T", "/F"],
                               capture_output=True, timeout=10)
            else:
                worker.terminate()
            worker.wait(timeout=5)
    for handle in handles:
        handle.close()


class DiagnosticPopen(original_popen):
    def __init__(self, args, *positional, **kwargs):
        if isinstance(args, list) and any("indobert_worker.py" in str(a) for a in args):
            prefix = "TEST" if "--tests" in sys.argv else "ROUTE"
            path = ROOT / "reports" / f"V1_RECOVERY_{prefix}_{stamp}_STDERR_{len(handles)}.txt"
            handle = path.open("w", encoding="utf-8")
            handles.append(handle)
            kwargs["stderr"] = handle
        super().__init__(args, *positional, **kwargs)
        if isinstance(args, list) and any("indobert_worker.py" in str(a) for a in args):
            workers.append(self)


subprocess.Popen = DiagnosticPopen
if "--tests" in sys.argv:
    import pytest
    try:
        code = pytest.main(["tests/test_phase4_v1_chat_runtime.py", "tests/test_v1_smoke.py",
                           "-o", "addopts=", "-p", "no:cacheprovider", "-q",
                           f"--basetemp=reports/v1-recovery-worker-{stamp}-tmp",
                           f"--junitxml=reports/V1_RECOVERY_WORKER_{stamp}.xml"])
    finally:
        stop_workers()
    raise SystemExit(code)
from fastapi.testclient import TestClient
from app.main import app
from app.api import routes

with TestClient(app) as client:
    response = client.post("/v1/chat", json={"user_input": "Apa itu KTP-el?", "session_id": "recovery-diag"})
    body = response.json()
    result = {"status": response.status_code, "keys": list(body), "detail": body.get("detail"),
              "error": body.get("error"), "message": body.get("message"),
              "rag_worker": routes._knowledge.rag._embedding_adapter.client.health()}
    (ROOT / "reports" / "V1_RECOVERY_ROUTE_DIAG.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))

routes._knowledge.rag._embedding_adapter.stop()
stop_workers()
