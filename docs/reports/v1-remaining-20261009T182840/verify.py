"""Scoped WEIP verification: real network/models and active DB access blocked."""
import asyncio
import builtins
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
MODE = sys.argv[1]
run = OUT / (MODE + "-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
run.mkdir(exist_ok=False)
temporary = run / "temporary"
tempfile.tempdir = str(run)
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
violations = []
def prohibited(*args, **kwargs):
    violations.append("EXTERNAL_EFFECT_BLOCKED")
    raise AssertionError("EXTERNAL_EFFECT_BLOCKED")
original_connect = sqlite3.connect
def temporary_sqlite(database, *args, **kwargs):
    if not isinstance(database, (str, os.PathLike)) or not Path(database).resolve().is_relative_to(temporary):
        return prohibited()
    return original_connect(database, *args, **kwargs)
sqlite3.connect = temporary_sqlite
subprocess.Popen.__init__ = prohibited
os.system = prohibited
original_socket = socket.socket.connect
def socketpair_only(self, address):
    frame = sys._getframe(1)
    listener = frame.f_locals.get("lsock")
    if (frame.f_code is socket._fallback_socketpair.__code__ and listener is not None
        and address == listener.getsockname() and address[0] in ("127.0.0.1", "::1")):
        return original_socket(self, address)
    return prohibited()
socket.socket.connect = socketpair_only
socket.socket.connect_ex = prohibited
def guarded(original):
    def opened(file, mode="r", *args, **kwargs):
        if isinstance(file, (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(file)).resolve()
            approved_fixture = ROOT / "data/knowledge/official_sources/ktp_el"
            fixture_files = {approved_fixture / "manifest.json"} | {approved_fixture / f"tng-ktpel-{i:03d}.md" for i in range(1,5)}
            readonly_fixture = p in fixture_files and not any(c in str(mode) for c in "wax+")
            if (p.is_relative_to(ROOT / "data") and not readonly_fixture) or (p.name == ".env" and not p.is_relative_to(temporary)):
                return prohibited()
            if any(c in str(mode) for c in "wax+") and not p.is_relative_to(run):
                return prohibited()
        return original(file, mode, *args, **kwargs)
    return opened
builtins.open = guarded(builtins.open)
io.open = guarded(io.open)
import pytest
paths = ["tests/test_web_evidence_pipeline.py"]
paths += ["tests/test_weip_rag_adapter.py"]
if MODE == "regression":
    paths += ["tests/test_source_fetcher.py", "tests/test_effective_rag_profile.py", "tests/test_configuration_contract.py"]
selection = "not actual_v2 and not dev_endpoint and not consumers_correlation and not empty_result and not bootstrap_layers and not owner_reads"
if MODE == "targeted":
    selection = "remaining_"
result = pytest.main([str(ROOT / p) for p in paths] + ["-q", "-p", "pytest_asyncio.plugin", "-p", "no:cacheprovider",
    "-k", selection, "-o", "log_file=" + str(run / "log.txt"),
    "--basetemp", str(temporary), "--junitxml", str(run / "results.xml")])
(run / "guards.json").write_text(json.dumps({"pytest_exit": int(result), "violations": violations,
    "network": "BLOCKED_EXCEPT_STDLIB_SOCKETPAIR", "sqlite": "TEMPORARY_TEST_DATABASES_ONLY",
    "subprocess": "BLOCKED", "writes": "NEW_RUN_DIRECTORY_ONLY", "selection": selection}, indent=2))
print("EVIDENCE_RUN=" + str(run))
raise SystemExit(result if not violations else 1)
