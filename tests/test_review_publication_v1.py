"""Publication gates at the existing V1 review/retrieval interfaces."""
from test_sop_review import engine_at

from app.knowledge.sop_review import SOPReview
from app.security.v1_knowledge import V1KnowledgeBoundary


def _pdf():
    import pymupdf
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((30,50), 'SOP layanan: Persyaratan Surat Permohonan. Waktu pelayanan tiga hari kerja.')
    raw = pdf.tobytes()
    pdf.close()
    return raw


def _approve_fixture(review, detail):
    """Synthetic reviewer decisions in a newly created test DB only."""
    identifier,version = detail['document_id'],detail['version_id']
    review.decide(identifier,version,'content_ok','test-reviewer')
    for case in detail['required_cases']:
        trial = review.record_trial(identifier,version,case,'Pertanyaan fixture',
                                    {'response':'Jawaban fixture'},'test-reviewer')
        review.rate(identifier,version,trial['trial_id'],True,'','test-reviewer')
    return review.decide(identifier,version,'approve','test-reviewer')


def _convert(tools, review, identifier, *, force=False):
    import time
    detail = review.detail(identifier)
    tools.process(identifier,detail['version_id'],force=force)
    deadline = time.monotonic()+10
    while tools.status(identifier)['status'] in {'QUEUED','PROCESSING'} and time.monotonic()<deadline:
        time.sleep(.01)
    assert tools.status(identifier)['status']=='COMPLETE'
    return review.detail(identifier)


def test_uploaded_sop_is_not_chat_knowledge_before_review_enrollment(tmp_path):
    engine = engine_at(tmp_path / 'chat.db')
    uploaded = engine.process_knowledge_source('scan.txt',
        b'Nama S.O.P PERMOHONAN DATA PRIBADI\nPersyaratan: Surat Permohonan. Waktu pelayanan tiga hari kerja.')
    identifier = uploaded['document_id']
    normal = V1KnowledgeBoundary(engine, operator=True, provider='ollama')
    selected = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[identifier])
    assert normal.search_knowledge('Persyaratan') == []
    assert selected.search_knowledge('Persyaratan') == []
    detail = SOPReview(engine).detail(identifier)
    trial = V1KnowledgeBoundary(engine, operator=True, provider='ollama',
                                document_ids=[identifier], sop_version=detail['version_id'], review_trial=True)
    assert trial.search_knowledge('Persyaratan')[0].document_id == identifier
    assert normal.search_knowledge('Persyaratan') == []


def test_changed_extracted_content_requires_a_new_review_and_approval(tmp_path, monkeypatch):
    import json
    from pathlib import Path
    from types import SimpleNamespace

    from app.knowledge.document_tools import DocumentTools
    engine = engine_at(tmp_path/'chat.db')
    uploaded = engine.process_knowledge_source('SOP.pdf',_pdf())
    identifier = uploaded['document_id']
    review = SOPReview(engine)
    outputs = ['Persyaratan: Surat Permohonan.','Persyaratan: Surat Pengantar.']
    def worker(args, **kwargs):
        text = outputs.pop(0)
        Path(args[-1]).write_text(json.dumps({'status':'COMPLETE','warnings':[],
            'page_count':1,'markdown':text,'docling_json':{'test':True},
            'blocks':[{'block_id':'#/texts/0','type':'text','content':text,'page_numbers':[1]}]}),encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr('app.knowledge.worker_process.run_worker',worker)
    monkeypatch.setattr('app.knowledge.document_tools.effective_config', lambda: {'fixture': True})
    tools = DocumentTools(engine,operator=True)
    first = _convert(tools,review,identifier)
    assert tools.compare_previous(identifier, first['version_id']) is None
    approved = _approve_fixture(review,first)
    assert approved['status']=='Aktif'
    normal = V1KnowledgeBoundary(engine,operator=True,provider='ollama',document_ids=[identifier])
    assert normal.search_knowledge('Persyaratan')[0].document_id==identifier
    second = _convert(tools,review,identifier,force=True)
    assert second['version_id']!=first['version_id']
    assert second['content_ok'] is False
    assert second['approval'] is None
    comparison = tools.compare_previous(identifier, second['version_id'])
    assert comparison['previous_version_id'] == first['version_id']
    assert comparison['version_id'] == second['version_id']
    assert comparison['changed_blocks'] == 1
    assert comparison['changes'][0]['before'] == 'Persyaratan: Surat Permohonan.'
    assert comparison['changes'][0]['after'] == 'Persyaratan: Surat Pengantar.'
    assert comparison['changes'][0]['pages'] == [1]
    assert normal.search_knowledge('Persyaratan')==[]
    import pytest
    with pytest.raises(ValueError,match='Versi berubah'):
        review.decide(identifier,first['version_id'],'content_ok','test-reviewer')
    assert _approve_fixture(review,second)['status']=='Aktif'
    assert 'Surat Pengantar' in normal.search_knowledge('Persyaratan')[0].source
    unscoped = V1KnowledgeBoundary(engine,operator=True,provider='ollama')
    assert 'Surat Pengantar' in unscoped.search_knowledge('Persyaratan')[0].source


def test_pending_candidates_cannot_displace_approved_knowledge_at_topk(tmp_path):
    engine = engine_at(tmp_path/'chat.db')
    engine.rag.set_embedding_func(lambda text: [1.,0.,0.] if text=='Persyaratan' or 'TERTUNDA' in text else [.8,.6,0.])
    engine.process_knowledge_source('pending.txt',
        b'TERTUNDA. Persyaratan contoh belum diperiksa oleh operator dan belum disetujui.')
    identifier = engine.process_knowledge_source('approved.txt',
        b'Persyaratan layanan: Surat Permohonan. Waktu pelayanan adalah tiga hari kerja.')['document_id']
    review = SOPReview(engine)
    _approve_fixture(review,review.detail(identifier))
    boundary = V1KnowledgeBoundary(engine,operator=True,provider='ollama')
    evidence = boundary.search_knowledge('Persyaratan',top_k=1)
    assert [item.document_id for item in evidence]==[identifier]


def test_concurrent_conversion_cannot_label_new_content_with_old_version(tmp_path, monkeypatch):
    import json
    import sqlite3
    import threading
    import time
    from pathlib import Path
    from types import SimpleNamespace

    from app.knowledge.document_tools import DocumentReadError, DocumentTools
    engine = engine_at(tmp_path/'chat.db')
    identifier = engine.process_knowledge_source('SOP.pdf',_pdf())['document_id']
    review = SOPReview(engine)
    release,started = threading.Event(),threading.Event()
    outputs = ['Ekstraksi pertama: Surat Permohonan.','Ekstraksi baru: Surat Pengantar.']
    def worker(args, **kwargs):
        text = outputs.pop(0)
        if 'baru' in text:
            started.set()
            assert release.wait(10)
        Path(args[-1]).write_text(json.dumps({'status':'COMPLETE','warnings':[],
            'page_count':1,'markdown':text,'docling_json':{'test':True},
            'blocks':[{'block_id':'#/texts/0','type':'text','content':text,'page_numbers':[1]}]}),encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr('app.knowledge.worker_process.run_worker',worker)
    monkeypatch.setattr('app.knowledge.document_tools.effective_config', lambda: {'fixture': True})
    tools = DocumentTools(engine,operator=True)
    first = _convert(tools,review,identifier)
    job = tools.process(identifier,first['version_id'],force=True)
    assert started.wait(5)
    connect = sqlite3.connect
    triggered = []
    def trace(statement):
        if not triggered and statement.startswith("UPDATE document_extractions SET status='FAILED'"):
            triggered.append(True)
            release.set()
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                with connect(tmp_path/'chat.db') as db:
                    row=db.execute('SELECT status FROM document_extractions WHERE job_id=?',(job['job_id'],)).fetchone()
                if row[0]=='COMPLETE':
                    return
                time.sleep(.01)
            raise AssertionError('Concurrent conversion did not complete')
    def controlled_connect(*args, **kwargs):
        connection=connect(*args,**kwargs)
        if threading.current_thread() is threading.main_thread():
            connection.set_trace_callback(trace)
        return connection
    monkeypatch.setattr(sqlite3,'connect',controlled_connect)
    try:
        result=tools.baca_dokumen(identifier,first['version_id'])
    except DocumentReadError as exc:
        assert 'VERSION_CHANGED' in str(exc) or 'VERSION_NOT_FOUND' in str(exc)
    else:
        assert result['blocks'][0]['content']=='Ekstraksi pertama: Surat Permohonan.'
    finally:
        release.set()
    assert triggered

