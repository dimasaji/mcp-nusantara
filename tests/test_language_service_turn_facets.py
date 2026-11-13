"""Defect E — general facet/context recognition for short follow-ups.

NUS-V1-LLAMA-RAG-001 PASAL 5 (Context Resolver) + PASAL 7 (Answer Router).
These tests pin GENERAL behaviour, not a PIAK-03-only rule: the table fixture
uses a neutral service so the same logic must work for any approved SOP.
"""
from types import SimpleNamespace

import pytest

from app.language.engine import LanguageEngine
from app.knowledge.grounding import EvidenceGroundingGuard, service_answer_facts


TOPIC = 'SOP LAYANAN CONTOH'
DOC_ID = 'DOC-SHA256-generic-example'

# A neutral activity table mirroring the validated SOP extraction shape.
ROWS = [
    {'number': 1, 'activity': 'Menyampaikan Surat Permohonan', 'kelengkapan': 'Surat Permohonan',
     'keterangan': '', 'page': 1},
    {'number': 2, 'activity': 'Memverifikasi data', 'kelengkapan': 'Surat Permohonan',
     'keterangan': '30 menit', 'page': 1},
    {'number': 3, 'activity': 'Proses pelayanan selesai', 'kelengkapan': '',
     'keterangan': '3 Hari Kerja', 'page': 2},
]
FULL_NO_FEE = ('SOP Layanan Contoh. Kelengkapan: Surat Permohonan. '
               'Proses pelayanan selesai 3 Hari Kerja.')


def table_item(full=FULL_NO_FEE, rows=ROWS):
    return SimpleNamespace(document_id=DOC_ID, title=TOPIC, source=full, chunk=full,
                           score=.9, metadata={'sop_rows': rows, 'full_document_text': full})


def previous():
    return {'topic': TOPIC, 'document_id': DOC_ID, 'title': TOPIC}


# ---------------------------------------------------------------------------
# A. Facet recognition (PASAL 5: recognize short follow-ups, restore context)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('question,facet', [
    ('Biayanya?', 'cost'),
    ('Berapa biayanya?', 'cost'),
    ('Siapa yang menangani?', 'who'),
    ('Siapa pelaksananya?', 'who'),
    ('Berapa hari kerjanya?', 'duration'),
    ('Berapa hari?', 'duration'),
])
def test_short_followup_facets_restore_context(question, facet):
    turn = LanguageEngine.service_turn(question, TOPIC)
    assert turn['facet'] == facet
    assert turn['topic_hint'] == ''
    assert turn['uses_context'] is True
    assert turn['topic'] == TOPIC


@pytest.mark.parametrize('question,facet', [
    ('Berapa lama?', 'duration'),
    ('Bagaimana prosedurnya?', 'procedure'),
    ('Apa syaratnya?', 'requirements'),
    ('Bisa online?', 'channel'),
    ('Bagaimana cara kerja layanan ini?', 'procedure'),
])
def test_existing_facets_and_cara_kerja_are_unchanged(question, facet):
    turn = LanguageEngine.service_turn(question, TOPIC)
    assert turn['facet'] == facet


# ---------------------------------------------------------------------------
# B. Cost — Path A facet, Path C abstention when the source lists no fee
#    (PASAL 7: never conclude "free" from an empty cost column)
# ---------------------------------------------------------------------------
def test_cost_followup_abstains_with_citation_when_no_fee_in_source():
    turn = LanguageEngine.service_turn('Biayanya?', TOPIC)
    facts = service_answer_facts(turn, [table_item()], previous())
    assert facts is not None and not facts.get('clarify')
    assert facts['facet'] == 'cost'
    assert facts['unknown'] is True
    assert facts['document_id'] == DOC_ID
    assert 'biaya' in facts['fallback'].casefold()
    assert facts['pages'] == [1, 2]
    guard = EvidenceGroundingGuard()
    assert guard.validate_service_rewrite(facts['fallback'], facts).grounded


def test_cost_is_not_abstained_when_source_states_a_fee():
    full = FULL_NO_FEE + ' Biaya layanan Rp 10.000.'
    turn = LanguageEngine.service_turn('Biayanya?', TOPIC)
    facts = service_answer_facts(turn, [table_item(full=full)], previous())
    # An explicit fee exists, so the absence abstention must NOT fire.
    assert facts is None or not (facts.get('unknown') and 'belum tercantum' in facts.get('fallback', ''))


# ---------------------------------------------------------------------------
# C. Who — restore context but never invent an actor from swimlane position.
#    A table SOP with no extractable actor must abstain cleanly WITH a citation
#    (Path C), not dump raw table-context scaffolding or fabricate a name.
# ---------------------------------------------------------------------------
def test_who_followup_abstains_with_citation_when_no_actor_in_table():
    turn = LanguageEngine.service_turn('Siapa yang menangani?', TOPIC)
    facts = service_answer_facts(turn, [table_item()], previous())
    assert facts is not None and not facts.get('clarify')
    assert facts['facet'] == 'who'
    assert facts['unknown'] is True
    assert facts['document_id'] == DOC_ID
    assert 'pelaksana' in facts['fallback'].casefold()
    assert facts['pages'] == [1, 2]
    assert EvidenceGroundingGuard().validate_service_rewrite(facts['fallback'], facts).grounded


# ---------------------------------------------------------------------------
# D. Duration phrasing still reaches the verified table fast path
# ---------------------------------------------------------------------------
def test_duration_phrasing_uses_verified_table_cell():
    turn = LanguageEngine.service_turn('Berapa hari kerjanya?', TOPIC)
    facts = service_answer_facts(turn, [table_item()], previous())
    assert facts is not None and not facts.get('clarify')
    assert facts['facet'] == 'duration'
    assert facts['unknown'] is False
    assert '3 Hari Kerja' in facts['fallback']
    assert facts['pages'] == [2]
    assert EvidenceGroundingGuard().validate_service_rewrite(facts['fallback'], facts).grounded