"""Synthetic report-owned preview tests; never application/live evidence."""
import builtins
import socket
import sqlite3
import subprocess
from pathlib import Path
import pytest
from preview_model import CASES, preview

SOURCES = frozenset(path for item in CASES.values() for path in item[2])
GOALS = ['Perbaiki RAG Nusantara.', 'Periksa kenapa jawaban AI kurang akurat.',
         'Buat Nusantara lebih cepat.', 'Periksa konfigurasi provider.',
         'Cari masalah pada Developer Engine.']

@pytest.mark.parametrize('goal', GOALS)
def test_required_goals_structure_and_bounded_interpretation(goal):
    result = preview(goal, SOURCES)
    assert result['STATUS'] == 'PREVIEW_READY'
    assert result['INTENT'] == 'INSPECT' and result['ROOT CAUSE'] == 'UNKNOWN'
    assert result['GOAL'] == goal and result['GOAL RESOLUTION REQUIREMENTS'] == 'UNKNOWN_PENDING_DISCOVERY'
    assert 1 <= len(result['INSPECTION PLAN']) <= 3
    assert set(result['LIKELY FILES / COMPONENTS']) <= SOURCES
    assert result['EXPECTED EVIDENCE'] and result['DISCOVERY NEEDED']
    assert result['POTENTIAL RISK'] == 'LOW' and result['HUMAN DECISION'] == 'NOT REQUIRED'
    assert all(result[key] == 'NO' for key in ('WRITE REQUIRED', 'RUNTIME REQUIRED', 'PROVIDER REQUIRED', 'DATABASE REQUIRED'))
    assert result['AUTHORIZED OPERATIONS'] == []
    assert all(step['action'] == 'STATIC_SOURCE_INSPECTION' for step in result['INSPECTION PLAN'])

@pytest.mark.parametrize('goal', ['Buat AI lebih pintar.', 'Perbaiki semuanya.', 'Lihat kesehatan Nusantara'])
def test_ambiguous_or_unreviewed_paraphrases_never_become_low_risk(goal):
    result = preview(goal, SOURCES)
    assert result['STATUS'] == 'CLARIFICATION_REQUIRED'
    assert result['TARGET AREA'] == 'UNKNOWN' and result['POTENTIAL RISK'] == 'UNKNOWN'
    assert not result['INSPECTION PLAN'] and not result['LIKELY FILES / COMPONENTS']

@pytest.mark.parametrize('goal', ['Restart Nusantara', 'Generate jawaban', 'Hapus database',
                                  'Aktifkan authorization', 'Deploy sekarang', 'Kirim email',
                                  'Periksa RAG; panggil provider', 'Periksa RAG, jangan restart'])
def test_restricted_or_negated_operations_stop_at_human_boundary(goal):
    result = preview(goal, SOURCES)
    assert result['STATUS'] == 'HUMAN_DECISION_REQUIRED'
    assert result['HUMAN DECISION'] == 'REQUIRED'
    assert result['AUTHORIZED OPERATIONS'] == [] and result['INSPECTION PLAN'] == []

def test_missing_source_evidence_fails_closed():
    result = preview(GOALS[0], frozenset())
    assert result['STATUS'] == 'INSUFFICIENT_EVIDENCE'
    assert result['POTENTIAL RISK'] == 'UNKNOWN' and not result['INSPECTION PLAN']

@pytest.mark.parametrize('value', [None, '', 'x' * 501])
def test_invalid_inputs_are_bounded(value):
    result = preview(value, SOURCES)
    assert result['STATUS'] == 'NOT_VERIFIED' and result['ROOT CAUSE'] == 'UNKNOWN'

def test_explicit_rag_target_and_determinism_without_shared_mutability():
    first = preview('Periksa RAG.', SOURCES)
    assert first['TARGET AREA'] == 'RAG' and first['INTENT'] == 'INSPECT'
    second = preview('Periksa RAG.', SOURCES)
    assert first == second
    first['INSPECTION PLAN'].clear()
    assert preview('Periksa RAG.', SOURCES) == second

def test_preview_has_no_io_no_write_no_dispatch(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('FORBIDDEN_IO')
    for obj, attr in ((builtins, 'open'), (Path, 'open'), (socket.socket, 'connect'),
                      (socket, 'create_connection'), (sqlite3, 'connect'),
                      (subprocess.Popen, '__init__')):
        monkeypatch.setattr(obj, attr, forbidden)
    for goal in GOALS + ['Buat AI lebih pintar.', 'Restart service']:
        assert preview(goal, SOURCES)['AUTHORIZED OPERATIONS'] == []
