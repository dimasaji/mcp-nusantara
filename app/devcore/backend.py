"""Adapter agar Developer Core memakai ToolRegistry LIVE (app.tools.registry) tanpa mengubahnya.

PENTING: bentuk hasil registry live belum dibaca. `normalize_result` menangani beberapa bentuk yang masuk akal
(dict datar, dict dibungkus {success, tool_name, result}, objek pydantic, str/list). Verifikasi terhadap
registry.py asli sebelum dipercaya; nama argumen tool bisa diubah lewat `arg_names`.
"""
from __future__ import annotations

from typing import Any


def normalize_result(name: str, raw: Any) -> dict[str, Any]:
    if hasattr(raw, "model_dump"):
        d = raw.model_dump()
    elif isinstance(raw, dict):
        d = dict(raw)
    else:
        d = {k: getattr(raw, k) for k in ("success", "tool_name", "result", "error") if hasattr(raw, k)}
    inner = d.get("result")
    if isinstance(inner, dict):
        out = dict(inner)
        out["success"] = bool(d.get("success", True)) and bool(inner.get("success", True))
        out["error"] = inner.get("error") or d.get("error")
    else:
        out = {k: v for k, v in d.items() if k not in ("result", "tool_name")}
        out["success"] = bool(d.get("success", True))
        if isinstance(inner, str) and name == "read_file":
            out["content"] = inner
        elif isinstance(inner, list) and name == "find_file":
            out["matches"] = [str(x) for x in inner]
        elif isinstance(inner, list) and name == "list_directory":
            out["entries"] = [x if isinstance(x, dict) else
                              {"name": str(x).rstrip("/"), "type": "dir" if str(x).endswith("/") else "file"} for x in inner]
    out["tool"] = name
    out.setdefault("error", None)
    return out


class RegistryBackend:
    def __init__(self, registry: Any, arg_names: dict[str, dict[str, str]] | None = None):
        self.registry = registry
        self.arg_names: dict[str, dict[str, str]] = {"read_file": {"path": "path"}, "find_file": {"name": "name"},
                                                     "list_directory": {"path": "path"}}
        for k, v in (arg_names or {}).items():
            self.arg_names.setdefault(k, {}).update(v)

    def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        mapped = {self.arg_names.get(name, {}).get(k, k): v for k, v in args.items()}
        try:
            raw = self.registry.execute(name, mapped)
        except Exception as exc:  # noqa: BLE001 - kegagalan tool => hasil terstruktur, bukan crash
            return {"success": False, "tool": name, "error": f"{type(exc).__name__}: {exc}"[:300]}
        return normalize_result(name, raw)
