"""NUS-V1-LLAMA-RAG-001 PASAL 6/7 (Defect K) — general-search pilot hydration must
be fail-safe per document.

Runtime defect: after the Defect I candidate-window widening, an Aktif pilot whose
extraction cannot be rendered (select_blocks ValueError on an oversized block, or
DOCUMENT_EXTRACTION_PARTIAL 409) entered the merged top-k and aborted the ENTIRE
search with 503 RETRIEVAL_UNAVAILABLE / 409, even though other readable evidence
existed. One unreadable pilot must be skipped, not fatal; the router abstains if
nothing readable remains. The explicitly bound single-document path still surfaces
its read error (unchanged).
"""
import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.knowledge.sop_review import SOPReview
from app.security.v1_knowledge import V1KnowledgeBoundary

GOOD = "DOC-SHA256-hydration-good"
BAD = "DOC-SHA256-hydration-bad"


def _engine():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    @contextmanager
    def pipeline_db():
        yield conn

    def search(query, top_k=None, filter=None):
        ids = (filter or {}).get("document_ids", [GOOD, BAD])
        items = [SimpleNamespace(document_id=d, title="SOP CONTOH", source="Isi.",
                                 chunk="Isi.", score=0.9, metadata={}) for d in ids]
        return items[:top_k] if top_k else items

    return SimpleNamespace(
        rag=SimpleNamespace(get_document_info=lambda i: SimpleNamespace(
            title="SOP CONTOH", source="Isi.", metadata={}),
            _store=SimpleNamespace(db_path=":memory:")),
        list_documents=lambda: SimpleNamespace(documents=[
            SimpleNamespace(document_id=GOOD), SimpleNamespace(document_id=BAD)]),
        retrieval_top_k=5, search_knowledge=search, _pipeline_db=pipeline_db)


def _citation(document_id):
    return SimpleNamespace(document_id=document_id, title="SOP CONTOH", source="Isi.",
                           chunk="Isi.", score=0.9, metadata={"version_id": "v1"})


@pytest.fixture
def patched_review(monkeypatch):
    monkeypatch.setattr(SOPReview, "is_pilot", lambda self, did: True)
    monkeypatch.setattr(SOPReview, "detail",
                        lambda self, did, **kw: {"status": "Aktif", "version_id": "v1"})

    def install(evidence_fn):
        monkeypatch.setattr(SOPReview, "evidence", evidence_fn)
    return install


def test_unreadable_pilot_valueerror_is_skipped_not_fatal(patched_review):
    def evidence(self, did, version, query=""):
        if did == BAD:
            raise ValueError("Konteks SOP tidak muat utuh: satu blok/tabel melebihi anggaran.")
        return [_citation(did)]
    patched_review(evidence)
    boundary = V1KnowledgeBoundary(_engine(), operator=True, provider="ollama")
    result = boundary.search_knowledge("Apa persyaratannya?", top_k=5)
    ids = [item.document_id for item in result]
    assert GOOD in ids
    assert BAD not in ids


def test_partial_extraction_pilot_409_is_skipped_not_fatal(patched_review):
    def evidence(self, did, version, query=""):
        if did == BAD:
            raise HTTPException(409, "Masalah pembacaan SOP: DOCUMENT_EXTRACTION_PARTIAL: DOCLING_NO_STRUCTURED_TABLES")
        return [_citation(did)]
    patched_review(evidence)
    boundary = V1KnowledgeBoundary(_engine(), operator=True, provider="ollama")
    result = boundary.search_knowledge("Apa persyaratannya?", top_k=5)
    ids = [item.document_id for item in result]
    assert GOOD in ids
    assert BAD not in ids


def test_readable_pilots_still_hydrate(patched_review):
    patched_review(lambda self, did, version, query="": [_citation(did)])
    boundary = V1KnowledgeBoundary(_engine(), operator=True, provider="ollama")
    result = boundary.search_knowledge("Apa persyaratannya?", top_k=5)
    ids = [item.document_id for item in result]
    assert GOOD in ids and BAD in ids
    assert boundary.source_versions({"evidence": [{"document_id": GOOD}]})[GOOD] == "v1"