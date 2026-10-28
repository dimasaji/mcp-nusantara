"""Input/output validation (stdlib only). Tidak mengubah kontrak V1."""
from __future__ import annotations

import re
from typing import Any

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TYPES = {
    "string": str, "integer": int, "number": (int, float), "boolean": bool,
    "object": dict, "array": list, "null": type(None),
}


class InputRejected(ValueError):
    """Input ditolak validator (bukan bug sistem)."""


def sanitize_text(text: Any, *, max_len: int = 20000) -> str:
    """Bersihkan karakter kontrol, tolak kosong/terlalu panjang/bukan string."""
    if not isinstance(text, str):
        raise InputRejected("input harus berupa teks")
    cleaned = _CONTROL.sub("", text).strip()
    if not cleaned:
        raise InputRejected("input kosong")
    if len(cleaned) > max_len:
        raise InputRejected(f"input melebihi {max_len} karakter")
    return cleaned


def validate_output(text: Any, *, max_len: int = 50000) -> str:
    """Pastikan output model berupa teks tidak kosong dan dalam batas ukuran."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("output model kosong atau bukan teks")
    return text[:max_len]


def validate_schema(data: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validasi subset JSON-Schema (type, required, properties, items, enum)."""
    errors: list[str] = []
    expected = schema.get("type")
    if expected:
        py = _TYPES.get(expected)
        ok = py is not None and isinstance(data, py)
        if expected in ("integer", "number") and isinstance(data, bool):
            ok = False
        if not ok:
            return [f"{path}: harus bertipe {expected}"]
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{path}: nilai tidak diizinkan")
    if isinstance(data, dict):
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"{path}.{key}: wajib ada")
        for key, sub in schema.get("properties", {}).items():
            if key in data:
                errors.extend(validate_schema(data[key], sub, f"{path}.{key}"))
    if isinstance(data, list) and "items" in schema:
        for i, item in enumerate(data):
            errors.extend(validate_schema(item, schema["items"], f"{path}[{i}]"))
    return errors
