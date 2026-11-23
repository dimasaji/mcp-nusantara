"""Versioned explanation of the existing controlled-work approval protocol.

This describes the protocol; it is not an execution receipt or authorization.
"""
from copy import deepcopy

APPROVAL_VALIDITY_SECONDS = 3600

_CONTRACT = {
    'version': 'nusantara.controlled-work.v1',
    'scope': 'CONTROLLED_FILE_WRITE',
    'source': 'Developer Core / change_plan.json',
    'approval_validity_seconds': APPROVAL_VALIDITY_SECONDS,
    'approval_executes_work': False,
    'steps': [
        {'id': 'PREPARE', 'label': 'Siapkan rencana', 'actor': 'Operasi developer',
         'description': 'Siapkan tujuan, calon berkas, risiko, pengujian, dan cara pemulihan.'},
        {'id': 'VERIFY', 'label': 'Periksa bukti', 'actor': 'Sistem',
         'description': 'Periksa hasil pengujian dan kecocokan bukti dengan source saat ini.'},
        {'id': 'DECIDE', 'label': 'Keputusan operator', 'actor': 'Operator terautentikasi',
         'description': 'Catat Setujui, Tolak, atau Tunda untuk paket bukti dan versi rencana ini.'},
        {'id': 'AUTHORIZE', 'label': 'Periksa izin', 'actor': 'Backend',
         'description': 'Periksa kembali bukti, keputusan terbaru, versi rencana, cakupan, masa berlaku, dan penggunaan izin.'},
        {'id': 'EXECUTE', 'label': 'Jalankan', 'actor': 'Eksekutor terkontrol',
         'description': 'Jalankan hanya melalui tindakan terpisah setelah seluruh pemeriksaan izin terpenuhi.'},
        {'id': 'AUDIT', 'label': 'Catat hasil', 'actor': 'Sistem audit',
         'description': 'Simpan keputusan dan hasil percobaan; bedakan mulai, berhasil, dan terhalang.'},
    ],
    'decisions': [
        {'code': 'PASS', 'label': 'Setujui',
         'description': 'Terima rencana yang ditinjau. Eksekusi tetap memerlukan tindakan Jalankan dan pemeriksaan ulang backend.'},
        {'code': 'FAIL', 'label': 'Tolak',
         'description': 'Tolak rencana. Eksekusi tidak diizinkan; siapkan perbaikan lalu tinjau ulang.'},
        {'code': 'HOLD', 'label': 'Tunda',
         'description': 'Tunggu informasi atau bukti tambahan. Eksekusi tidak diizinkan; lengkapi lalu tinjau ulang.'},
    ],
}


def workflow_contract():
    """Return a serializable copy so callers cannot change policy by editing it."""
    return deepcopy(_CONTRACT)
