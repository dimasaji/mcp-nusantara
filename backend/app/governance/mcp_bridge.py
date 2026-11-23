"""Phase 8 - MCP: discovery + validasi manifest tool eksternal sebelum masuk registry governed.

Fail-closed: kelas/risiko tidak dikenal => EXTERNAL/HIGH (butuh approval). Tool tanpa handler,
skema, atau nama valid ditolak. Model tidak pernah melihat tool yang belum lolos validasi.
"""
from __future__ import annotations

import ast
import operator
import re
from datetime import datetime, timezone
from typing import Any, Callable

from app.governance.tools import GovernedToolRegistry, Risk, ToolClass, ToolSpec

_NAME = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_OBJ = {"type": "object"}


def register_manifest(registry: GovernedToolRegistry, manifest: list[dict[str, Any]],
                      handlers: dict[str, Callable[[dict[str, Any]], Any]]) -> dict[str, str]:
    """Return {tool_name: alasan_ditolak}. Tool valid didaftarkan; sisanya dilewati."""
    rejected: dict[str, str] = {}
    for i, t in enumerate(manifest):
        name = str(t.get("tool_name", f"#{i}"))
        try:
            if not _NAME.match(name):
                raise ValueError("nama tool tidak valid")
            if not t.get("description") or not isinstance(t.get("input_schema"), dict):
                raise ValueError("description/input_schema wajib")
            if name not in handlers:
                raise ValueError("handler tidak tersedia")
            try:
                cls = ToolClass(t.get("tool_class"))
            except ValueError:
                cls = ToolClass.EXTERNAL
            try:
                risk = Risk(t.get("risk"))
            except ValueError:
                risk = Risk.HIGH
            timeout = float(t.get("timeout_s", 10.0))
            if not 0 < timeout <= 120:
                raise ValueError("timeout_s harus 0..120")
            registry.register(ToolSpec(name, str(t["description"])[:500], t["input_schema"],
                                       t.get("output_schema") or _OBJ, cls, risk,
                                       str(t.get("permission", "")), timeout,
                                       bool(t.get("audit_required", True))), handlers[name])
        except (ValueError, TypeError) as exc:
            rejected[name] = str(exc)
    return rejected


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Mod: operator.mod, ast.USub: operator.neg}


def safe_calc(expr: str) -> float:
    """Kalkulator aritmetika via AST (tanpa eval/pangkat) - bukan eksekusi kode arbitrer."""
    if len(expr) > 200:
        raise ValueError("ekspresi terlalu panjang")

    def ev(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("ekspresi tidak diizinkan")
    return ev(ast.parse(expr, mode="eval"))


def register_builtin_tools(registry: GovernedToolRegistry) -> None:
    registry.register(
        ToolSpec("calculator", "Hitung ekspresi aritmetika sederhana",
                 {"type": "object", "required": ["expression"], "properties": {"expression": {"type": "string"}}},
                 {"type": "object", "required": ["result"]}, ToolClass.READ, Risk.LOW, timeout_s=2.0),
        lambda a: {"result": safe_calc(a["expression"])})
    registry.register(
        ToolSpec("current_time_utc", "Waktu UTC saat ini", _OBJ,
                 {"type": "object", "required": ["iso"]}, ToolClass.READ, Risk.LOW, timeout_s=1.0),
        lambda a: {"iso": datetime.now(timezone.utc).isoformat()})
