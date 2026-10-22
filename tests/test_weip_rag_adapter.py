"""Offline adapter tests. Synthetic consent/embeddings; no official authority claim."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.knowledge.web_evidence import EvidenceRejected
from app.knowledge.store import SQLiteVectorStore
from app.knowledge.rag import RAG
from app.knowledge.schemas import DocumentIngestRequest, KnowledgeBaseConfig
from test_web_evidence_pipeline import pipeline, verified, source, Response, collect

TEXT = 'Syarat KTP-el: pemohon berusia 17 tahun dan membawa Kartu Keluarga.'


def make_adapter(tmp_path):
    p, _ = pipeline(tmp_path, entry=verified(), responses=[Response(body=TEXT.encode())])
    p.now = lambda: datetime(2026, 10, 9, tzinfo=timezone.utc)
    auth = p.review_authorizer
    p.review_authorizer = lambda *a: replace(auth(*a), purposes=('temporary_rag_ingestion',))
    r = collect(p, publication_date='2020-01-01', effective_date='2020-01-01', expiry_date='2099-01-01')
    r = p.approve(r['document_id'], reviewer='fixture-reviewer', review_reference='fixture-only',
                  purpose='temporary_rag_ingestion')
    store = SQLiteVectorStore(str(tmp_path/'isolated.db'))
    rag = RAG(vector_store=store, embedding_func=lambda text: [1.0]+[0.0]*767)
    return p, r, rag, store


def test_remaining_task1_approved_adapter_retrievable(tmp_path):
    p, r, rag, store = make_adapter(tmp_path)
    result = p.ingest_into_temporary_rag(r['document_id'], rag, temporary_root=tmp_path)
    assert result.success
    assert store.get_document_info(r['document_id']).metadata['approval']['purpose'] == 'temporary_rag_ingestion'
    assert rag.query('Apa syarat membuat KTP?').evidence_pack.evidence[0].document_id == r['document_id']
    assert p.staging.get(r['document_id'])['status'] == 'APPROVED_FOR_INGESTION'


@pytest.mark.parametrize('invalid', ['expired','revoked','purpose','version','hash','provenance','rejected'])
def test_remaining_task1_rejected_never_enters_retrieval(tmp_path, invalid):
    p, r, rag, store = make_adapter(tmp_path)
    auth = p.review_authorizer
    if invalid == 'expired':
        p.now = lambda: datetime(2099, 1, 1, tzinfo=timezone.utc)
    elif invalid == 'revoked':
        p.review_authorizer = lambda *a: replace(auth(*a), revoked=True)
    elif invalid == 'purpose':
        p.review_authorizer = lambda *a: replace(auth(*a), purposes=('other',))
    elif invalid == 'provenance':
        p.review_authorizer = lambda *a: replace(auth(*a), provenance_reference=None)
    elif invalid == 'hash':
        (p.staging.root/(r['document_id']+'.bin')).write_bytes(b'changed')
    else:
        if invalid == 'version':
            r['version'] = 'changed'
        else:
            r['approval']['status'] = 'REJECTED'
        p.staging._save(r)
    with pytest.raises(EvidenceRejected):
        p.ingest_into_temporary_rag(r['document_id'], rag, temporary_root=tmp_path)
    assert store.list_documents() == []
    assert rag.query('Apa syarat membuat KTP?').evidence_pack.evidence == []


def test_remaining_task1_requires_explicit_temporary_boundary(tmp_path):
    p, r, rag, _ = make_adapter(tmp_path)
    # No production path is opened. The adapter rejects a store outside caller root.
    with pytest.raises(EvidenceRejected, match='TEMPORARY_STORE_REQUIRED'):
        p.ingest_into_temporary_rag(r['document_id'], rag, temporary_root=tmp_path/'other')


@pytest.mark.parametrize('stage', ['document','embedding','chunk','count','post_validation'])
def test_remaining_task2_failure_rolls_back_and_preserves_previous(tmp_path, monkeypatch, stage):
    p, r, rag, store = make_adapter(tmp_path)
    previous = DocumentIngestRequest(document_id='previous', title='Earlier fixture', source='Akta kelahiran memerlukan surat kelahiran.')
    assert rag.ingest_document(previous).success
    before_doc = store.get_document_info('previous').model_dump()
    before_chunks = [c.model_dump() for c in store.get_chunks_by_document('previous')]
    def fail(*a, **k):
        raise RuntimeError('fixture failure')
    if stage == 'embedding':
        rag._embedding = fail
    elif stage == 'post_validation':
        auth = p.review_authorizer
        count = [0]
        def authorize(*a):
            count[0] += 1
            return replace(auth(*a), revoked=count[0] > 1)
        p.review_authorizer = authorize
    else:
        name = {'document':'store_document_info','chunk':'store_chunk','count':'update_document_chunks_count'}[stage]
        original = getattr(store, name)
        def write_then_fail(*a, **k):
            original(*a, **k)
            fail()
        monkeypatch.setattr(store, name, write_then_fail)
    with pytest.raises(EvidenceRejected):
        p.ingest_into_temporary_rag(r['document_id'], rag, temporary_root=tmp_path)
    assert store.get_document_info(r['document_id']) is None
    assert store.get_chunks_by_document(r['document_id']) == []
    assert store.get_document_info('previous').model_dump() == before_doc
    assert [c.model_dump() for c in store.get_chunks_by_document('previous')] == before_chunks


def test_remaining_task2_replay_preserves_existing_version_without_reembedding(tmp_path):
    p, r, rag, store = make_adapter(tmp_path)
    assert p.ingest_into_temporary_rag(r['document_id'], rag, temporary_root=tmp_path).success
    old_doc = store.get_document_info(r['document_id']).model_dump()
    old_chunks = [c.model_dump() for c in store.get_chunks_by_document(r['document_id'])]
    rag._embedding = lambda _: (_ for _ in ()).throw(RuntimeError('fixture failed replacement'))
    replay = p.ingest_into_temporary_rag(r['document_id'], rag, temporary_root=tmp_path)
    assert replay.success and replay.chunks_created == 0
    assert store.get_document_info(r['document_id']).model_dump() == old_doc
    assert [c.model_dump() for c in store.get_chunks_by_document(r['document_id'])] == old_chunks


def test_remaining_task2_staging_initial_write_failure_has_no_partial_files(tmp_path, monkeypatch):
    p, _ = pipeline(tmp_path)
    original = Path.replace
    def failure(path, target):
        if path.suffix == '.pending':
            raise OSError('fixture staging failure')
        return original(path, target)
    monkeypatch.setattr(Path, 'replace', failure)
    with pytest.raises(OSError):
        collect(p)
    assert p.staging.list() == []
    assert list(p.staging.root.glob('WEIP-*')) == []


def test_remaining_task2_fetch_failure_has_no_document(tmp_path):
    p, _ = pipeline(tmp_path, responses=[Response(status=404)])
    with pytest.raises(EvidenceRejected):
        collect(p)
    assert p.staging.list() == []


@pytest.mark.parametrize('permanent', [False, True])
def test_remaining_task2_atomic_rename_retry_is_bounded(tmp_path, monkeypatch, permanent):
    p, _ = pipeline(tmp_path)
    original = Path.replace
    calls = []
    def rename(path, target):
        if path.suffix == '.pending':
            calls.append(path)
            if permanent or len(calls) <= 2:
                error = PermissionError('synthetic Windows sharing failure')
                error.winerror = 5
                raise error
        return original(path, target)
    monkeypatch.setattr(Path, 'replace', rename)
    monkeypatch.setattr('app.knowledge.web_evidence.time.sleep', lambda _: None)
    if permanent:
        with pytest.raises(PermissionError):
            collect(p)
        assert len(calls) == 3
        assert list(p.staging.root.glob('WEIP-*')) == []
    else:
        assert collect(p)['status'] == 'REVIEW_REQUIRED'
        assert len(calls) == 6  # First transition: three attempts; later writes once.
    assert list(p.staging.root.glob('*.pending')) == []


def test_remaining_task2_changed_request_during_ingestion_rolls_back(tmp_path):
    p, r, rag, store = make_adapter(tmp_path)
    changed = [False]
    def embedding(text):
        if not changed[0]:
            record = p.staging.get(r['document_id'])
            record['metadata']['title'] = 'changed during operation'
            record['approval']['binding'] = p._approval_binding(record)
            p.staging._save(record)
            changed[0] = True
        return [1.0]+[0.0]*767
    rag._embedding = embedding
    with pytest.raises(EvidenceRejected, match='DOCUMENT_CHANGED_DURING_INGESTION'):
        p.ingest_into_temporary_rag(r['document_id'], rag, temporary_root=tmp_path)
    assert store.list_documents() == []


@pytest.mark.parametrize('body,parser,quarantined', [
    (b'%PDF-1.4 fixture', lambda _: TEXT, False),
    (b'broken', lambda _: TEXT, True),
    (b'', lambda _: TEXT, True),
    (b'%PDF-1.4 fixture', lambda _: '', True),
    (b'%PDF-1.4 fixture', lambda _: (_ for _ in ()).throw(RuntimeError('private parser error')), True),
    (b'%PDF-1.4 /JavaScript', lambda _: TEXT, True),
    (b'%PDF-1.4 fixture', None, True),
])
def test_remaining_task3_pdf_failure_containment(tmp_path, body, parser, quarantined):
    p, _ = pipeline(tmp_path, entry=source(kind='PDF'), responses=[Response(body=body, headers={'Content-Type':'application/pdf'})])
    p.pdf_parser = parser  # Synthetic offline seam only; native extraction is blocked.
    r = collect(p)
    assert r['status'] == ('QUARANTINED' if quarantined else 'REVIEW_REQUIRED')
    with pytest.raises(EvidenceRejected):
        p.to_v1_request(r['document_id'])
    if quarantined:
        assert r['text'] is None
        assert r['audit'][-1]['reason'] == 'PARSE_UNSAFE_OR_UNAVAILABLE'


def test_remaining_task4_filter_grammar_stays_fail_closed(tmp_path):
    from app.knowledge.engine import KnowledgeEngine
    _, _, rag, _ = make_adapter(tmp_path)
    engine = KnowledgeEngine(rag=rag)
    with pytest.raises(ValueError, match='KNOWLEDGE_FILTER_NOT_SUPPORTED'):
        engine.search_knowledge('KTP', filter={'official':True})
    assert engine.search_knowledge('KTP', filter={}) == []


def test_remaining_task4_ktp_reranking_and_grounding(tmp_path):
    from app.knowledge.grounding import EvidenceGroundingGuard
    p, r, rag, store = make_adapter(tmp_path)
    rag._config.reranker_enabled = True
    def embedding(text):
        return ([1.0,0.0] if 'ktp' in text.lower() else [0.0,1.0])+[0.0]*766
    rag._embedding = embedding
    p.ingest_into_temporary_rag(r['document_id'], rag, temporary_root=tmp_path)
    assert rag.ingest_document(DocumentIngestRequest(document_id='birth', title='Akta', source='Persyaratan akta kelahiran: surat kelahiran.')).success
    result = rag.query('Apa syarat membuat KTP?', top_k=1, rerank=True)
    assert result.evidence_pack.reranked
    assert [e.document_id for e in result.evidence_pack.evidence] == [r['document_id']]
    assert store.search_lexical('syarat KTP')[0][0].document_id == r['document_id']
    guard = EvidenceGroundingGuard()
    invalid = guard.validate('Untuk membuat KTP wajib membawa sertifikat tanah dan membayar 999 rupiah.', result.evidence_pack.evidence, intent_name='ask_document_requirements')
    assert not invalid.grounded
