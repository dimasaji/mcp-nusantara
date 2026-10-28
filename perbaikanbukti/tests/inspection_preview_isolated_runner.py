"""Scoped validation with external effects blocked before application imports."""
import builtins
import importlib.abc
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
out = root / "docs/reports/normal-inspection-preview-20261008-01a11b73"
sys.path.insert(0, str(root))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
os.environ["PREVIEW_V2_BEFORE"] = str(out / "app__api__v2_routes.py.before")
temporary = out / "temporary"
temporary.mkdir(exist_ok=True)
os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
violations = []


def prohibited(*args, **kwargs):
    violations.append("PROHIBITED_EXTERNAL_EFFECT")
    raise AssertionError("PROHIBITED_EXTERNAL_EFFECT")


sqlite3.connect = prohibited
os.system = prohibited
subprocess.Popen.__init__ = prohibited
original_connect = socket.socket.connect


def socketpair_only(self, address):
    frame = sys._getframe(1)
    listener = frame.f_locals.get("lsock")
    if (frame.f_code is socket._fallback_socketpair.__code__ and listener is not None
            and address == listener.getsockname() and address[0] in ("127.0.0.1", "::1")):
        return original_connect(self, address)
    return prohibited()


socket.socket.connect = socketpair_only
socket.socket.connect_ex = prohibited


def guarded(original):
    def opened(file, mode="r", *args, **kwargs):
        if isinstance(file, (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(file)).resolve()
            if (path.suffix in (".db", ".db-wal", ".db-shm")
                    or path.is_relative_to(root / "data") or path.is_relative_to(root / ".dev")):
                prohibited()
            if any(c in str(mode) for c in "wax+") and not path.is_relative_to(out):
                prohibited()
        return original(file, mode, *args, **kwargs)
    return opened


builtins.open = guarded(builtins.open)
io.open = guarded(io.open)


class ForbiddenOwners(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("app.models", "app.knowledge", "app.language", "app.main",
            "app.security.local_operator", "app.approval.runtime_authorization")):
            prohibited()
        if fullname.startswith("app.api.") and fullname != "app.api.inspection_preview":
            prohibited()


sys.meta_path.insert(0, ForbiddenOwners())
import httpx
httpx.HTTPTransport.handle_request = prohibited
httpx.AsyncHTTPTransport.handle_async_request = prohibited
from app.approval import ApprovalQueue, AuditTrail
for method in ("submit", "consume", "approve"):
    if hasattr(ApprovalQueue, method):
        setattr(ApprovalQueue, method, prohibited)
original_record = AuditTrail.record


def memory_audit_only(self, *args, **kwargs):
    if self.path is not None:
        prohibited()
    return original_record(self, *args, **kwargs)


AuditTrail.record = memory_audit_only
import pytest
paths = [root / "tests/test_inspection_preview_api.py",
         root / "tests/v2/test_devcore_inspection.py", root / "tests/v2/test_devcore.py",
         root / "tests/v2/test_devcore_grounding_response.py"]
os.chdir(out)
result = pytest.main([str(p) for p in paths] + ["-p", "pytest_asyncio.plugin",
    "-o", "log_file=" + str(out / "BACKEND_LOG.txt"),
    "-p", "no:cacheprovider", "--basetemp", str(out / "backend-tmp"),
    "--junitxml", str(out / "BACKEND_RESULTS.xml"), "-q"])
(out / "BACKEND_GUARDS.json").write_text(json.dumps({
    "violations": violations, "pytest_exit": int(result),
    "network": "BLOCKED_EXCEPT_STDLIB_SOCKETPAIR", "real_application_composition": "BLOCKED",
    "provider_knowledge_imports": "BLOCKED", "sqlite": "BLOCKED", "subprocess": "BLOCKED",
    "live_persistence": "BLOCKED", "writes": "EVIDENCE_DIRECTORY_ONLY",
}, indent=2), encoding="utf-8")
raise SystemExit(result if not violations else 1)
