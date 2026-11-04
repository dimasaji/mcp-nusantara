from pathlib import Path

from app.knowledge.engine import KnowledgeEngine


class FakeStore:
    def __init__(self, path):
        self.db_path = Path(path)
        import sqlite3
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute('CREATE TABLE documents (document_id TEXT PRIMARY KEY, metadata_json TEXT)')


class FakeRag:
    def __init__(self, path):
        self._store = FakeStore(path)
        self.indexed = []

    def ingest_document(self, request):
        self.indexed.append(request)
        return type('Result', (), {'success': True, 'error': None, 'chunks_created': 1,
                                   'chunks_stored': 1, 'total_time_ms': 3})()

    def list_documents(self):
        from app.knowledge.schemas import DocumentInfo
        return [DocumentInfo(document_id=request.document_id, title=request.title,
                             source=request.source, content_type=request.content_type,
                             chunks_count=1, metadata=request.metadata) for request in self.indexed]


def test_pipeline_deduplicates_and_never_promotes_authority(tmp_path):
    rag = FakeRag(tmp_path / 'chat.db')
    engine = KnowledgeEngine(rag=rag)
    payload = b"Informasi proses layanan untuk warga. Persyaratan berkas mengikuti dokumen sumber ini. " * 4

    first = engine.process_knowledge_source('petunjuk.txt', payload)
    duplicate = engine.process_knowledge_source('salinan.txt', payload)

    assert first['status'] == 'READY'
    assert Path(first['source_path']).read_bytes() == payload
    assert Path(first['source_path']).parent == (tmp_path / 'source-documents')
    assert duplicate['status'] == 'DUPLICATE'
    assert Path(duplicate['source_path']).read_bytes() == payload
    assert duplicate['document_id'] == first['document_id']
    assert len(rag.indexed) == 1
    assert rag.indexed[0].metadata['source_authority'] == 'UNVERIFIED'
    assert rag.indexed[0].metadata['revision_status'] == 'NOT_CONFIRMED_CURRENT'


def test_upload_uses_explicit_sop_title_without_promoting_authority(tmp_path):
    rag = FakeRag(tmp_path / 'chat.db')
    engine = KnowledgeEngine(rag=rag)
    result = engine.process_knowledge_source('scan.txt',
        b'Nomor SOP PIAK-03\nNama S.O.P PERMOHONAN DATA PRIBADI\nIsi contoh dokumen pengujian nonrahasia.')
    assert result['status'] == 'READY'
    assert rag.indexed[0].title == 'PERMOHONAN DATA PRIBADI'
    assert rag.indexed[0].metadata['source_authority'] == 'UNVERIFIED'


def test_pipeline_retains_extraction_failure_in_chat_store_history(tmp_path):
    engine = KnowledgeEngine(rag=FakeRag(tmp_path / 'chat.db'))
    failed = engine.process_knowledge_source('binary.exe', b'not a supported knowledge document')

    assert failed['status'] == 'FAILED'
    assert failed['reason'] == 'FORMAT_NOT_SUPPORTED'
    status = engine.knowledge_pipeline_status()
    assert status['database'] == str((tmp_path / 'chat.db').resolve())
    assert status['runs'][0]['run_id'] == failed['run_id']
    assert status['runs'][0]['reason'] == 'FORMAT_NOT_SUPPORTED'


def test_folder_watch_uses_the_same_pipeline_and_deduplicates(tmp_path):
    rag = FakeRag(tmp_path / 'chat.db')
    engine = KnowledgeEngine(rag=rag)
    watch = engine.set_knowledge_watch(True)
    path = Path(watch['folder']) / 'incoming.md'
    path.write_text('Informasi prosedur layanan. Persyaratan dapat dilihat pada sumber operasional. ' * 4,
                    encoding='utf-8')

    assert engine.scan_knowledge_watch() == 1
    assert engine.scan_knowledge_watch() == 0
    status = engine.knowledge_pipeline_status()
    assert status['watch']['enabled'] is True
    assert status['runs'][0]['status'] == 'READY'
    assert len(rag.indexed) == 1


def test_piak03_extracted_sop_is_only_a_generic_pipeline_fixture(tmp_path):
    fixture = (Path(__file__).resolve().parents[1] / 'artifacts/sop-integration'
               / 'run-20261015T090151-a46af298/PERMOHONAN_DATA_PRIBADI/ingestion-text.txt')
    assert fixture.is_file(), 'PIAK-03 extracted-text fixture must remain available for pipeline verification'
    rag = FakeRag(tmp_path / 'chat.db')
    result = KnowledgeEngine(rag=rag).process_knowledge_source(fixture.name, fixture.read_bytes())

    assert result['status'] == 'READY'
    assert 'Surat Permohonan' in rag.indexed[0].source
    assert '3 Hari Kerja' in rag.indexed[0].source
    assert rag.indexed[0].metadata['source_authority'] == 'UNVERIFIED'
    assert rag.indexed[0].metadata['revision_status'] == 'NOT_CONFIRMED_CURRENT'
