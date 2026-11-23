"""SOP field extractor - extracts structured fields from SOP text.

Provides deterministic answer composition without LLM.
"""
import json
import re
from typing import Optional


def extract_sop_fields(text: str) -> dict:
    """Extract structured fields from SOP text.

    Returns dict with keys: requirements, procedure, duration, cost, legal_basis,
    product, channel, title. Each value is a string (empty if not found).
    """
    fields = {
        'title': '',
        'requirements': '',
        'procedure': '',
        'duration': '',
        'cost': '',
        'legal_basis': '',
        'product': '',
        'channel': '',
    }

    if not text:
        return fields

    # Title: "NAMA SOP: ..." or "NAMA SOP ..." (OCR may omit colon)
    title_match = re.search(r'Nama\s*S\.?O\.?P\.?\s*[:;\-]?\s*([A-Z][^\r\n|]{5,})', text, re.I | re.M)
    if title_match:
        fields['title'] = title_match.group(1).strip()[:200]

    # Requirements: inline value or following lines/bullets
    lines = text.splitlines()
    for i, raw in enumerate(lines):
        line = raw.strip()
        m = re.match(r'Persyaratan\s*[:;\-]?\s*(.*)', line, re.I)
        if not m:
            continue
        inline = m.group(1).strip()
        if len(inline) > 3:
            fields['requirements'] = inline[:500]
            break
        # Collect following non-empty lines until next section header
        collected = []
        for j in range(i + 1, min(i + 8, len(lines))):
            l = lines[j].strip()
            if not l:
                break
            if re.match(r'(Prosedur|Durasi|Biaya|Dasar\s+Hukum|Kanal|Produk|Persyaratan)\s*[:;\-]?', l, re.I):
                break
            collected.append(l.lstrip('-*0123456789. ').strip())
        if collected:
            fields['requirements'] = '; '.join(collected)[:500]
            break

    # Procedure: inline value or following lines/bullets
    for i, raw in enumerate(lines):
        line = raw.strip()
        m = re.match(r'Prosedur\s*[:;\-]?\s*(.*)', line, re.I)
        if not m:
            continue
        inline = m.group(1).strip()
        if len(inline) > 3:
            fields['procedure'] = inline[:500]
            break
        collected = []
        for j in range(i + 1, min(i + 8, len(lines))):
            l = lines[j].strip()
            if not l:
                break
            if re.match(r'(Persyaratan|Durasi|Biaya|Dasar\s+Hukum|Kanal|Produk|Prosedur)\s*[:;\-]?', l, re.I):
                break
            collected.append(l.lstrip('-*0123456789. ').strip())
        if collected:
            fields['procedure'] = '; '.join(collected)[:500]
            break

    # Duration: look for "X hari/jam/menit"
    dur_match = re.search(r'(\d+\s*(?:hari|jam|menit)(?:\s+kerja)?)', text, re.I)
    if dur_match:
        fields['duration'] = dur_match.group(1).strip()

    # Cost: look for "Rp" or "gratis" or "biaya"
    cost_match = re.search(r'(?:Rp\.?\s*[\d.,]+|gratis|tidak\s+dipungut\s+biaya)', text, re.I)
    if cost_match:
        fields['cost'] = cost_match.group(0).strip()

    # Legal basis: "Dasar Hukum" section (inline value or following lines)
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r'Dasar\s+Hukum\s*[:;\-]?\s*(.+)', line, re.I)
        if m and len(m.group(1).strip()) > 3:
            # Inline value present; do not bleed into following lines.
            fields['legal_basis'] = m.group(1).strip()[:300]
            break
        if re.match(r'Dasar\s+Hukum\s*$', line, re.I) or re.match(r'Dasar\s+Hukum\s*[:;\-]?\s*$', line, re.I):
            idx = text.splitlines().index(line)
            basis = []
            for j in range(idx + 1, min(idx + 5, len(text.splitlines()))):
                l = text.splitlines()[j].strip()
                if l and not l.startswith('Peringatan') and not l.startswith('Keterkaitan'):
                    basis.append(l)
                else:
                    break
            if basis:
                fields['legal_basis'] = ' '.join(basis)[:300]
            break

    # Channel: online/loket
    if re.search(r'online|website|aplikasi', text, re.I):
        fields['channel'] = 'online'
    elif re.search(r'loket', text, re.I):
        fields['channel'] = 'loket'

    # Product: what is being issued
    product_match = re.search(r'Penerbitan\s+(\w[\w\s]{3,40})', text, re.I)
    if product_match:
        fields['product'] = product_match.group(1).strip()[:100]

    return fields


def compose_answer(fields: dict, question: str) -> str:
    """Compose a deterministic answer from SOP fields."""
    q = question.lower()
    parts = []

    if any(w in q for w in ['persyaratan', 'syarat', 'berkas', 'dokumen']):
        if fields['requirements']:
            parts.append('Persyaratan: ' + fields['requirements'])

    if any(w in q for w in ['prosedur', 'langkah', 'cara', 'alur', 'proses']):
        if fields['procedure']:
            parts.append('Prosedur: ' + fields['procedure'])

    if any(w in q for w in ['lama', 'durasi', 'waktu', 'kapan', 'selesai']):
        if fields['duration']:
            parts.append('Waktu: ' + fields['duration'])

    if any(w in q for w in ['biaya', 'tarif', 'harga', 'gratis', 'bayar']):
        if fields['cost']:
            parts.append('Biaya: ' + fields['cost'])

    if any(w in q for w in ['dasar hukum', 'undang', 'peraturan']):
        if fields['legal_basis']:
            parts.append('Dasar hukum: ' + fields['legal_basis'])

    if any(w in q for w in ['produk', 'apa yang', 'diterbitkan', 'dikeluarkan']):
        if fields['product']:
            parts.append('Produk: ' + fields['product'])

    if any(w in q for w in ['kanal', 'online', 'loket', 'cara pengajuan']):
        if fields['channel']:
            parts.append('Kanal: ' + fields['channel'])

    if not parts:
        return ''

    return '\n'.join(parts)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: sop_field_extractor.py <text_file>')
        sys.exit(1)
    text = open(sys.argv[1], encoding='utf-8').read()
    fields = extract_sop_fields(text)
    print(json.dumps(fields, indent=2, ensure_ascii=False) if False else str(fields))
    for k, v in fields.items():
        if v:
            print(f'{k}: {v[:100]}')
