"""Container audit probe. Stream this script to docker exec -i ... python - [initial|restart]."""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PHASE = sys.argv[1] if len(sys.argv) > 1 else "initial"
BASE = "http://127.0.0.1:8000"
DOCUMENT_ID = "docker-audit-fixture-20261005"
QUERY = "Berapa lama verifikasi dokumen audit Nusantara?"
CONTENT = "Prosedur Audit Nusantara. Verifikasi dokumen audit Nusantara selesai dalam dua hari kerja."
checks = []


def request(path, body=None, admin=False, base=BASE, timeout=300):
    headers = {"Content-Type": "application/json"}
    if admin:
        headers["X-Admin-Token"] = os.environ["NUSANTARA_ADMIN_TOKEN"]
    req = urllib.request.Request(base + path,
        data=json.dumps(body).encode() if body is not None else None, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def check(name, fn):
    started = time.perf_counter()
    try:
        detail = fn()
        checks.append({"name": name, "status": "PASS", "detail": detail})
    except Exception as exc:
        checks.append({"name": name, "status": "FAIL", "error_type": type(exc).__name__,
                       "detail": str(exc)[:300]})
    checks[-1]["seconds"] = round(time.perf_counter() - started, 3)
    print(json.dumps(checks[-1]), flush=True)


def health():
    status, data = request("/health")
    assert status == 200 and data["status"] == "ok"
    return "API responds from inside Linux container"


def auth():
    for path, payload in (("/v1/documents/ingest", {"title": "audit", "content": CONTENT}),
                          ("/v2/dev", {"user_input": "List folder app"})):
        status, _ = request(path, payload)
        assert status == 403, f"{path}: expected 403, got {status}"
    return "Anonymous privileged requests rejected"


def ingest():
    status, data = request("/v1/documents/ingest",
        {"id": DOCUMENT_ID, "title": "Docker audit fixture", "content": CONTENT}, admin=True)
    assert status == 200 and data.get("success"), f"ingest {status}: {data.get('detail', 'failed')}"
    assert data["chunks_stored"] > 0
    return {"chunks_stored": data["chunks_stored"]}


def search():
    status, data = request("/v1/knowledge/search", {"query": QUERY, "top_k": 1})
    assert status == 200, f"search {status}: {data.get('detail', 'failed')}"
    results = data["results"]
    assert results and results[0]["document_id"] == DOCUMENT_ID
    return {"document_id": results[0]["document_id"], "score": results[0]["score"]}


def responsive_ingest():
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(ingest)
        time.sleep(0.3)
        started = time.perf_counter()
        status, data = request("/health", timeout=3)
        assert status == 200 and data["status"] == "ok"
        latency = round(time.perf_counter() - started, 3)
        result = future.result(timeout=300)
        return {**result, "health_during_ingest_seconds": latency}


def audit():
    if PHASE == "initial":
        status, data = request("/v2/dev", {"user_input": "List folder app"}, admin=True)
        assert status == 200 and data["tool"]["used"]
    status, data = request("/v2/audit/verify", admin=True)
    assert status == 200 and data["valid"] and data["entries"] > 0
    return {"entries": data["entries"], "hash_chain_valid": data["valid"]}


def generation():
    status, data = request("/api/generate", {"model": os.getenv("LLM_MODEL", "llama3.2:1b"),
        "prompt": "Jawab satu kata: siap.", "stream": False, "options": {"num_predict": 16}},
        base=os.environ["LLM_BASE_URL"])
    assert status == 200 and data["response"].strip()
    return {"model": data["model"], "tokens": data.get("eval_count")}


def symlink_security():
    import tempfile
    from pathlib import Path
    from app.devcore.workspace import Workspace, PathBlocked

    with tempfile.TemporaryDirectory() as inside, tempfile.TemporaryDirectory() as outside:
        target = Path(outside) / "private.txt"
        target.write_text("audit fixture", encoding="utf-8")
        (Path(inside) / "link.txt").symlink_to(target)
        try:
            Workspace(inside).resolve("link.txt")
        except PathBlocked:
            return "Real Linux symlink outside workspace rejected"
        raise AssertionError("symlink escaped workspace")


check("container_http_health", health)
check("container_authorization", auth)
if PHASE == "initial":
    check("container_ingest_real_indobert", responsive_ingest)
check("container_retrieval" if PHASE == "initial" else "retrieval_after_container_restart", search)
check("container_audit" if PHASE == "initial" else "audit_after_container_restart", audit)
if PHASE == "initial":
    check("container_to_host_ollama", generation)
    check("linux_symlink_boundary", symlink_security)
status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
print(json.dumps({"phase": PHASE, "status": status, "checks": checks}), flush=True)
raise SystemExit(0 if status == "PASS" else 1)
