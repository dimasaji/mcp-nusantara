"""Run real local audit checks on temporary data, without touching production data.

Usage: python scripts/verify_audit_runtime.py
Requires the application's Python dependencies, cached IndoBERT, and local Ollama.
Docker checks remain NOT_RUN here; this does not certify a container deployment.
"""
from __future__ import annotations

import argparse
import asyncio
import gc
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
QUERY = "Berapa lama verifikasi dokumen audit Nusantara?"
DOCUMENT = "Prosedur Audit Nusantara. Verifikasi dokumen audit Nusantara selesai dalam dua hari kerja."


def restarted_retrieval(db: str) -> None:
    from app.knowledge.rag import RAG
    from app.knowledge.store import SQLiteVectorStore

    rag = RAG(vector_store=SQLiteVectorStore(db))
    try:
        evidence = rag.query(query_text=QUERY, top_k=1).evidence_pack.evidence
        if not evidence or evidence[0].document_id != "audit-runtime-fixture":
            raise RuntimeError("document not retrieved after process restart")
        print(json.dumps({"document_id": evidence[0].document_id, "score": evidence[0].score}))
    finally:
        rag._embedding_adapter.stop()


def verify(output: Path) -> int:
    checks: list[dict] = []
    started = time.perf_counter()

    def check(name: str, fn) -> None:
        start = time.perf_counter()
        try:
            detail = fn()
            checks.append({"name": name, "status": "PASS", "detail": detail,
                           "seconds": round(time.perf_counter() - start, 3)})
        except Exception as exc:
            # Report types, not arbitrary exception text that might contain credentials.
            checks.append({"name": name, "status": "FAIL", "error_type": type(exc).__name__,
                           "seconds": round(time.perf_counter() - start, 3)})
        print(f"{name}: {checks[-1]['status']}", flush=True)

    # These environment overrides apply only to this verification process and its child.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    with tempfile.TemporaryDirectory(prefix="nusantara-audit-") as temporary:
        base = Path(temporary)
        db = base / "knowledge.db"
        os.environ["NUSANTARA_DATA_DIR"] = str(base / "data")
        os.environ["NUSANTARA_KNOWLEDGE_DB"] = str(db)
        os.environ["NUSANTARA_ADMIN_TOKEN"] = secrets.token_urlsafe(32)

        from fastapi.testclient import TestClient
        from app.main import app
        from app.api import routes, v2_routes
        from app.approval import AuditTrail
        from app.core.config import settings
        from app.models.ollama import OllamaProvider

        headers = {"X-Admin-Token": os.environ["NUSANTARA_ADMIN_TOKEN"]}
        try:
            with TestClient(app) as client:
                def authorization():
                    response = client.post("/v1/documents/ingest", json={"title": "audit", "content": DOCUMENT})
                    if response.status_code != 403:
                        raise RuntimeError("unauthorized ingest accepted")
                    response = client.post("/v2/dev", json={"user_input": "List folder ."})
                    if response.status_code != 403:
                        raise RuntimeError("unauthorized developer access accepted")
                    return "Both privileged endpoints returned 403 without credentials"

                check("api_authorization", authorization)

                def ingest():
                    response = client.post("/v1/documents/ingest", headers=headers,
                        json={"id": "audit-runtime-fixture", "title": "Audit fixture", "content": DOCUMENT})
                    if response.status_code != 200 or not response.json().get("success"):
                        raise RuntimeError("real embedding ingest failed")
                    return {"chunks_stored": response.json()["chunks_stored"]}

                check("api_ingest_real_indobert", ingest)

                def search():
                    response = client.post("/v1/knowledge/search", json={"query": QUERY, "top_k": 1})
                    if response.status_code != 200:
                        raise RuntimeError("search HTTP failure")
                    evidence = response.json()["results"]
                    if not evidence or evidence[0]["document_id"] != "audit-runtime-fixture":
                        raise RuntimeError("wrong or missing retrieval evidence")
                    return {"document_id": evidence[0]["document_id"], "score": evidence[0]["score"]}

                check("api_semantic_retrieval", search)

                def restart():
                    process = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                        "--restart-db", str(db)], capture_output=True, text=True, timeout=120)
                    if process.returncode != 0:
                        raise RuntimeError("retrieval after process restart failed")
                    return "Separate Python process retrieved the persisted fixture"

                check("sqlite_process_restart", restart)

                def audit_reload():
                    file = base / "audit-probe.jsonl"
                    trail = AuditTrail(file)
                    trail.record("audit.verification", fixture="temporary")
                    restored = AuditTrail(file)
                    if not restored.verify() or len(restored.entries()) != 1:
                        raise RuntimeError("audit reload invalid")
                    restored.record("audit.restarted", fixture="temporary")
                    if not AuditTrail(file).verify():
                        raise RuntimeError("audit append after reload invalid")
                    return "Hash chain verified before and after reopening and appending"

                check("audit_persistence", audit_reload)

                async def generation():
                    provider = OllamaProvider(base_url=settings.llm_base_url,
                                              model=settings.llm_model, timeout=30)
                    try:
                        health = await provider.health_check()
                        if not health["available"]:
                            raise RuntimeError("configured model unavailable")
                        result = await provider.generate({"prompt": "Jawab hanya satu kata: siap.", "max_tokens": 16})
                        if not result["content"].strip():
                            raise RuntimeError("empty real model response")
                        return {"model": result["model"], "tokens_used": result["tokens_used"]}
                    finally:
                        await provider.close()

                check("ollama_real_generation", lambda: asyncio.run(generation()))
        finally:
            for module in (routes, v2_routes):
                adapter = module._knowledge.rag._embedding_adapter
                if adapter:
                    adapter.stop()
                semantic = getattr(module._language, "semantic_intent_engine", None)
                if semantic and getattr(semantic, "client", None):
                    semantic.client.stop()
            gc.collect()

    checks.append({"name": "docker_build_health_persistence", "status": "NOT_RUN",
                   "detail": "Docker deployment still requires build and container tests",
                   "docker_cli_found": bool(shutil.which("docker"))})
    status = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "CONDITIONAL"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"status": status, "seconds": round(time.perf_counter() - started, 3),
                                 "checks": checks}, indent=2), encoding="utf-8")
    print(f"Readiness: {status}; report: {output}", flush=True)
    return 1 if status == "FAIL" else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--restart-db")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "audit_reports" / "AUDIT_RUNTIME_READINESS_2026-10-05.json")
    args = parser.parse_args()
    if args.restart_db:
        restarted_retrieval(args.restart_db)
    else:
        raise SystemExit(verify(args.output))
