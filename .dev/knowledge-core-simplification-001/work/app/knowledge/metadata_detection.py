"""Conservative metadata detection from stored extraction, never from a filename."""
import re
import unicodedata
from datetime import date

from .sop_metadata import SOPMetadata


PATTERNS = {
    'official_title': r'(?:judul(?: resmi)?(?: sop)?|nama\s+s\.?\s*o\.?\s*p\.?)',
    'institution': r'(?:instansi|nama instansi|kementerian|lembaga|perangkat daerah)',
    'unit': r'(?:unit kerja|unit organisasi|unit pelaksana|bidang|bagian)',
    'sop_number': r'(?:nomor|no\.?)\s*(?:s\.?o\.?p\.?)',
    'jurisdiction': r'(?:wilayah kewenangan|wilayah kerja|cakupan wilayah)',
    'issued_on': r'(?:tanggal penetapan|ditetapkan pada|tanggal ditetapkan|tgl\.? pengesahan)',
    'effective_on': r'(?:tanggal mulai berlaku|mulai berlaku|berlaku mulai|tanggal berlaku)',
    'expires_on': r'(?:tanggal akhir berlaku|berlaku sampai|berlaku hingga|tanggal berakhir)',
    'revision': r'(?:nomor revisi|revisi(?: ke)?)',
}


def _date(value):
    months = dict(zip(('januari februari maret april mei juni juli agustus september oktober november desember').split(), range(1, 13)))
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            return date.fromisoformat(value).isoformat()
        found = re.fullmatch(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})', value.casefold())
        if found:
            return date(int(found[3]), months[found[2]], int(found[1])).isoformat()
    except (ValueError, KeyError):
        pass
    return None


def detect_metadata(document_id, blocks):
    facts = {}
    for key, label in PATTERNS.items():
        fact = {'status': 'unreadable', 'value': None, 'page_number': None,
                'note': 'Tidak terdeteksi otomatis; ketiadaan dalam sumber belum dapat dipastikan.'}
        for block in blocks:
            for line in block['content'].splitlines():
                match = re.match(r'^\s*' + label + r'(?:\s*[:：-]\s*|\s+)(.+?)\s*$', line, re.I)
                if not match and key in {'institution', 'unit'}:
                    match = re.search(r'\b' + ('DINAS' if key == 'institution' else 'BIDANG') +
                        r'\s+(.+?)(?=\s+(?:BIDANG|DASAR HUKUM|KUALIFIKASI PELAKSANA)\b|$)', line, re.I)
                if not match:
                    continue
                value = re.split(r'\s+Tgl\b', match[1], flags=re.I)[0].strip()
                if key.endswith('_on'):
                    value = _date(value)
                if value:
                    fact = {'status': 'present', 'value': value[:1024],
                            'page_number': next(iter(block.get('page_numbers', [])), None), 'note': ''}
                    break
            if fact['status'] == 'present':
                break
        facts[key] = fact
    if facts['official_title']['status'] != 'present':
        return None
    anchors = [facts[k]['value'] for k in ('institution', 'unit', 'sop_number')]
    if not anchors[-1]:
        anchors[-1] = facts['official_title']['value']
    slug = unicodedata.normalize('NFKD', '-'.join(v for v in anchors if v)).encode('ascii', 'ignore').decode().lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')[:120]
    return SOPMetadata.model_validate({**facts, 'logical_sop_id': 'SOP:' + slug if slug else document_id,
        'validity': 'not_confirmed', 'validity_note': 'Deteksi sistem; tidak menyimpulkan keberlakuan hukum.'})
