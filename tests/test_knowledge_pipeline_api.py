"""HTTP tests: no live application import, store, token or embedding worker."""
import asyncio
import io
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.api.knowledge_pipeline import create_knowledge_pipeline_router, get_knowledge_engine
from app.knowledge.engine import KnowledgeEngine
from app.knowledge.rag import RAG
from app.knowledge.schemas import KnowledgeBaseConfig
from app.knowledge.store import SQLiteVectorStore


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'isolated-upload-fixture')
    engine = KnowledgeEngine(rag=RAG(
        config=KnowledgeBaseConfig(embedding_model='fixture', embedding_dimension=3),
        vector_store=SQLiteVectorStore(str(tmp_path / 'chat.db')),
        embedding_func=lambda text: [1.0, 0.0, 0.0],
    ))

    async def run_sync(function, *args, timeout_s):
        return await asyncio.wait_for(asyncio.to_thread(function, *args), timeout_s)

    app = FastAPI()
    app.include_router(create_knowledge_pipeline_router(run_sync), prefix='/v1')
    app.dependency_overrides[get_knowledge_engine] = lambda: engine
    with TestClient(app) as http:
        yield http
    app.dependency_overrides.clear()


AUTH = {'X-Admin-Token': 'isolated-upload-fixture'}
UPLOAD = '/v1/knowledge/pipeline/documents'
STATUS = '/v1/knowledge/pipeline/status'


def pdf_bytes():
    output = io.BytesIO()
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=800)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
        NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
        DictionaryObject({NameObject('/F1'): font})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 750 Td '
        b'(Persyaratan layanan: Surat Permohonan. Waktu layanan adalah 3 Hari Kerja.) Tj ET')
    page[NameObject('/Contents')] = stream
    writer.write(output)
    return output.getvalue()


def upload(client, payload, filename='Petunjuk layanan.pdf'):
    return client.post(UPLOAD, content=payload, headers={**AUTH,
        'Content-Type': 'application/octet-stream', 'X-Document-Name': quote(filename)})


def test_pdf_upload_processing_history_and_duplicate(client, tmp_path):
    before = client.get(STATUS, headers=AUTH)
    assert before.status_code == 200
    assert before.json()['runs'] == []
    raw = pdf_bytes()
    response = upload(client, raw)
    assert response.status_code == 200, response.text
    ready = response.json()
    assert ready['status'] == 'READY', ready
    assert ready['filename'] == 'Petunjuk layanan.pdf'
    assert ready['chunks_stored'] > 0
    assert ready['reason'] is None
    source = Path(ready['source_path'])
    assert source.is_relative_to(tmp_path)
    assert source.read_bytes() == raw
    history = client.get(STATUS, headers=AUTH).json()
    assert history['database'] == str((tmp_path / 'chat.db').resolve())
    assert history['documents_indexed'] == history['pipeline_ready_documents'] == 1
    assert history['runs'][0]['run_id'] == ready['run_id']
    duplicate = upload(client, raw, 'Salinan.pdf').json()
    assert duplicate['status'] == 'DUPLICATE'
    assert duplicate['document_id'] == ready['document_id']
    assert duplicate['run_id'] != ready['run_id']
    history = client.get(STATUS, headers=AUTH).json()
    assert [run['status'] for run in history['runs']] == ['DUPLICATE', 'READY']
    assert history['documents_indexed'] == history['pipeline_ready_documents'] == 1
    assert len(list((tmp_path / 'source-documents').iterdir())) == 1


def test_failed_pdf_is_recorded_and_does_not_hide_ready_history(client):
    ready = upload(client, pdf_bytes()).json()
    failed = upload(client, b'not a PDF', 'broken.pdf')
    assert failed.status_code == 200
    assert failed.json()['status'] == 'FAILED'
    assert failed.json()['reason']
    assert failed.json()['document_id'] is None
    history = client.get(STATUS, headers=AUTH).json()
    assert [run['status'] for run in history['runs']] == ['FAILED', 'READY']
    assert history['runs'][1]['document_id'] == ready['document_id']
    assert history['documents_indexed'] == history['pipeline_ready_documents'] == 1


def test_upload_and_history_require_admin_and_empty_document_is_rejected(client, tmp_path):
    assert client.post(UPLOAD, content=pdf_bytes()).status_code == 403
    assert client.get(STATUS).status_code == 403
    assert client.get(STATUS, headers={'X-Admin-Token': 'wrong'}).status_code == 403
    empty = upload(client, b'')
    assert empty.status_code == 422
    assert empty.json() == {'detail': 'DOCUMENT_EMPTY'}
    assert client.get(STATUS, headers=AUTH).json()['runs'] == []
    assert not (tmp_path / 'source-documents').exists()


def test_retry_failed_source_after_reopening_history_requires_auth(client):
    failed=upload(client,b'not a PDF','retry.pdf').json()
    path=f"/v1/knowledge/pipeline/runs/{failed['run_id']}/retry"
    assert client.post(path).status_code==403
    retry=client.post(path,headers=AUTH)
    assert retry.status_code==200
    assert retry.json()['status']=='FAILED'
    assert retry.json()['run_id']!=failed['run_id']
    assert len(client.get(STATUS,headers=AUTH).json()['runs'])==2


def test_history_remains_readable_while_embedding_is_running(client,tmp_path):
    from threading import Event
    from concurrent.futures import ThreadPoolExecutor
    started,release=Event(),Event()
    def embed(text):
        started.set()
        assert release.wait(12)
        return [1.,0.,0.]
    engine=KnowledgeEngine(rag=RAG(config=KnowledgeBaseConfig(embedding_model='fixture',embedding_dimension=3),
        vector_store=SQLiteVectorStore(str(tmp_path/'concurrent.db')),embedding_func=embed))
    client.app.dependency_overrides[get_knowledge_engine]=lambda:engine
    assert client.get(STATUS,headers=AUTH).status_code==200
    with ThreadPoolExecutor() as pool:
        pending=pool.submit(upload,client,pdf_bytes())
        assert started.wait(3)
        try:
            response=client.get(STATUS,headers=AUTH)
            assert response.status_code==200
            assert response.json()['runs'][0]['status']=='PROCESSING'
        finally:
            release.set()
        assert pending.result().json()['status']=='READY'


def test_retry_recovers_committed_index_after_interrupted_finalization(client,tmp_path):
    import sqlite3
    uploaded=upload(client,pdf_bytes()).json()
    # Fault injection: crash window after index commit, before final run status.
    with sqlite3.connect(tmp_path/'chat.db') as db:
        db.execute("UPDATE knowledge_pipeline_runs SET status='PROCESSING' WHERE run_id=?",(uploaded['run_id'],))
    reopened=KnowledgeEngine(rag=RAG(config=KnowledgeBaseConfig(embedding_model='fixture',embedding_dimension=3),
        vector_store=SQLiteVectorStore(str(tmp_path/'chat.db')),embedding_func=lambda text:[1.,0.,0.]))
    client.app.dependency_overrides[get_knowledge_engine]=lambda:reopened
    assert client.get(STATUS,headers=AUTH).json()['runs'][0]['status']=='FAILED'
    result=client.post(f"/v1/knowledge/pipeline/runs/{uploaded['run_id']}/retry",headers=AUTH).json()
    assert result['status']=='READY',result
    assert result['document_id']==uploaded['document_id']
    assert client.get(STATUS,headers=AUTH).json()['documents_indexed']==1
