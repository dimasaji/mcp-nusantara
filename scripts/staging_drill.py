"""Manual, isolated staging release/rollback drill using a copy of the real app.

No production port/data/source is replaced. Broken candidate and evidence remain
available for review. Dependency runtime and model runtime are external artifacts.
"""
from __future__ import annotations
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.improvement.release import create_backup, restore_backup


def health(port: int) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{port}/v1/health", timeout=1) as response:
            return json.load(response).get("status") == "ok"
    except Exception:
        return False


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def run() -> dict:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    workspace = ROOT / "audit_reports" / f"staging-drill-{stamp}"
    source = workspace / "release-source"
    source.mkdir(parents=True)
    shutil.copytree(ROOT / "app", source / "app", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(ROOT / "pyproject.toml", source / "pyproject.toml")
    if (ROOT / "config").exists():
        shutil.copytree(ROOT / "config", source / "config")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "NUSANTARA_DATA_DIR": "data",
           "NUSANTARA_KNOWLEDGE_DB": "data/knowledge.db"}
    env.pop("NUSANTARA_ADMIN_TOKEN", None)
    processes = []
    logs = []
    def launch(path, label):
        log = (workspace / f"{label}.log").open("w", encoding="utf-8")
        logs.append(log)
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                                    "--port", str(port), "--no-access-log"], cwd=path, env=env,
                                   stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        processes.append(process)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and process.poll() is None:
            if health(port):
                return process, True
            time.sleep(.2)
        return process, False
    try:
        initial, initial_ok = launch(source, "baseline")
        if not initial_ok:
            raise RuntimeError("baseline staging startup failed")
        stop(initial)  # quiesce data before backup
        archive = create_backup(source, workspace / "backups", "staging")
        # Fault injection applies only to the isolated candidate copy.
        with (source / "app/main.py").open("a", encoding="utf-8") as file:
            file.write('\nraise RuntimeError("isolated staging fault injection")\n')
        broken, broken_ok = launch(source, "broken-candidate")
        stop(broken)
        restored = restore_backup(archive, workspace / "restored") / source.name
        rolled_back, recovered = launch(restored, "rollback")
        result = {"captured_at": stamp, "workspace": str(workspace), "archive": str(archive),
                  "baseline_health": initial_ok, "broken_candidate_rejected": not broken_ok,
                  "rollback_health": recovered, "production_modified": False,
                  "scope": "copied source + quiesced data + local HTTP health; not a production release"}
        result["status"] = "PASS" if initial_ok and not broken_ok and recovered else "FAIL"
        (workspace / "result.json").write_text(json.dumps(result, indent=2), "utf-8")
        print(json.dumps(result, indent=2))
        return result
    finally:
        for process in processes:
            stop(process)
        for log in logs:
            log.close()


if __name__ == "__main__":
    sys.exit(run()["status"] != "PASS")
