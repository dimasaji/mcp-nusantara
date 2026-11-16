"""NUS-V1-LLAMA-RAG-001 PASAL 6/14 (Defect I) — candidate window before boost.

Runtime cause (Stage B B01, build bb166b4a): the boundary searches the eligible
catalog in batches of 20 with top_k=limit PER BATCH. The engine cuts each batch
to top_k by RAW hybrid score and only then applies the title/keyword boost.
A document whose raw hybrid rank inside its batch is below the cutoff never
receives the boost that would rank it first overall. CAPIL-01 (19 embedded
chunks, hybrid 0.527, exact-service title) lost to five boilerplate neighbours
at top_k=5 but ranked #1 at top_k=10 (reports/repro/search_probe_b01.json).

The fake engine models the real engine semantics faithfully: cut by raw rank
within the requested scope, return survivors with their boosted scores.
General fixture — 25 neutral documents, no PIAK-03/CAPIL-01 specifics.
"""
import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace

from app.security.v1_knowledge import V1KnowledgeBoundary

CORRECT = "DOC-SHA256-window-target"
IDS = [f"DOC-SHA256-window-{i:02d}" for i in range(25)]
IDS[18] = CORRECT

# Raw hybrid ranks: seven documents in the first batch beat the target (0.50);
# the second batch (20..24) sits at 0.56-0.60. Only the target earns the big
# title boost (1.0) — but only if it survives its batch's candidate cutoff.
RAW = {}
for i, did in enumerate(IDS):
    if i < 7:
        RAW[did] = 0.70 - 0.01 * i
    elif did == CORRECT:
        RAW[did] = 0.50
    elif i < 20:
        RAW[did] = 0.49 - 0.005 * i
    else:
        RAW[did] = 0.60 - 0.01 * (i - 20)
BOOSTED = {did: (1.0 if did == CORRECT else RAW[did]) for did in IDS}


def _engine():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    @contextmanager
    def pipeline_db():
        yield conn

    def search(query, top_k=None, filter=None):
        scope = (filter or {}).get("document_ids") or IDS
        ranked = sorted(scope, key=lambda d: RAW[d], reverse=True)[: top_k or 5]
        return [SimpleNamespace(document_id=d, title=f"LAYANAN CONTOH {d[-2:]}",
                                source="Isi layanan contoh.", chunk="Isi layanan contoh.",
                                score=BOOSTED[d], metadata={}) for d in ranked]

    def info(identifier):
        if identifier not in IDS:
            return None
        return SimpleNamespace(title=f"LAYANAN CONTOH {identifier[-2:]}",
                               source="Isi layanan contoh.", metadata={})

    return SimpleNamespace(
        rag=SimpleNamespace(get_document_info=info,
                            _store=SimpleNamespace(db_path=":memory:")),
        list_documents=lambda: SimpleNamespace(
            documents=[SimpleNamespace(document_id=d) for d in IDS]),
        retrieval_top_k=5,
        search_knowledge=search,
        _pipeline_db=pipeline_db)


def test_strong_title_match_survives_batch_candidate_cutoff():
    boundary = V1KnowledgeBoundary(_engine(), operator=True, provider="ollama")
    result = boundary.search_knowledge("apa persyaratan layanan contoh akta kelahiran tangerang live")
    top = [item.document_id for item in result]
    assert CORRECT in top, f"boosted target lost to batch cutoff: {top}"
    assert top[0] == CORRECT


def test_result_still_bounded_and_sorted():
    boundary = V1KnowledgeBoundary(_engine(), operator=True, provider="ollama")
    result = boundary.search_knowledge("apa persyaratan layanan contoh")
    assert len(result) <= 5
    scores = [item.score for item in result]
    assert scores == sorted(scores, reverse=True)


def test_equal_boost_tie_broken_by_raw_hybrid():
    # Two exact-title competitors both saturate at boosted 1.0. The one with the
    # higher RAW hybrid (closer semantic+lexical match) must win, not batch order.
    low = "DOC-SHA256-tie-low"
    high = "DOC-SHA256-tie-high"
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    @contextmanager
    def pipeline_db():
        yield conn

    def search(query, top_k=None, filter=None):
        return [SimpleNamespace(document_id=low, title="LAYANAN CONTOH", source="Isi.",
                                chunk="Isi.", score=1.0, metadata={"hybrid_score": 0.40}),
                SimpleNamespace(document_id=high, title="LAYANAN CONTOH", source="Isi.",
                                chunk="Isi.", score=1.0, metadata={"hybrid_score": 0.80})]

    eng = SimpleNamespace(
        rag=SimpleNamespace(get_document_info=lambda i: SimpleNamespace(
            title="LAYANAN CONTOH", source="Isi.", metadata={}),
            _store=SimpleNamespace(db_path=":memory:")),
        list_documents=lambda: SimpleNamespace(documents=[
            SimpleNamespace(document_id=low), SimpleNamespace(document_id=high)]),
        retrieval_top_k=5, search_knowledge=search, _pipeline_db=pipeline_db)
    boundary = V1KnowledgeBoundary(eng, operator=True, provider="ollama")
    result = boundary.search_knowledge("apa persyaratan layanan contoh")
    assert [item.document_id for item in result][0] == high