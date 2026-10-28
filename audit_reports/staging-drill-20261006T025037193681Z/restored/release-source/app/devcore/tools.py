"""Tool read-only Developer Core: read_file, find_file, list_directory.
Hasil selalu terstruktur {success, tool, ..., error}; kegagalan yang diharapkan TIDAK melempar exception."""
from __future__ import annotations

import fnmatch
import os
from typing import Any

from app.devcore.workspace import SKIP_DIRS, PathBlocked, Workspace, is_sensitive_name
from app.governance.tools import GovernedToolRegistry, Risk, ToolClass, ToolSpec

MAX_MATCHES, MAX_ENTRIES, MAX_SCAN = 20, 200, 20000


def _fail(tool: str, error: str, **extra: Any) -> dict[str, Any]:
    return {"success": False, "tool": tool, "error": error, **extra}


def read_file(ws: Workspace, args: dict[str, Any]) -> dict[str, Any]:
    try:
        p = ws.resolve(args["path"])
    except PathBlocked as exc:
        return _fail("read_file", f"DIBLOKIR: {exc}", path=str(args.get("path")))
    rel = ws.rel(p)
    if not p.is_file():
        return _fail("read_file", "file tidak ditemukan", path=rel)
    try:
        with p.open("rb") as f:
            data = f.read(ws.max_read_bytes + 1)
        size = p.stat().st_size
    except OSError as exc:
        return _fail("read_file", f"gagal membaca: {type(exc).__name__}", path=rel)
    if b"\x00" in data[:8000]:
        return _fail("read_file", "file biner tidak didukung", path=rel)
    truncated = len(data) > ws.max_read_bytes
    text = data[: ws.max_read_bytes].decode("utf-8", errors="replace")
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    return {"success": True, "tool": "read_file", "path": rel, "content": text, "error": None,
            "truncated": truncated, "size_bytes": size, "lines": lines}


def find_file(ws: Workspace, args: dict[str, Any]) -> dict[str, Any]:
    q = str(args["name"]).strip().replace("\\", "/").lower()
    if not q or ".." in q.split("/"):
        return _fail("find_file", "query tidak valid", query=q)
    matches: list[str] = []
    scanned, truncated = 0, False
    for dirpath, dirs, files in os.walk(ws.root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (dirpath == str(ws.root) and d == "data"))
        for name in sorted(files):
            scanned += 1
            if scanned > MAX_SCAN:
                truncated = True
                break
            if is_sensitive_name(name):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), ws.root).replace(os.sep, "/")
            if (fnmatch.fnmatch(name.lower(), q) if "/" not in q else rel.lower().endswith(q)):
                matches.append(rel)
                if len(matches) >= MAX_MATCHES:
                    truncated = True
                    break
        if truncated:
            break
    return {"success": True, "tool": "find_file", "query": q, "matches": matches, "truncated": truncated, "error": None}


def list_directory(ws: Workspace, args: dict[str, Any]) -> dict[str, Any]:
    try:
        p = ws.resolve(args.get("path") or ".")
    except PathBlocked as exc:
        return _fail("list_directory", f"DIBLOKIR: {exc}", path=str(args.get("path")))
    if not p.is_dir():
        return _fail("list_directory", "direktori tidak ditemukan", path=ws.rel(p) if p.is_relative_to(ws.root) else "?")
    entries = []
    for child in sorted(p.iterdir(), key=lambda c: (not c.is_dir(), c.name.lower())):
        if child.name in SKIP_DIRS or is_sensitive_name(child.name) or (p == ws.root and child.name == "data"):
            continue
        entries.append({"name": child.name, "type": "dir" if child.is_dir() else "file"})
    return {"success": True, "tool": "list_directory", "path": ws.rel(p), "entries": entries[:MAX_ENTRIES],
            "truncated": len(entries) > MAX_ENTRIES, "error": None}


def register_dev_tools(registry: GovernedToolRegistry, ws: Workspace) -> None:
    out = {"type": "object", "required": ["success", "tool"], "properties": {"success": {"type": "boolean"}}}

    def spec(name: str, desc: str, schema: dict[str, Any]) -> ToolSpec:
        return ToolSpec(name, desc, schema, out, ToolClass.READ, Risk.LOW, timeout_s=10.0)

    registry.register(spec("read_file", "Baca isi file di workspace (read-only)",
                           {"type": "object", "required": ["path"], "properties": {"path": {"type": "string"}}}),
                      lambda a: read_file(ws, a))
    registry.register(spec("find_file", "Cari file berdasarkan nama/glob di workspace",
                           {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}),
                      lambda a: find_file(ws, a))
    registry.register(spec("list_directory", "Daftar isi direktori di workspace",
                           {"type": "object", "properties": {"path": {"type": "string"}}}),
                      lambda a: list_directory(ws, a))
