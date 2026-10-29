"""Citation reads use the saved answer's private revision binding, never a URL version."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_selected_pdf_chat import approved_pdf as approved_pdf

from app.api.knowledge_pipeline import (
    create_knowledge_pipeline_router,
    get_chat_memory,
    get_chat_source_provider,
    get_knowledge_engine,
)
from app.knowledge.sop_review import SOPReview
from app.memory.engine import MemoryEngine
from app.security.v1_knowledge import V1KnowledgeBoundary, v1_session_id

SESSION = 'web-11111111-1111-4111-8111-111111111111'
REQUEST = 'e' * 32
AUTH = {'X-Admin-Token': 'source-fixture', 'X-Chat-Session': SESSION}


@pytest.fixture
def source_client(approved_pdf, monkeypatch):
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'source-fixture')
    engine, identifier = approved_pdf
    memory = MemoryEngine()
    boundary = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[identifier])
    assert boundary.search_knowledge('Persyaratan')
    answer = {'response': 'Jawaban uji', 'evidence': [{'document_id': identifier, 'pages': [2]}]}
    session = v1_session_id(SESSION, operator=True)
    memory.begin_chat(session, REQUEST, 'Pertanyaan uji')
    memory.finish_chat(session, REQUEST, answer=answer, source_versions=boundary.source_versions(answer))
    app = FastAPI()
    app.include_router(create_knowledge_pipeline_router(None), prefix='/v1')
    app.dependency_overrides[get_knowledge_engine] = lambda: engine
    app.dependency_overrides[get_chat_memory] = lambda: memory
    app.dependency_overrides[get_chat_source_provider] = lambda: 'ollama'
    with TestClient(app) as client:
        yield client, engine, identifier


def source_url(identifier, page=2):
    return f'/v1/knowledge/pipeline/reviews/{identifier}/citation?request_id={REQUEST}&page_number={page}'


def test_citation_opens_bound_pdf_page_with_auth_and_no_token_in_url(source_client):
    client, _, identifier = source_client
    result = client.get(source_url(identifier), headers=AUTH)
    assert result.status_code == 200, result.text
    assert result.content.startswith(b'%PDF-')
    assert result.headers['X-Source-Page'] == '2'
    assert result.headers['Cache-Control'] == 'no-store'
    assert client.get(source_url(identifier)).status_code == 403
    assert client.get(source_url(identifier), headers={'X-Admin-Token': 'source-fixture'}).status_code == 403
    assert client.get(source_url(identifier, page=1), headers=AUTH).status_code == 404
    other = {**AUTH, 'X-Chat-Session': SESSION.replace('11111111-', '22222222-', 1)}
    assert client.get(source_url(identifier), headers=other).status_code == 404


@pytest.mark.parametrize('action', ['reject', 'defer', 'revoke'])
def test_citation_rejects_source_after_publication_is_withdrawn(source_client, action):
    client, engine, identifier = source_client
    review = SOPReview(engine)
    detail = review.detail(identifier)
    review.decide(identifier, detail['version_id'], action, 'operator', 'Sumber perlu diperiksa')
    result = client.get(source_url(identifier), headers=AUTH)
    assert result.status_code == 409


def test_citation_rejects_changed_revision_and_cloud_provider(source_client):
    client, engine, identifier = source_client
    client.app.dependency_overrides[get_chat_source_provider] = lambda: 'openrouter'
    assert client.get(source_url(identifier), headers=AUTH).status_code == 409
    client.app.dependency_overrides[get_chat_source_provider] = lambda: 'ollama'
    doc = engine.rag.get_document_info(identifier)
    engine.rag._store.store_document_info(doc.model_copy(update={'title': 'Judul versi baru'}))
    assert client.get(source_url(identifier), headers=AUTH).status_code == 409


def test_later_trial_binding_cannot_upgrade_an_ordinary_saved_answer(source_client):
    client, engine, identifier = source_client
    review = SOPReview(engine)
    detail = review.detail(identifier)
    review.bind_session(v1_session_id(SESSION, operator=True), identifier, detail['version_id'])
    review.decide(identifier, detail['version_id'], 'revoke', 'operator', 'Sumber dicabut')
    assert client.get(source_url(identifier), headers=AUTH).status_code == 409


def test_genuine_trial_citation_retains_its_own_preview_authority(source_client):
    client, engine, identifier = source_client
    memory = client.app.dependency_overrides[get_chat_memory]()
    session = v1_session_id(SESSION, operator=True)
    regular = memory.chat_history(session)[0]
    version = regular['source_versions'][identifier]
    access = {'mode': 'review_trial', 'version': version}
    trial_request = 'f' * 32
    assert memory.begin_chat(session, trial_request, 'Pertanyaan uji', source_access=access)['state'] == 'NEW'
    memory.finish_chat(session, trial_request, answer=regular['answer'], source_versions=regular['source_versions'])
    review = SOPReview(engine)
    review.decide(identifier, version, 'defer', 'operator', 'Masih diperiksa')
    url = source_url(identifier).replace(REQUEST, trial_request)
    assert client.get(url, headers=AUTH).status_code == 200
    assert memory.begin_chat(session, REQUEST, 'Pertanyaan uji', source_access=access)['state'] == 'CONFLICT'
