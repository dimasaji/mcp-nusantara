"""Actual DevCore previews over empty temporary workspaces, no live dependencies."""
import asyncio
import json

import pytest

from app.devcore import DevCore, plan

GOALS = [
    ('Perbaiki RAG Nusantara.', 'RAG'),
    ('Periksa kenapa jawaban AI kurang akurat.', 'Core'),
    ('Buat Nusantara lebih cepat.', 'Core'),
    ('Periksa konfigurasi provider.', 'Configuration'),
    ('Cari masalah pada Developer Engine.', 'Developer Engine'),
]


def no_operation(*args, **kwargs):
    raise AssertionError('Preview must not inspect or dispatch')


def core_without_execution(tmp_path, monkeypatch):
    core = DevCore(str(tmp_path), generate=no_operation, backend=object())
    monkeypatch.setattr(core, '_call', no_operation)
    monkeypatch.setattr(core, '_resolve_reads', no_operation)
    monkeypatch.setattr(core.registry, 'execute', no_operation)
    return core


@pytest.mark.parametrize('goal,target', GOALS)
def test_supported_goal_through_real_devcore_has_terminal_preview(tmp_path, monkeypatch, goal, target):
    core = core_without_execution(tmp_path, monkeypatch)
    result = asyncio.run(core.handle(goal, 'synthetic-session'))
    p = result['inspection_preview']
    assert result['handled'] and result['intent'] == 'inspection_preview'
    assert p['goal'] == goal and p['target'] == target and p['intent'] == 'INSPECT'
    assert p['status'] == 'PREVIEW_READY' and p['root_cause'] == 'UNKNOWN'
    assert p['file_evidence'] == 'CANDIDATES_NOT_INSPECTED'
    assert p['goal_resolution_requirements'] == 'UNKNOWN_PENDING_DISCOVERY'
    assert p['requirements_scope'] == 'PROPOSED_NEXT_STATIC_INSPECTION'
    assert set(p) >= {'goal', 'understanding', 'intent', 'target', 'discovery', 'likely_files',
                      'plan', 'expected_evidence', 'risk', 'write_required', 'runtime_required',
                      'provider_required', 'database_required', 'human_decision', 'next_step'}
    assert p['plan'] and p['expected_evidence'] and p['discovery']
    assert all(step['action'] == 'STATIC_SOURCE_INSPECTION' for step in p['plan'])
    assert all(p[key] == 'NO' for key in ('write_required', 'runtime_required', 'provider_required', 'database_required'))
    assert p['risk'] == 'LOW' and p['human_decision'] == 'NOT REQUIRED'
    assert p['authorized_operations'] == []
    assert result['tool'] == {'used': False, 'name': None, 'result': None, 'calls': []}
    assert result['verification'] == {'status': 'not_applicable', 'violations': []}
    assert json.loads(result['answer']) == p
    assert list(tmp_path.iterdir()) == []
    assert core.audit.verify()
    audit = json.dumps(core.audit.entries())
    assert 'NOT_INVOKED' in audit and 'dev.request' in audit
    assert goal not in audit and 'STATIC_SOURCE_INSPECTION' not in audit


@pytest.mark.parametrize('goal', ['Buat AI lebih pintar', 'Perbaiki RAG', 'Cari masalah pada AI'])
def test_unknown_engineering_goal_clarifies_without_generic_find(tmp_path, monkeypatch, goal):
    result = asyncio.run(core_without_execution(tmp_path, monkeypatch).handle(goal))
    p = result['inspection_preview']
    assert p['status'] == 'CLARIFICATION_REQUIRED'
    assert p['intent'] == 'AMBIGUOUS' and p['target'] == 'UNKNOWN'
    assert p['risk'] == 'UNKNOWN' and p['plan'] == [] and p['likely_files'] == []
    assert not result['tool']['used']


@pytest.mark.parametrize('goal', ['Restart Nusantara', 'Deploy Nusantara', 'Activate runtime',
    'Delete database', 'Reset database', 'Authorize runtime', 'Production mutation',
    'Database mutation', 'Perbaiki RAG Nusantara; generate jawaban',
    'Baca app/main.py lalu restart Nusantara', 'Hapus app/main.py dan deploy',
    'Delete database app/schema.sql',
    'Delete app/main.py',
    'Periksa konfigurasi provider, jangan restart'])
def test_restricted_goals_and_mixed_source_requests_fail_closed(tmp_path, monkeypatch, goal):
    result = asyncio.run(core_without_execution(tmp_path, monkeypatch).handle(goal))
    p = result['inspection_preview']
    assert p['status'] == 'HUMAN_DECISION_REQUIRED' and p['human_decision'] == 'REQUIRED'
    assert p['risk'] == 'HIGH' and p['plan'] == [] and p['authorized_operations'] == []
    assert result['modify_blocked'] and not result['tool']['used']
    assert p['root_cause'] == 'UNKNOWN'


@pytest.mark.parametrize('goal,key', [('Restart Nusantara', 'runtime_required'),
    ('Generate jawaban', 'provider_required'), ('Hapus database', 'database_required')])
def test_operation_requirements_are_not_misclassified_as_static(tmp_path, monkeypatch, goal, key):
    p = asyncio.run(core_without_execution(tmp_path, monkeypatch).handle(goal))['inspection_preview']
    assert p[key] == 'YES' and p['requirements_scope'] == 'REQUESTED_OPERATION_NOT_AUTHORIZED'


def test_normalization_and_response_mutation_do_not_change_future_plans(tmp_path, monkeypatch):
    core = core_without_execution(tmp_path, monkeypatch)
    goal = '  Perbaiki   RAG Nusantara.  '
    first = asyncio.run(core.handle(goal))
    assert first['original_text'] == goal
    assert first['inspection_preview']['goal'] == goal
    assert first['inspection_preview']['status'] == 'PREVIEW_READY'
    first['inspection_preview']['plan'].clear()
    assert asyncio.run(core.handle(goal))['inspection_preview']['plan']


def test_existing_router_modes_are_not_replaced():
    for text, intent in [('Baca app/main.py', 'read_file'), ('Cari file settings', 'find_file'),
                         ('Tampilkan isi folder app/', 'list_directory'),
                         ('Ubah app/main.py dan hapus semua isinya', 'read_file')]:
        p = plan(text)
        assert p.intent == intent and p.inspection is None and p.actions
    for text in ('halo', 'daftar belanja saya apa saja', 'tambahkan tanggal hari ini'):
        assert not plan(text).handled
