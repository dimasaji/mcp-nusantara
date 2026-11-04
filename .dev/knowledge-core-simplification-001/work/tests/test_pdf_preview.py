import hashlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.knowledge_pipeline import create_knowledge_pipeline_router, get_knowledge_engine
from app.knowledge.sop_review import SOPReview
from test_selected_pdf_chat import table_pdf
from test_sop_review import engine_at


def test_original_pdf_preview_uses_physical_page_and_access_control(tmp_path, monkeypatch):
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'preview-fixture')
    engine = engine_at(tmp_path / 'chat.db')
    raw = table_pdf()
    run = engine.process_knowledge_source('table.pdf', raw)
    detail = SOPReview(engine).detail(run['document_id'])
    app = FastAPI()
    app.include_router(create_knowledge_pipeline_router(None))
    app.dependency_overrides[get_knowledge_engine] = lambda: engine
    client = TestClient(app)
    url = f"/knowledge/pipeline/reviews/{run['document_id']}/source?version_id={detail['version_id']}"
    assert client.get(url + '&page_number=2').status_code == 403
    headers = {'X-Admin-Token': 'preview-fixture'}
    response = client.get(url + '&page_number=2', headers=headers)
    assert response.status_code == 200
    assert response.content.startswith(b'\x89PNG\r\n\x1a\n')
    assert response.headers['x-source-page'] == '2'
    assert response.headers['x-source-sha256'] == hashlib.sha256(raw).hexdigest()
    assert client.get(url + '&page_number=3', headers=headers).status_code == 422
    assert client.get(url, headers=headers).content == raw
