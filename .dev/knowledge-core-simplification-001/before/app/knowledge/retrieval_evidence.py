"""Persistent local storage for effective RAG receipts.

Stores receipt metadata, not the user's raw query or retrieved text.
Each line is independently SHA-256 verifiable.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def receipt_path() -> Path:
    configured = os.environ.get("NUSANTARA_RETRIEVAL_EVIDENCE_PATH")
    if configured:
        return Path(configured).expanduser().resolve()

    # app/knowledge/retrieval_evidence.py -> repository root
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "evidence" / "retrieval-receipts.jsonl"


def persist_retrieval_receipt(snapshot: dict[str, Any]) -> dict[str, str]:
    """Append one receipt record and fsync it before returning."""
    if not isinstance(snapshot, dict):
        raise TypeError("Receipt snapshot must be a dictionary")

    invocation_id = snapshot.get("invocation_id")
    if not isinstance(invocation_id, str) or not invocation_id.strip():
        raise ValueError("Receipt invocation_id is missing")

    record: dict[str, Any] = {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "receipt": snapshot,
    }
    record["record_sha256"] = hashlib.sha256(
        _canonical_json(record).encode("utf-8")
    ).hexdigest()

    path = receipt_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = _canonical_json(record) + "\n"

    # The service is configured for one Uvicorn worker. The lock also
    # prevents concurrent threads in this process from interleaving writes.
    with _LOCK:
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())

    return {
        "path": str(path),
        "record_sha256": record["record_sha256"],
    }


def verify_receipt_record(record: dict[str, Any]) -> bool:
    """Verify the record hash; this does not prove source authenticity."""
    if not isinstance(record, dict):
        return False
    supplied = record.get("record_sha256")
    if not isinstance(supplied, str):
        return False
    payload = {key: value for key, value in record.items()
               if key != "record_sha256"}
    expected = hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()
    return supplied == expected
