"""Security gate (workflow #24): path harus di dalam workspace, bukan file sensitif, bukan direktori terlarang."""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path

SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache",
             ".ruff_cache", ".pytest_cache"}
_SENSITIVE = ("*.pem", "*.key", "*.pfx", "*.p12", "id_rsa*", "id_ed25519*", "credentials*", "secrets*", ".netrc")


class PathBlocked(PermissionError):
    pass


def is_sensitive_name(name: str) -> bool:
    n = name.lower()
    if n == ".env" or (n.startswith(".env.") and n != ".env.example"):
        return True
    return any(fnmatch.fnmatch(n, p) for p in _SENSITIVE)


class Workspace:
    def __init__(self, root: str | Path, max_read_bytes: int = 200_000):
        self.root = Path(root).resolve()
        self.max_read_bytes = max_read_bytes

    def resolve(self, ref: str) -> Path:
        if not isinstance(ref, str) or not ref.strip() or "\x00" in ref:
            raise PathBlocked("path tidak valid")
        raw = ref.strip().replace("\\", "/")
        if raw.startswith("~"):
            raise PathBlocked("path home tidak diizinkan")
        p = Path(raw)
        if not p.is_absolute() and re.match(r"^[A-Za-z]:/", raw):
            raise PathBlocked("path drive absolut di luar workspace")
        target = (p if p.is_absolute() else self.root / p).resolve()  # resolve() mengikuti symlink
        if not target.is_relative_to(self.root):
            raise PathBlocked("path di luar workspace")
        rel = target.relative_to(self.root)
        if rel.parts and rel.parts[0] == "data":
            raise PathBlocked("direktori data/ diblokir (berisi audit/memory)")
        if any(part in SKIP_DIRS or is_sensitive_name(part) for part in rel.parts):
            raise PathBlocked("path diblokir oleh kebijakan keamanan")
        return target

    def rel(self, p: Path) -> str:
        return p.relative_to(self.root).as_posix() or "."
