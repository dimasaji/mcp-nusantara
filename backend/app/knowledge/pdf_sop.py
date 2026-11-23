"""Read ruled SOP activity tables without mixing qualifications into applicant inputs."""
from __future__ import annotations

import re


def activity_rows(raw: bytes) -> list[dict]:
    import pymupdf

    rows = []
    labels = {'no.': 'number', 'uraian kegiatan': 'activity', 'kelengkapan': 'kelengkapan',
              'waktu': 'waktu', 'output': 'output', 'keterangan': 'keterangan'}
    with pymupdf.open(stream=raw, filetype='pdf') as document:
        for number, page in enumerate(document, 1):
            for table in page.find_tables().tables:
                columns = {}
                for cells in table.extract():
                    cells = [' '.join((cell or '').split()) for cell in cells]
                    for index, cell in enumerate(cells):
                        if cell.casefold() in labels:
                            columns[labels[cell.casefold()]] = index
                    if not {'number', 'activity', 'kelengkapan'}.issubset(columns):
                        continue
                    values = {key: cells[index] for key, index in columns.items() if index < len(cells)}
                    if not values.get('number', '').isdigit() or not values.get('activity'):
                        continue
                    rows.append({**values, 'number': int(values['number']), 'page': number})
    # Ambiguous/repeated numbering does not establish one continuous procedure.
    if not rows or [row['number'] for row in rows] != list(range(1, len(rows) + 1)):
        return []
    return rows


def rows_text(rows: list[dict]) -> str:
    labels = {'activity': 'Uraian Kegiatan', 'kelengkapan': 'Kelengkapan',
              'waktu': 'Waktu', 'output': 'Output', 'keterangan': 'Keterangan'}
    return '\n'.join(
        f"{row['number']}. " + ' | '.join(f'{labels[key]}: {row[key]}' for key in
            ('activity', 'kelengkapan', 'waktu', 'output', 'keterangan') if row.get(key))
        for row in rows)


def requirement_rows(rows: list[dict], question: str = '') -> list[dict]:
    """Read submission/intake cells until the workflow becomes internal.

    This is a conservative selection, not an inferred universal checklist.
    Later collection or internal certification steps do not add requirements.
    """
    if not rows:
        return []
    if re.search(r'(?:langkah|tahap)\s+(?:pertama|1)\b', question, re.I):
        return [rows[0]] if rows[0].get('kelengkapan') else []
    selected = []
    seen = set()
    for row in rows:
        activity = row['activity']
        submission = re.match(r'^(?:pemohon\s+)?(?:menyampaikan|mengajukan|menyerahkan|mengisi|mengunggah|mengupload|membawa|melampirkan)\b', activity, re.I)
        intake = (re.match(r'^(?:petugas\s+)?(?:menerima|memeriksa|memverifikasi|melakukan verifikasi|melakukan pemeriksaan)\b', activity, re.I)
                  and re.search(r'\b(?:berkas|dokumen|kelengkapan|permohonan)\b', activity, re.I))
        internal = re.search(r'\b(?:sertifikasi|disposisi|nota|draf|draft|jawaban)\b', activity, re.I)
        if internal or not (submission or intake):
            break
        value = ' '.join(row.get('kelengkapan', '').casefold().split())
        if value and value not in seen:
            selected.append(row)
            seen.add(value)
    return selected


def table_facts(turn: dict, evidence) -> dict | None:
    """Choose explicit table cells, never infer actors from flowchart position."""
    if len(evidence or []) != 1 or turn.get('facet') not in {'requirements', 'duration', 'procedure'}:
        return None
    item = evidence[0]
    rows = getattr(item, 'metadata', {}).get('sop_rows', [])
    if not rows:
        return None
    facet = turn['facet']
    selected = []
    if facet == 'requirements':
        selected = requirement_rows(rows, turn.get('question', ''))
        if not selected:
            return None
        quote = '\n'.join(f"Kelengkapan: {row['kelengkapan']}." for row in selected)
        values = {}
        for row in selected:
            value = row['kelengkapan'].rstrip('.')
            values.setdefault(' '.join(value.casefold().split()), value)
        fallback = ('Siapkan ' + next(iter(values.values())) + '.' if len(values) == 1 else
                    'Kelengkapan menurut SOP:\n' + '\n'.join('- ' + value for value in values.values()))
    elif facet == 'duration':
        selected = [row for row in rows if re.search(r'\bselesai\b', row['activity'], re.I)
                    and re.search(r'\b\d+\s+(?:hari|jam|menit)(?:\s+kerja)?\b', row.get('keterangan', ''), re.I)]
        if len(selected) != 1:
            return None
        duration = re.search(r'\b\d+\s+(?:hari|jam|menit)(?:\s+kerja)?\b', selected[0]['keterangan'], re.I)[0]
        quote = rows_text(selected)
        fallback = 'Menurut SOP: ' + duration + '.'
    else:
        selected = rows
        quote = 'Prosedur:\n' + '\n'.join(f"{row['number']}. {row['activity']}." for row in selected)
        fallback = quote
    return {'topic': item.title, 'title': item.title, 'document_id': item.document_id,
            'source': quote, 'score': item.score, 'facet': facet, 'quote': quote,
            'rewrite_quote': quote, 'fallback': fallback, 'unknown': False,
            'pages': sorted({row['page'] for row in selected}), 'table_derived': True,
            'proof': [{'title': item.title, 'chunk': quote, 'score': item.score}]}
