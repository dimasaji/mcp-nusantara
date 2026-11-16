"""Enhanced Golden Set generator for Nusantara V1 SOPs.

Generates structured golden sets with:
- document_id and version_id binding
- expected citation pages
- ground truth placeholders
- out-of-scope and no-answer questions
- multi-step questions
"""
import sys, json, os, hashlib
from datetime import datetime, timezone

def generate_enhanced(sop_data, output_path, doc_id=None, version_id=None):
    title = sop_data.get('title', 'SOP')
    doc_id = doc_id or sop_data.get('id_sop', '')
    version_id = version_id or sop_data.get('version_id', '')

    questions = []

    # Tier A: Normal questions (5)
    tier_a = [
        {'id': 'G-01', 'q': 'Apa persyaratan %s?' % title, 'type': 'requirements',
         'expected_answer': 'Lihat bagian persyaratan pada dokumen.',
         'expected_citation_pages': [1], 'must_abstain': False},
        {'id': 'G-02', 'q': 'Bagaimana prosedur %s?' % title, 'type': 'procedure',
         'expected_answer': 'Lihat bagian prosedur pada dokumen.',
         'expected_citation_pages': [1], 'must_abstain': False},
        {'id': 'G-03', 'q': 'Berapa lama proses %s?' % title, 'type': 'time',
         'expected_answer': 'Lihat bagian waktu pada dokumen.',
         'expected_citation_pages': [1], 'must_abstain': False},
        {'id': 'G-04', 'q': 'Berapa biaya %s?' % title, 'type': 'cost',
         'expected_answer': 'Lihat bagian biaya pada dokumen.',
         'expected_citation_pages': [1], 'must_abstain': False},
        {'id': 'G-05', 'q': 'Apa dasar hukum %s?' % title, 'type': 'legal',
         'expected_answer': 'Lihat bagian dasar hukum pada dokumen.',
         'expected_citation_pages': [1], 'must_abstain': False},
    ]

    # Tier B: Ambiguous questions (2)
    tier_b = [
        {'id': 'G-06', 'q': 'syarat %s' % title.lower(), 'type': 'typo',
         'expected_answer': 'Typo/bahasa sehari-hari, jawaban sama dengan G-01.',
         'expected_citation_pages': [1], 'must_abstain': False},
        {'id': 'G-07', 'q': 'kondisi khusus %s' % title, 'type': 'special',
         'expected_answer': 'Lihat bagian kondisi khusus pada dokumen.',
         'expected_citation_pages': [1], 'must_abstain': False},
    ]

    # Tier C: Out-of-scope and no-answer (3)
    tier_c = [
        {'id': 'G-08', 'q': 'Cuaca hari ini?', 'type': 'out_of_scope',
         'expected_answer': 'Informasi tidak tersedia dalam SOP.',
         'expected_citation_pages': [], 'must_abstain': True},
        {'id': 'G-09', 'q': 'Berapa denda keterlambatan?', 'type': 'no_answer',
         'expected_answer': 'Informasi tidak tersedia dalam SOP.',
         'expected_citation_pages': [], 'must_abstain': True},
        {'id': 'G-10', 'q': 'Siapa penanggung jawab layanan?', 'type': 'no_answer',
         'expected_answer': 'Informasi tidak tersedia dalam SOP.',
         'expected_citation_pages': [], 'must_abstain': True},
    ]

    # Tier D: Multi-step (1)
    tier_d = [
        {'id': 'G-11', 'q': 'Bandungkan persyaratan dan prosedur %s' % title, 'type': 'multi_step',
         'expected_answer': 'Gabungan persyaratan dan prosedur dari dokumen.',
         'expected_citation_pages': [1], 'must_abstain': False},
    ]

    golden = {
        'sop_id': doc_id,
        'document_id': doc_id,
        'version_id': version_id,
        'title': title,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'tier_a': tier_a,
        'tier_b': tier_b,
        'tier_c': tier_c,
        'tier_d': tier_d,
        'total_questions': len(tier_a) + len(tier_b) + len(tier_c) + len(tier_d),
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    json.dump(golden, open(output_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print('Golden set saved:', output_path)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: generate_golden_set_enhanced.py <sop_json> <output_json> [doc_id] [version_id]')
        sys.exit(1)
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    doc_id = sys.argv[3] if len(sys.argv) > 3 else None
    version_id = sys.argv[4] if len(sys.argv) > 4 else None
    generate_enhanced(data, sys.argv[2], doc_id, version_id)
