"""NUS-V1-LLAMA-RAG-001 PASAL 7 (Defect J) — the post-router last-resort recovery
must not present a rendered context selection (block dump) as a grounded answer.

Runtime defect: Stage B B02-B05 returned "Konteks bagian terpilih; 342 blok lain
tidak dimuat..." block dumps as grounded=True answers because the recovery took
evidence[0].chunk[:400] verbatim and the grounding guard trivially validated the
source text against itself. A selection rendering is context for the model, not
an answer; the router must abstain instead (Path C).
"""
from test_chat_source_recovery import run_document_chat

DUMP = ('Konteks bagian terpilih; 342 blok lain tidak dimuat. '
        'Jangan menyimpulkan isi bagian yang tidak dimuat.\n\n'
        '[blok table-1; halaman 1]\nPersyaratan: Surat Permohonan.')
SELECTION_METADATA = {
    'docling_blocks': [{'block_id': 'table-1', 'type': 'table',
                        'content': 'Persyaratan: Surat Permohonan.', 'page_numbers': [1]}],
    'omitted_block_ids': ['block-2', 'block-3'],
}


def test_recovery_abstains_instead_of_dumping_context_selection():
    public = run_document_chat('Apa persyaratan SOP ini?', 'Wajib membawa paspor.',
                               pilot=True, source=DUMP, metadata=SELECTION_METADATA)
    assert not public['grounding']['grounded']
    assert public['provider_status'] != 'evidence_fast_path'
    assert 'Konteks bagian terpilih' not in public['response']
    assert '[blok ' not in public['response']
    assert 'belum dapat dipastikan' in public['response']


def test_recovery_still_returns_plain_prose_source():
    # Guard: a genuine prose chunk (no selection rendering) must still recover.
    public = run_document_chat('Apa persyaratan SOP ini?',
                               'Persyaratan: Wajib membawa KTP dan membayar 500 rupiah.',
                               pilot=True)
    assert public['response'] == 'Persyaratan: Pemohon menyerahkan Surat Permohonan kepada petugas.'
    assert public['grounding']['grounded']
    assert public['provider_status'] == 'evidence_fast_path'