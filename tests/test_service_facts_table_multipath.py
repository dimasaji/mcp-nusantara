"""Verified fast path must read an authoritative SOP activity table in the
general multi-document retrieval path (NUS-V1-LLAMA-RAG-001, PASAL 7 Path A).

These tests use the real service_answer_facts/table_facts logic. They are general:
no PIAK-03-only rule, no hardcoded answer — selection is by service match + table
presence, and ambiguous matches must clarify rather than mix services.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.knowledge.grounding import service_answer_facts


def _ev(did, title, chunk, rows, score=1.0):
    return SimpleNamespace(document_id=did, title=title, chunk=chunk, source=chunk,
                           score=score, metadata={'sop_rows': rows})


REQ_ROWS = [
    {'number': 1, 'activity': 'Menyampaikan Surat Permohonan', 'kelengkapan': 'Surat Permohonan', 'page': 1},
    {'number': 2, 'activity': 'Mendisposisi Izin', 'kelengkapan': 'Surat Permohonan', 'page': 1},
]
DUR_ROWS = REQ_ROWS + [
    {'number': 15, 'activity': 'Proses pelayanan permohonan data selesai', 'keterangan': '3 Hari Kerja', 'page': 2},
]
OTHER_ROWS = [{'number': 1, 'activity': 'Mengisi Form Permohonan Data', 'kelengkapan': 'Formulir Permohonan Data', 'page': 1}]


def test_requirements_uses_unique_title_matched_table_in_multi_doc():
    turn = {'facet': 'requirements', 'topic_hint': 'permohonan data pribadi', 'uses_context': False}
    stub = _ev('stub', 'PERMOHONAN DATA PRIBADI', '', [], 1.0)
    real = _ev('real', 'PERMOHONAN DATA PRIBADI',
               'Kelengkapan pemohon pada tahap pengajuan: Surat Permohonan.', REQ_ROWS, 1.0)
    other = _ev('other', 'Dasar Hukum Kualifikasi Pelaksana', 'prose', OTHER_ROWS, 0.8)
    facts = service_answer_facts(turn, [stub, real, other], {})
    assert facts is not None and not facts.get('clarify')
    assert facts['document_id'] == 'real'
    assert facts['facet'] == 'requirements'
    assert 'Surat Permohonan' in facts['quote']
    assert 'Formulir' not in facts['quote']  # never mixes the other service


def test_duration_followup_uses_restored_document_scope():
    turn = {'facet': 'duration', 'topic_hint': '', 'uses_context': True}
    real = _ev('real', 'PERMOHONAN DATA PRIBADI', 'table', DUR_ROWS, 1.0)
    other = _ev('other', 'Dasar Hukum Kualifikasi Pelaksana', 'prose', OTHER_ROWS, 0.8)
    facts = service_answer_facts(turn, [other, real], {'document_id': 'real'})
    assert facts is not None and not facts.get('clarify')
    assert facts['document_id'] == 'real'
    assert '3 Hari Kerja' in facts['fallback']


def test_ambiguous_two_matching_tables_clarifies_not_mixes():
    turn = {'facet': 'requirements', 'topic_hint': 'permohonan data pribadi', 'uses_context': False}
    a = _ev('a', 'PERMOHONAN DATA PRIBADI', 'table', REQ_ROWS, 1.0)
    b = _ev('b', 'PERMOHONAN DATA PRIBADI', 'table', OTHER_ROWS, 0.9)
    facts = service_answer_facts(turn, [a, b], {})
    assert facts is not None and facts.get('clarify')
    assert not facts.get('document_id')