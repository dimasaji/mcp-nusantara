"""NUS-V1-LLAMA-RAG-001 PASAL 5/7 (Defect F residual) — prior-evidence reuse must
re-bind the cited source through the V1 knowledge boundary.

Runtime defect: the reuse fast-path cited the prior SOP although the current
turn's scoped retrieval returned ev=0, so the boundary had no retrieval-time
version for it and routes.validate_response raised 409
CHAT_SOURCE_VERSION_UNAVAILABLE (Stage A T09/T10 HTTP 409, build 03f05cb8).
The boundary must expose a fail-closed re-bind: re-check current access and
record the CURRENT version, or raise so the agent abstains instead of citing.
"""
import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.security.v1_knowledge import V1KnowledgeBoundary

DOC = "DOC-SHA256-rebind-example"


def _engine(document=None):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    @contextmanager
    def pipeline_db():
        yield conn

    return SimpleNamespace(
        rag=SimpleNamespace(get_document_info=lambda identifier: document,
                            _store=SimpleNamespace(db_path=":memory:")),
        list_documents=lambda: SimpleNamespace(documents=[]),
        retrieval_top_k=5,
        search_knowledge=lambda *a, **k: [],
        _pipeline_db=pipeline_db)


def _document():
    # Neutral title: must not match the SOP pilot heuristic in SOPReview.is_pilot.
    return SimpleNamespace(title="LAYANAN CONTOH", source="Isi layanan contoh.",
                           metadata={"page": 1})


def test_rebind_records_current_version_for_available_source():
    boundary = V1KnowledgeBoundary(_engine(_document()), operator=True, provider="ollama")
    boundary.reuse_prior_citation(DOC)
    answer = {"evidence": [{"document_id": DOC}]}
    boundary.validate_response(answer)  # must not raise
    assert boundary.source_versions(answer)[DOC]


def test_rebind_missing_source_fails_closed():
    boundary = V1KnowledgeBoundary(_engine(None), operator=True, provider="ollama")
    with pytest.raises(HTTPException) as exc:
        boundary.reuse_prior_citation(DOC)
    assert exc.value.status_code == 409


def test_rebind_requires_operator_local_model():
    boundary = V1KnowledgeBoundary(_engine(_document()), operator=False, provider="ollama")
    with pytest.raises(HTTPException) as exc:
        boundary.reuse_prior_citation(DOC)
    assert exc.value.status_code == 409
    # Non-local provider is already denied at the boundary constructor.
    with pytest.raises(HTTPException) as exc:
        V1KnowledgeBoundary(_engine(_document()), operator=True, provider="openrouter")
    assert exc.value.status_code == 409


def test_rebind_then_source_change_is_detected():
    document = _document()
    boundary = V1KnowledgeBoundary(_engine(document), operator=True, provider="ollama")
    boundary.reuse_prior_citation(DOC)
    document.source = "Isi SOP berubah."
    with pytest.raises(HTTPException) as exc:
        boundary.validate_response({"evidence": [{"document_id": DOC}]})
    assert exc.value.status_code == 409