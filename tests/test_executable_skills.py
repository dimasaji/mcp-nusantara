"""Core contracts and durable queue tests; external worker is a fixture."""
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import BaseModel, ConfigDict
from test_review_publication_v1 import _pdf
from test_sop_review import engine_at

from app.approval import ApprovalQueue, AuditTrail
from app.governance.tools import GovernedToolRegistry
from app.knowledge.document_tools import DocumentTools
from app.knowledge.sop_review import SOPReview
from app.skills.composition import OPERATOR_PERMISSIONS
from app.skills.runtime import SkillDefinition, SkillRuntime


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    value: str


class Output(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    result: str


def invoke(engine, name, arguments):
    return engine.skills.execute(name, arguments, role='operator',
        permissions=set(OPERATOR_PERMISSIONS), requested_by='fixture')


def test_non_sop_registration_and_typed_execution(tmp_path):
    runtime = SkillRuntime(GovernedToolRegistry(ApprovalQueue(AuditTrail(tmp_path / 'audit.jsonl'))))
    calls = []
    runtime.register(SkillDefinition('research.echo', 'research', '1', 'Fixture', Input, Output),
                     lambda data: calls.append(data.value) or {'result': data.value})
    context = {'role': 'user', 'permissions': set(), 'requested_by': 'fixture'}
    catalog = runtime.catalog(role='user', permissions=set())
    assert catalog[0]['domain'] == 'research'
    assert catalog[0]['output_schema']['properties']['result']['type'] == 'string'
    assert runtime.execute('research.echo', {'value': 12, 'role': 'operator'}, **context).status == 'invalid_input'
    assert calls == []
    assert runtime.execute('research.echo', {'value': 'article'}, **context).output == {'result': 'article'}
    assert runtime.execute('unknown', {}, **context).status == 'unknown_tool'
    runtime.register(SkillDefinition('research.bad', 'research', '1', 'Fixture', Input, Output),
                     lambda data: {'result': 12})
    assert runtime.execute('research.bad', {'value': 'article'}, **context).status == 'failed'


@pytest.fixture
def worker_fixture(monkeypatch):
    calls, started, release = [], threading.Event(), threading.Event()
    def worker(args, **kwargs):
        calls.append(args[-2])
        started.set()
        assert release.wait(5)
        text = 'Persyaratan: Surat Contoh untuk layanan warga.'
        Path(args[-1]).write_text(json.dumps({'status': 'COMPLETE', 'warnings': [],
            'page_count': 1, 'markdown': text, 'docling_json': {'fixture': True},
            'blocks': [{'block_id': 'text', 'type': 'text', 'content': text, 'page_numbers': [1]}]}), encoding='utf-8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr('app.knowledge.worker_process.run_worker', worker)
    monkeypatch.setattr('app.knowledge.document_tools.effective_config', lambda: {'fixture': True})
    yield calls, started, release
    release.set()


def wait_status(tools, identifier):
    deadline = time.monotonic() + 5
    while tools.status(identifier)['status'] in {'QUEUED', 'PROCESSING'} and time.monotonic() < deadline:
        time.sleep(.01)
    return tools.status(identifier)['status']


def test_two_documents_queue_without_operator_retry(tmp_path, worker_fixture):
    calls, started, release = worker_fixture
    engine = engine_at(tmp_path / 'chat.db')
    ids = [engine.process_knowledge_source(f'SOP-{i}.pdf', _pdf() + f'\n%{i}'.encode())['document_id'] for i in [4, 5]]
    review = SOPReview(engine)
    try:
        outputs = []
        for identifier in ids:
            outcome = invoke(engine, 'documents.prepare', {'document_id': identifier,
                'version_id': review.detail(identifier)['version_id']})
            assert outcome.status == 'executed', outcome.error
            outputs.append(outcome.output)
            assert started.wait(2)
        assert outputs[1]['status'] == 'QUEUED'
    finally:
        release.set()
    tools = DocumentTools(engine, operator=True)
    assert [wait_status(tools, i) for i in ids] == ['COMPLETE', 'COMPLETE']
    assert len(calls) == 2
    assert all(review.detail(i)['approval'] is None for i in ids)


def test_waiting_request_survives_storage_reopen_without_duplicate_work(tmp_path, worker_fixture):
    calls, _, release = worker_fixture
    release.set()
    db = tmp_path / 'chat.db'
    engine = engine_at(db)
    identifier = engine.process_knowledge_source('SOP.pdf', _pdf())['document_id']
    version = SOPReview(engine).detail(identifier)['version_id']
    queued = DocumentTools(engine, operator=True).enqueue(identifier, version)
    assert calls == []
    tools = DocumentTools(engine_at(db), operator=True)
    assert tools.resume_queued() == 1
    tools.resume_queued()
    assert wait_status(tools, identifier) == 'COMPLETE'
    assert tools.status(identifier)['job_id'] == queued['job_id']
    assert len(calls) == 1


def test_changed_source_waiting_behind_running_job_is_rejected(tmp_path, worker_fixture):
    calls, started, release = worker_fixture
    engine = engine_at(tmp_path / 'chat.db')
    review = SOPReview(engine)
    tools = DocumentTools(engine, operator=True)
    ids = [engine.process_knowledge_source(f'SOP-{i}.pdf', _pdf() + f'\n%{i}'.encode())['document_id'] for i in [4, 5]]
    try:
        for identifier in ids:
            tools.process(identifier, review.detail(identifier)['version_id'])
        assert started.wait(2)
        path, raw, _ = review.source(ids[1])
        path.write_bytes(raw + b'\n%changed-while-queued')
    finally:
        release.set()
    assert wait_status(tools, ids[0]) == 'COMPLETE'
    assert wait_status(tools, ids[1]) == 'FAILED'
    assert len(calls) == 1
