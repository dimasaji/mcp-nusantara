"""Phase 11 - feedback: FEEDBACK -> CLASSIFICATION -> VALIDATION -> STORAGE -> ANALYSIS.
Feedback tidak pernah mengubah model/kode; hanya disimpan dengan provenance."""
from __future__ import annotations

import json
import threading
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.observability.context import new_id
from app.observability.logging import redact

# tipe -> (kategori, polaritas, failure_class)
TAXONOMY: dict[str, tuple[str, str, str | None]] = {
    "thumbs_up": ("explicit", "positive", None),
    "thumbs_down": ("explicit", "negative", "UNKNOWN"),
    "correction": ("explicit", "negative", "MODEL_FAILURE"),
    "hallucination_report": ("explicit", "negative", "MODEL_FAILURE"),
    "user_rewrite": ("implicit", "negative", "MODEL_FAILURE"),
    "tool_failure": ("system", "negative", "TOOL_FAILURE"),
    "retrieval_failure": ("system", "negative", "RAG_FAILURE"),
    "policy_violation": ("evaluator", "negative", "POLICY_FAILURE"),
}
_SOURCES = {"explicit": {"user"}, "implicit": {"user", "system"}, "system": {"system"},
            "evaluator": {"evaluator"}}


class FeedbackRejected(ValueError):
    pass


@dataclass
class FeedbackRecord:
    feedback_id: str
    type: str
    category: str
    polarity: str
    failure_class: str | None
    request_id: str
    session_id: str
    comment: str
    provenance: dict[str, Any]
    created_at: str


class FeedbackStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else None
        self._lock = threading.Lock()
        self._items: list[FeedbackRecord] = []
        if self.path and self.path.exists():
            for line in self.path.read_text("utf-8").splitlines():
                try:
                    self._items.append(FeedbackRecord(**json.loads(line)))
                except (ValueError, TypeError):
                    continue

    def submit(self, ftype: str, request_id: str, *, source: str, submitted_by: str,
               comment: str = "", session_id: str = "-") -> FeedbackRecord:
        if ftype not in TAXONOMY:
            raise FeedbackRejected("tipe feedback tidak dikenal")
        category, polarity, fclass = TAXONOMY[ftype]
        if source not in _SOURCES[category]:
            raise FeedbackRejected(f"sumber '{source}' tidak boleh mengirim feedback {category}")
        if not request_id or len(request_id) > 64:
            raise FeedbackRejected("request_id wajib (maks 64 karakter)")
        if len(comment) > 2000:
            raise FeedbackRejected("komentar terlalu panjang")
        with self._lock:
            for x in self._items:  # deduplikasi
                if (x.type, x.request_id, x.provenance.get("submitted_by")) == (ftype, request_id, submitted_by):
                    return x
            rec = FeedbackRecord(new_id("fb"), ftype, category, polarity, fclass, request_id, session_id,
                                 redact(comment), {"source": source, "submitted_by": submitted_by,
                                                   "validated": True},
                                 datetime.now(timezone.utc).isoformat())
            self._items.append(rec)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
            return rec

    def all(self) -> list[FeedbackRecord]:
        with self._lock:
            return list(self._items)

    def summary(self) -> dict[str, Any]:
        items = self.all()
        return {"total": len(items),
                "by_type": dict(Counter(i.type for i in items)),
                "negative_ratio": round(sum(i.polarity == "negative" for i in items) / len(items), 3) if items else None,
                "by_failure_class": dict(Counter(i.failure_class for i in items if i.failure_class))}
