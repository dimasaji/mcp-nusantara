"""Report-owned finite preview prototype; no integration, executor or I/O.

Only reviewed goal templates are accepted. Unknown paraphrases fail closed.
Requirements describe the proposed static inspection, not eventual remediation.
"""
from copy import deepcopy

CASES = {
    'perbaiki rag nusantara': ('RAG', 'Petakan retrieval dan grounding sebelum menentukan perbaikan.',
        ('app/core/nusantara_config.py', 'app/knowledge/rag.py', 'app/knowledge/grounding.py'),
        ('Baca definisi retrieval configuration tanpa memuat konfigurasi runtime.', 'Trace retrieval menuju evidence pack secara statis.', 'Periksa aturan grounding dan identifikasi kebutuhan diagnosis terisolasi.'),
        ('Hubungan configuration → retrieval → evidence → grounding.', 'Hipotesis yang didukung source; kualitas data aktual tetap UNKNOWN.')),
    'periksa rag': ('RAG', 'Inspeksi statis pipeline RAG; tidak menjalankan retrieval.',
        ('app/knowledge/rag.py', 'app/knowledge/grounding.py'),
        ('Baca pipeline retrieval/evidence.', 'Trace konsumsi evidence pada grounding.'),
        ('Referensi source dan batas dependency SQLite/embedding.',)),
    'periksa kenapa jawaban ai kurang akurat': ('Core', 'Petakan kemungkinan kehilangan evidence; penyebab belum diketahui.',
        ('app/api/routes.py', 'app/knowledge/grounding.py', 'app/devcore/grounding.py'),
        ('Trace pemilihan jalur jawaban dari source API tanpa import aplikasi.', 'Bandingkan aturan grounding RAG dan Developer Engine.', 'Catat alternatif penyebab dan evidence tambahan yang diperlukan.'),
        ('Cabang jawaban dan pemakaian evidence.', 'Dependency RAG/Model; akurasi aktual NOT_VERIFIED.')),
    'buat nusantara lebih cepat': ('Core', 'Petakan timeout dan pekerjaan sinkron; belum menetapkan bottleneck atau target latency.',
        ('app/core/nusantara_config.py', 'app/api/routes.py', 'app/devcore/core.py'),
        ('Bandingkan deklarasi timeout dengan consumer source.', 'Trace pekerjaan blocking dan dependency provider/RAG secara statis.', 'Tentukan desain benchmark sintetis setelah target latency diperjelas.'),
        ('Lokasi timeout dan jalur blocking.', 'Bottleneck serta latency runtime belum diketahui.')),
    'periksa konfigurasi provider': ('Configuration', 'Periksa definisi dan consumer konfigurasi provider tanpa menghubungi provider.',
        ('app/core/nusantara_config.py', 'app/core/config.py', 'app/models/router.py'),
        ('Baca schema provider tanpa membaca credentials/configuration aktif.', 'Trace effective configuration owner dari source.', 'Trace selection/binding provider dan tandai consumer yang belum dikorelasikan.'),
        ('Schema → owner → consumer/Provider dependency.', 'Provider/model aktual NOT_VERIFIED.')),
    'cari masalah pada developer engine': ('Developer Engine', 'Inspeksi goal routing, source reading, dan grounding; tidak mengasumsikan root cause.',
        ('app/devcore/router.py', 'app/devcore/core.py', 'app/devcore/workspace.py', 'app/devcore/grounding.py'),
        ('Trace goal → intent → read-only actions.', 'Periksa workspace/sensitive-file boundary dari source.', 'Trace grounding → answer dan cocokkan dengan tes terisolasi yang sudah ada.'),
        ('Pemetaan jalur handled/unhandled dan boundary.', 'Gap yang dapat direproduksi dengan fixture non-protected.')),
}

def preview(goal, available_sources):
    base = {'GOAL': goal if isinstance(goal, str) and len(goal) <= 500 else '[INVALID_INPUT]',
            'UNDERSTANDING': 'Tujuan perlu diperjelas; tidak ada diagnosis.',
            'TARGET AREA': 'UNKNOWN', 'INTENT': 'AMBIGUOUS', 'CLARIFICATION': 'REQUIRED',
            'DISCOVERY NEEDED': ['Tentukan target, gejala dan kriteria sukses.'],
            'LIKELY FILES / COMPONENTS': [], 'INSPECTION PLAN': [],
            'EXPECTED EVIDENCE': [], 'POTENTIAL RISK': 'UNKNOWN',
            'WRITE REQUIRED': 'UNKNOWN', 'RUNTIME REQUIRED': 'UNKNOWN',
            'PROVIDER REQUIRED': 'UNKNOWN', 'DATABASE REQUIRED': 'UNKNOWN',
            'HUMAN DECISION': 'UNKNOWN', 'NEXT STEP': 'Klarifikasi target dan kriteria sukses.',
            'STATUS': 'CLARIFICATION_REQUIRED',
            'REQUIREMENTS SCOPE': 'PROPOSED_NEXT_STATIC_INSPECTION',
            'GOAL RESOLUTION REQUIREMENTS': 'UNKNOWN_PENDING_DISCOVERY',
            'AUTHORIZED OPERATIONS': [], 'ROOT CAUSE': 'UNKNOWN',
            'BOUNDARIES': ['NO WRITE', 'NO RUNTIME', 'NO PROVIDER', 'NO DATABASE ACCESS',
                           'NO AUTHORIZATION', 'NO DEPLOYMENT', 'NO EXTERNAL OPERATION']}
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 500:
        base['STATUS'] = 'NOT_VERIFIED'
        base['NEXT STEP'] = 'Berikan goal teks bounded yang valid.'
        return base
    # Deliberately conservative: even negated risky terms require clarification.
    low = ' '.join(goal.lower().strip().rstrip('.').split())
    risky = ('restart', 'reload', 'generation', 'generate', 'health check', 'list-model',
             'hapus database', 'ubah database', 'sqlite', 'wal', 'shm', 'otorisasi',
             'authorization', 'deploy', 'kirim email', 'panggil provider', 'ubah source')
    if any(term in low for term in risky):
        base.update({'STATUS': 'HUMAN_DECISION_REQUIRED', 'INTENT': 'RESTRICTED_OR_UNCLEAR_OPERATION',
                     'HUMAN DECISION': 'REQUIRED', 'POTENTIAL RISK': 'UNKNOWN',
                     'NEXT STEP': 'Pisahkan inspeksi statis dari operasi berisiko; keputusan manusia diperlukan.'})
        return base
    if low not in CASES:
        return base
    area, understanding, paths, steps, evidence = CASES[low]
    if not isinstance(available_sources, frozenset):
        base['STATUS'] = 'NOT_VERIFIED'
        return base
    if not set(paths).issubset(available_sources):
        base.update({'STATUS': 'INSUFFICIENT_EVIDENCE', 'TARGET AREA': area,
                     'NEXT STEP': 'Pastikan referensi source non-protected tersedia sebelum inspeksi.'})
        return base
    base.update({'UNDERSTANDING': understanding, 'TARGET AREA': area, 'INTENT': 'INSPECT',
                 'CLARIFICATION': 'NOT REQUIRED FOR STATIC INSPECTION',
                 'DISCOVERY NEEDED': list(steps), 'LIKELY FILES / COMPONENTS': list(paths),
                 'INSPECTION PLAN': [{'action': 'STATIC_SOURCE_INSPECTION', 'step': step} for step in steps],
                 'EXPECTED EVIDENCE': list(evidence), 'POTENTIAL RISK': 'LOW',
                 'HUMAN DECISION': 'NOT REQUIRED', 'STATUS': 'PREVIEW_READY',
                 'NEXT STEP': 'Tinjau preview, kemudian lakukan hanya inspeksi source yang disebutkan; jangan import aplikasi.'})
    for key in ('WRITE REQUIRED', 'RUNTIME REQUIRED', 'PROVIDER REQUIRED', 'DATABASE REQUIRED'):
        base[key] = 'NO'
    return deepcopy(base)
