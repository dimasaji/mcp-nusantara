"""Authenticated discovery, invocation, automatic upload and publication checks."""
import asyncio
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_knowledge_pipeline_api import AUTH, upload
from test_knowledge_pipeline_api import client as pipeline_client  # noqa: F401
from test_review_publication_v1 import _approve_fixture, _pdf

from app.api.knowledge_pipeline import get_knowledge_engine
from app.api.skills import create_skill_router
from app.knowledge.sop_review import SOPReview


@pytest.fixture
def skill_client(pipeline_client):  # noqa: F811 - imported pytest fixture
    async def run_sync(fn, *args, timeout_s):
        return await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout_s)
    pipeline_client.app.include_router(create_skill_router(run_sync), prefix='/v1')
    return pipeline_client


def test_discovery_and_invocation_enforce_authorization(skill_client):
    assert skill_client.get('/v1/skills').status_code == 403
    response = skill_client.get('/v1/skills', headers=AUTH)
    assert response.status_code == 200
    assert {s['name'] for s in response.json()['skills']} == {
        'documents.prepare', 'documents.inspect', 'knowledge.search', 'sop.facts'}
    url = '/v1/skills/knowledge.search/run'
    assert skill_client.post(url, json={'arguments': {'query': 'layanan'}}).status_code == 403
    assert skill_client.post(url, headers=AUTH, json={'arguments': {'query': 'layanan'}, 'role': 'operator'}).status_code == 422
    assert skill_client.post(url, headers=AUTH, json={'arguments': {'query': 'layanan', 'permissions': ['admin']}}).status_code == 422
    assert skill_client.post('/v1/skills/missing/run', headers=AUTH, json={}).status_code == 404


def test_upload_calls_preparation_skill_and_duplicate_reuses_job(skill_client, monkeypatch):
    def worker(args, **kwargs):
        text = 'Persyaratan: Surat Contoh untuk layanan warga.'
        Path(args[-1]).write_text(json.dumps({'status': 'COMPLETE', 'warnings': [],
            'page_count': 1, 'markdown': text, 'docling_json': {'fixture': True},
            'blocks': [{'block_id': 'text', 'type': 'text', 'content': text, 'page_numbers': [1]}]}), encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr('app.knowledge.worker_process.run_worker', worker)
    monkeypatch.setattr('app.knowledge.document_tools.effective_config', lambda: {'fixture': True})
    raw = _pdf()
    first = upload(skill_client, raw, 'SOP-4.pdf').json()
    assert first['preparation']['status'] == 'executed'
    identifier = first['document_id']
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        output = skill_client.post('/v1/skills/documents.inspect/run', headers=AUTH,
            json={'arguments': {'document_id': identifier}}).json()
        if output['output']['status'] == 'COMPLETE':
            break
        time.sleep(.01)
    assert output['output']['status'] == 'COMPLETE'
    second = upload(skill_client, raw, 'renamed.pdf').json()
    assert second['status'] == 'DUPLICATE'
    assert second['preparation']['output']['job_id'] == first['preparation']['output']['job_id']
    engine = skill_client.app.dependency_overrides[get_knowledge_engine]()
    assert SOPReview(engine).detail(identifier)['approval'] is None


def test_facts_require_current_approval_and_revoke_removes_access(skill_client):
    engine = skill_client.app.dependency_overrides[get_knowledge_engine]()
    identifier = engine.process_knowledge_source('Layanan.txt',
        b'Persyaratan: Surat Contoh untuk layanan warga.')['document_id']
    review = SOPReview(engine)
    detail = review.detail(identifier)
    arguments = {'document_id': identifier, 'version_id': detail['version_id'], 'question': 'Apa persyaratannya?'}
    url = '/v1/skills/sop.facts/run'
    assert skill_client.post(url, headers=AUTH, json={'arguments': arguments}).json()['output']['status'] == 'not_approved'
    _approve_fixture(review, detail)
    result = skill_client.post(url, headers=AUTH, json={'arguments': arguments}).json()
    assert result['output']['status'] == 'answered'
    assert 'Surat Contoh' in result['output']['facts']['quote']
    review.decide(identifier, detail['version_id'], 'revoke', 'fixture', 'Fixture revoke')
    revoked = skill_client.post(url, headers=AUTH, json={'arguments': arguments}).json()
    assert revoked['output']['status'] == 'not_approved'
    assert revoked['output']['facts'] is None


def test_revocation_between_source_validation_and_return_suppresses_facts(skill_client, monkeypatch):
    """Instrument interleaving only; source/access checks and revocation are real."""
    from app.security.v1_knowledge import V1KnowledgeBoundary

    engine = skill_client.app.dependency_overrides[get_knowledge_engine]()
    identifier = engine.process_knowledge_source('Layanan.txt',
        b'Persyaratan: Surat Contoh untuk layanan warga.')['document_id']
    review = SOPReview(engine)
    detail = review.detail(identifier)
    _approve_fixture(review, detail)
    validate = V1KnowledgeBoundary.validate_response
    def validate_then_revoke(boundary, answer, source_versions=None):
        validate(boundary, answer, source_versions)
        review.decide(identifier, detail['version_id'], 'revoke', 'fixture', 'Concurrent fixture revoke')
    monkeypatch.setattr(V1KnowledgeBoundary, 'validate_response', validate_then_revoke)
    result = skill_client.post('/v1/skills/sop.facts/run', headers=AUTH, json={'arguments': {
        'document_id': identifier, 'version_id': detail['version_id'], 'question': 'Apa persyaratannya?'}}).json()
    assert result['status'] == 'executed'
    assert result['output']['status'] == 'not_approved'
    assert result['output']['facts'] is None
