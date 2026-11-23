"""Structured JSON logging dengan redaksi secret/data sensitif."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from app.observability.context import current_ids

_SENSITIVE_KEYS = re.compile(r"(pass(word)?|secret|token|api[_-]?key|authorization|cookie|nik|ktp)", re.I)
_PATTERNS = [
    (re.compile(r"(?i)bearer\s+[a-z0-9._\-]+"), "Bearer [REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}"), "[REDACTED_KEY]"),
    (re.compile(r"\b\d{16}\b"), "[REDACTED_ID]"),
]


def redact(value: Any, _depth: int = 0) -> Any:
    if _depth > 6:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if _SENSITIVE_KEYS.search(str(k)) else redact(v, _depth + 1))
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, _depth + 1) for v in value]
    if isinstance(value, str):
        for pat, rep in _PATTERNS:
            value = pat.sub(rep, value)
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": redact(record.getMessage()),
            **current_ids(),
        }
        extra = getattr(record, "fields", None)
        if extra:
            payload["fields"] = redact(extra)
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger("nusantara")
    root.setLevel(level.upper())
    if not any(isinstance(h.formatter, JsonFormatter) for h in root.handlers):
        h = logging.StreamHandler()
        h.setFormatter(JsonFormatter())
        root.addHandler(h)
    root.propagate = False


def log_event(event: str, **fields: Any) -> None:
    logging.getLogger("nusantara").info(event, extra={"fields": fields})
