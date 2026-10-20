"""Run an isolated local V1 candidate, verify identity/API, stop its process tree."""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.core.runtime_identity import source_build_id


def main() -> int:
    root = ROOT / "reports/v1-recovery-candidate"
    root.mkdir(exist_ok=True)
    db = root / "knowledge.db"
    with closing(sqlite3.connect((ROOT / "data/knowledge/nusantara_knowledge.db").as_uri() + "?mode=ro", uri=True)) as source:
        with closing(sqlite3.connect(db)) as destination:
            source.backup(destination)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    expected = source_build_id()
    env = {**os.environ, "NUSANTARA_DATA_DIR": str(root), "NUSANTARA_KNOWLEDGE_DB": str(db)}
    records = []
    log_path = root / "server.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
                                   cwd=ROOT, env=env, stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        def request(path, payload=None):
            body = json.dumps(payload).encode() if payload is not None else None
            req = Request(base + path, data=body, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=90) as response:
                return response.status, json.loads(response.read(2_000_000))
        try:
            for _ in range(40):
                try:
                    status, health = request("/v1/health")
                    break
                except Exception:
                    if process.poll() is not None:
                        raise RuntimeError("candidate exited before startup")
                    time.sleep(.25)
            else:
                raise RuntimeError("candidate startup timeout")
            assert status == 200 and health["build_id"] == expected
            records.append({"check": "startup_health_identity", "status": "PASS", "build_id": health["build_id"]})
            status, search = request("/v1/knowledge/search", {"query": "Apa itu paspor?", "top_k": 1})
            assert status == 200 and search["results"][0]["document_id"] == "BENCH-PASPOR-001"
            records.append({"check": "knowledge", "status": "PASS", "document_id": "BENCH-PASPOR-001"})
            status, chat = request("/v1/chat", {"session_id": "recovery-candidate", "user_input": "Apa itu KTP-el?"})
            trust = chat["trust"]
            assert status == 200 and isinstance(trust["requires_human"], bool) and 0 <= trust["confidence"] <= 1
            records.append({"check": "chat_trust", "status": "PASS", "trust": trust,
                            "grounding": chat.get("grounding"), "answer": chat.get("response")})
        except Exception as exc:
            records.append({"check": "candidate", "status": "FAIL", "error_type": type(exc).__name__, "detail": str(exc)})
        finally:
            if process.poll() is None:
                if os.name == "nt":
                    subprocess.run(["C:/Windows/System32/taskkill.exe", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=15)
                else:
                    process.terminate()
                process.wait(timeout=10)
    result = {"mode": "isolated_native_local_candidate", "base_url": base, "expected_build_id": expected,
              "server_pid": process.pid, "server_stopped": process.poll() is not None,
              "records": records, "production_deployment": "NOT_RUN", "container_deployment": "NOT_RUN",
              "limitations": "Local candidate execution; no production target or container build inferred"}
    result["status"] = "FAIL" if any(r["status"] == "FAIL" for r in records) else "PASS_LOCAL"
    (ROOT / "reports/V1_RECOVERY_RUNTIME.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return int(result["status"] == "FAIL")


if __name__ == "__main__":
    raise SystemExit(main())
