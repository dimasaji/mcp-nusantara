"""Deterministic goal previews. Planning never reads files or grants authority."""
from __future__ import annotations

import re
from typing import Any

# Reviewed starting points, not claims that these files exist in every workspace.
_GOALS = {
    'perbaiki rag nusantara': ('RAG', 'Petakan retrieval dan grounding sebelum menentukan perbaikan.',
        ('app/core/nusantara_config.py', 'app/knowledge/rag.py', 'app/knowledge/grounding.py'),
        ('Periksa schema retrieval dari source tanpa memuat konfigurasi aktif.',
         'Trace retrieval menuju evidence pack secara statis.',
         'Periksa aturan grounding serta batas SQLite/embedding.'),
        ('Referensi configuration → retrieval → evidence → grounding.',)),
    'periksa kenapa jawaban ai kurang akurat': ('Core', 'Petakan jalur jawaban dan evidence; penyebab belum diketahui.',
        ('app/api/routes.py', 'app/knowledge/grounding.py', 'app/devcore/grounding.py'),
        ('Trace cabang jawaban dari source tanpa import aplikasi.',
         'Bandingkan aturan grounding RAG dan Developer Engine.',
         'Catat hipotesis dan kebutuhan evidence tambahan.'),
        ('Cabang jawaban, penggunaan evidence dan dependency RAG/Model.',)),
    'buat nusantara lebih cepat': ('Core', 'Petakan timeout dan pekerjaan blocking; bottleneck belum diketahui.',
        ('app/core/nusantara_config.py', 'app/api/routes.py', 'app/devcore/core.py'),
        ('Bandingkan deklarasi timeout dengan consumer source.',
         'Trace pekerjaan blocking dan dependency provider/RAG secara statis.',
         'Perjelas target latency sebelum merancang benchmark sintetis.'),
        ('Lokasi timeout dan jalur blocking; tidak ada pengukuran runtime.',)),
    'periksa konfigurasi provider': ('Configuration', 'Periksa definisi dan consumer konfigurasi tanpa menghubungi provider.',
        ('app/core/nusantara_config.py', 'app/core/config.py', 'app/models/router.py'),
        ('Baca schema provider tanpa credentials atau konfigurasi aktif.',
         'Trace effective configuration owner dari source.',
         'Trace selection/binding dan tandai consumer yang belum dikorelasikan.'),
        ('Schema → owner → consumer, dependency Provider.',)),
    'cari masalah pada developer engine': ('Developer Engine', 'Trace routing, batas workspace dan grounding tanpa asumsi root cause.',
        ('app/devcore/router.py', 'app/devcore/core.py', 'app/devcore/workspace.py', 'app/devcore/grounding.py'),
        ('Trace goal → intent → read-only actions.',
         'Periksa batas workspace/sensitive-file dari source.',
         'Trace grounding → answer dan cocokkan dengan tes yang tersedia.'),
        ('Jalur handled/unhandled dan kandidat gap untuk fixture terisolasi.',)),
}
_RESTRICTED = re.compile(
    r'\b(restart|reload|deploy(?:ment)?|activate|aktifkan|delete|reset|authorize|otorisasi|'
    r'authorization|hapus|production mutation|database mutation|ubah database|'
    r'generation|generate|health check|list[- ]models?|embedding|index rebuild|'
    r'panggil provider|jalankan model|kirim email|service start|service stop)\b', re.I)
_ENGINEERING = re.compile(r'\b(rag|nusantara|ai|provider|model|konfigurasi|developer engine|'
                          r'developer|core|runtime|database|control plane)\b', re.I)


def inspection_preview(text: str, *, explicit_source: bool = False) -> dict[str, Any] | None:
    """Return a bounded preview or None to preserve existing source/chat routing.

    Explicit file inspection retains its existing read-only modification refusal.
    Lifecycle/provider/authority operations remain blocked even with file refs.
    Unknown goal wording is never coerced into a supported template.
    """
    normalized = ' '.join(text.split()).strip().rstrip('.').lower()
    restricted = _RESTRICTED.search(normalized)
    # Preserve existing Indonesian source-review/refusal; explicit "delete" stops.
    if explicit_source and (not restricted or restricted.group(0).lower() == 'hapus'):
        # Other dangerous terms in the same request must not escape this check.
        remaining = [m.group(0).lower() for m in _RESTRICTED.finditer(normalized)]
        protected_operation = re.search(r'\b(database|sqlite|rag|index|wal|shm)\b', normalized)
        if not protected_operation and all(term == 'hapus' for term in remaining):
            return None
    if not restricted and (explicit_source or not _ENGINEERING.search(normalized)):
        return None
    result = {
        'goal': text, 'understanding': 'Target, gejala dan kriteria sukses perlu diperjelas.',
        'intent': 'AMBIGUOUS', 'target': 'UNKNOWN',
        'discovery': ['Tentukan target dan kriteria sukses.'], 'likely_files': [], 'plan': [],
        'expected_evidence': [], 'risk': 'UNKNOWN', 'write_required': 'UNKNOWN',
        'runtime_required': 'UNKNOWN', 'provider_required': 'UNKNOWN', 'database_required': 'UNKNOWN',
        'human_decision': 'UNKNOWN', 'next_step': 'Klarifikasi tujuan engineering.',
        'status': 'CLARIFICATION_REQUIRED', 'root_cause': 'UNKNOWN',
        'requirements_scope': 'PROPOSED_NEXT_STATIC_INSPECTION',
        'goal_resolution_requirements': 'UNKNOWN_PENDING_DISCOVERY',
        'file_evidence': 'CANDIDATES_NOT_INSPECTED', 'authorized_operations': [],
        'boundaries': ['NO WRITE', 'NO RUNTIME', 'NO PROVIDER', 'NO DATABASE ACCESS',
                       'NO AUTHORIZATION', 'NO DEPLOYMENT', 'NO EXTERNAL OPERATION']}
    if restricted:
        result.update(intent='RESTRICTED_OPERATION', status='HUMAN_DECISION_REQUIRED',
                      human_decision='REQUIRED', risk='HIGH',
                      requirements_scope='REQUESTED_OPERATION_NOT_AUTHORIZED',
                      next_step='Pisahkan inspeksi statis dari operasi berisiko; keputusan manusia diperlukan.')
        terms = {m.group(0).lower() for m in _RESTRICTED.finditer(normalized)}
        if terms & {'restart', 'reload', 'activate', 'aktifkan', 'service start', 'service stop'}:
            result['runtime_required'] = 'YES'
        if terms & {'generation', 'generate', 'embedding', 'panggil provider', 'jalankan model',
                    'health check', 'list-model', 'list-models', 'list model', 'list models'}:
            result['provider_required'] = 'YES'
            result['runtime_required'] = 'YES'
        if terms & {'database mutation', 'ubah database', 'index rebuild'} or (
                terms & {'hapus', 'delete', 'reset'} and re.search(r'\b(database|rag|index|wal|shm)\b', normalized)):
            result['database_required'] = 'YES'
            result['write_required'] = 'YES'
        return result
    if normalized not in _GOALS:
        return result
    target, understanding, files, steps, evidence = _GOALS[normalized]
    result.update(understanding=understanding, intent='INSPECT', target=target,
                  discovery=list(steps), likely_files=list(files),
                  plan=[{'action': 'STATIC_SOURCE_INSPECTION', 'step': step} for step in steps],
                  expected_evidence=list(evidence), risk='LOW', human_decision='NOT REQUIRED',
                  status='PREVIEW_READY', next_step='Tinjau preview; konfirmasi kandidat source sebelum inspeksi terpisah.')
    for name in ('write_required', 'runtime_required', 'provider_required', 'database_required'):
        result[name] = 'NO'
    return result
