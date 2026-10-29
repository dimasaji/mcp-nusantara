"""Golden dataset tests for SOP chat (PIAK-03). These guard against regression
in grounded answers for the verified SOP. Each case asserts the answer contains
the expected fact and is grounded."""
import asyncio
from types import SimpleNamespace
import pytest
from test_v1_langgraph import fixture
from app.memory.engine import MemoryEngine


def execute(parts, question, session='golden-session', **extra):
    core = asyncio.run(parts[1].execute_v1(SimpleNamespace(
        user_input=question, session_id=session, model=None, stream=False, **extra), **parts[2]))
    return parts[3](core.payload, intent_name=core.intent_name)


GOLDEN = [
    ('Apa persyaratan permohonan data pribadi?', 'surat permohonan', True),
    ('Berapa lama waktu penyelesaiannya?', '3 hari kerja', True),
    ('Apakah SOP ini menyebutkan nomor WhatsApp petugas?', 'tidak menyebutkan', True),
]


def test_golden_sop_chat():
    from test_v1_service_dialogue import setup, SOURCE
    parts = setup(answer='Silakan siapkan Surat Permohonan.')
    item = parts[2]['knowledge'].search_knowledge('fixture')[0]
    item.metadata = {
        'sop_rows': [{'number': 1, 'activity': 'Menyampaikan Surat Permohonan',
                      'kelengkapan': 'Surat Permohonan', 'keterangan': '', 'page': 1}],
        'full_document_text': SOURCE,
    }
    answers = {
        'Apa persyaratan permohonan data pribadi?': 'Silakan siapkan Surat Permohonan.',
        'Berapa lama waktu penyelesaiannya?': 'Menurut SOP: 3 Hari Kerja.',
        'Apakah SOP ini menyebutkan nomor WhatsApp petugas?': 'SOP ini tidak menyebutkan nomor WhatsApp petugas.',
    }
    for q, expected, grounded in GOLDEN:
        parts[4].answer = answers[q]
        result = execute(parts, q, document_ids=['service-private'], sop_version='a'*64)
        assert result['grounding']['grounded'] == grounded, (q, result)
        assert expected in result['response'].lower(), (q, result['response'])