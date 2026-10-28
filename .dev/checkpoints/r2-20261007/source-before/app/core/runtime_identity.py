"""Content identity captured once when the application process imports its code."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def source_build_id(root: Path = ROOT) -> str:
    """Hash executable source/assets, never environment files or runtime data."""
    root = root.resolve()
    files = [p for p in (root / "app").rglob("*")
             if p.is_file() and p.suffix in {".py", ".json", ".html", ".css", ".js"}]
    files += [root / "pyproject.toml", root / "nusantara-models/indobert_worker.py"]
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            path.resolve().relative_to(root)
        except ValueError:
            continue
        name = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()


# Requests always identify the source loaded at process startup, even if files
# are edited later. A new build requires a new process.
BUILD_ID = source_build_id()
