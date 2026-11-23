"""Phase 15 - knowledge discovery: GAP -> validasi sumber -> ekstraksi -> provenance -> KANDIDAT.
Kandidat tidak pernah masuk production sebelum approval manusia (promote() mengonsumsi approval)."""
from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import asdict
from pathlib import Path
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.approval.queue import ApprovalQueue, ApprovalRequest
from app.observability.context import new_id
from app.rag.store import DocMeta, VersionedKnowledgeStore


class SourceRejected(ValueError):
    pass


class NotApproved(PermissionError):
    pass


class SourceValidator:
    def __init__(self, allowed_hosts: set[str] | None = None, allow_internal: bool = True):
        self.allowed_hosts = {h.lower() for h in (allowed_hosts or set())}
        self.allow_internal = allow_internal

    def validate(self, uri: str) -> tuple[bool, str]:
        u = urlparse(uri)
        if u.scheme == "internal":
            return (self.allow_internal, "internal" if self.allow_internal else "internal tidak diizinkan")
        if u.scheme != "https":
            return False, "hanya https/internal"
        host = (u.hostname or "").lower()
        if any(host == h or host.endswith("." + h) for h in self.allowed_hosts):
            return True, "host di allowlist"
        return False, "host tidak di allowlist"


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))).strip()


@dataclass
class KnowledgeCandidate:
    candidate_id: str
    gap_id: str
    title: str
    topic: str
    uri: str
    content: str
    provenance: dict
    status: str = "candidate"


class CandidateStore:
    def __init__(self, validator: SourceValidator, path: Path | None = None):
        self.validator = validator
        self._items: dict[str, KnowledgeCandidate] = {}
        self.path = path
        self._lock = threading.RLock()
        if path and path.exists():
            for raw in json.loads(path.read_text("utf-8")):
                candidate = KnowledgeCandidate(**raw)
                if hashlib.sha256(candidate.content.encode()).hexdigest() != candidate.provenance["sha256"]:
                    raise SourceRejected("candidate integrity failure")
                self._items[candidate.candidate_id] = candidate

    def _save(self) -> None:
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(".tmp")
            temp.write_text(json.dumps([asdict(c) for c in self._items.values()], ensure_ascii=False), "utf-8")
            temp.replace(self.path)

    def propose(self, gap_id: str, uri: str, raw_content: str, *, title: str, topic: str,
                provided_by: str) -> KnowledgeCandidate:
        ok, why = self.validator.validate(uri)
        if not ok:
            raise SourceRejected(why)
        text = html_to_text(raw_content)[:100_000]
        if len(text) < 20:
            raise SourceRejected("konten terlalu pendek")
        digest = hashlib.sha256(text.encode()).hexdigest()
        with self._lock:
            for existing in self._items.values():
                if existing.uri == uri and existing.provenance["sha256"] == digest:
                    return existing
            if len(self._items) >= 1000:
                raise SourceRejected("candidate capacity reached")
            c = KnowledgeCandidate(new_id("kc"), gap_id, title, topic, uri, text, {
            "uri": uri, "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "validator": why,
            "provided_by": provided_by})
            self._items[c.candidate_id] = c
            self._save()
        return c

    def get(self, candidate_id: str) -> KnowledgeCandidate | None:
        return self._items.get(candidate_id)

    @staticmethod
    def _payload(c: KnowledgeCandidate) -> dict:
        return {"candidate_id": c.candidate_id, "sha256": c.provenance["sha256"]}

    def submit_for_review(self, candidate_id: str, approvals: ApprovalQueue, requested_by: str) -> ApprovalRequest:
        c = self._items[candidate_id]
        return approvals.submit("knowledge_candidate", self._payload(c), risk="medium", requested_by=requested_by,
                                summary={"title": c.title, "uri": c.uri, "gap_id": c.gap_id})

    def promote(self, candidate_id: str, approval_id: str, approvals: ApprovalQueue,
                target: VersionedKnowledgeStore, *, authority: int = 60,
                access_level: str = "internal") -> DocMeta:
        c = self._items[candidate_id]
        if c.status != "candidate" or not approvals.consume(approval_id, self._payload(c)):
            raise NotApproved("kandidat belum disetujui manusia")
        meta = target.add_document(f"kc-{c.candidate_id}", c.content, source=c.uri, topic=c.topic,
                                   authority=authority, access_level=access_level)
        c.status = "approved"
        self._save()
        return meta
