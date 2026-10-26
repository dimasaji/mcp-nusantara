"""Budgeted source selection preserving table headers, blocks and physical pages."""
import re


def project_activity_blocks(document, question):
    """Project stored table rows with their real column labels, never answers."""
    rows = document.get('activity_rows', [])
    if not rows:
        return document['blocks']
    fields = ['activity', 'kelengkapan', 'waktu', 'output', 'keterangan']
    selected_rows = rows
    if re.search(r'persyaratan|syarat|bawa', question, re.I):
        selected_rows = rows[:1]
        fields = ['activity', 'kelengkapan']
    elif re.search(r'proses|prosedur|bagaimana|lalu|lanjut', question, re.I):
        fields = ['activity']
    elif re.search(r'berapa lama|waktu|durasi', question, re.I) and not re.search(r'biaya', question, re.I):
        selected_rows = [r for r in rows if r.get('waktu') or r.get('keterangan')]
        fields = ['activity', 'waktu', 'keterangan']
    elif re.search(r'hasil|produk', question, re.I):
        fields = ['activity', 'output']
    labels = {'activity': 'Uraian Kegiatan', 'kelengkapan': 'Kelengkapan', 'waktu': 'Waktu',
              'output': 'Output', 'keterangan': 'Keterangan'}
    result = []
    for block in document['blocks']:
        if block['type'] != 'table':
            result.append(block); continue
        relevant = [r for r in selected_rows if r['block_id'] == block['block_id']]
        if not relevant:
            continue
        content = 'Tabel kegiatan SOP. Kolom: No.; ' + '; '.join(labels[f] for f in fields) + '.\n'
        content += '\n'.join(f"{r['number']}. " + ' | '.join(labels[f] + ': ' + r[f] for f in fields if r.get(f)) for r in relevant)
        if re.search(r'persyaratan|syarat|bawa', question, re.I):
            content = '\n'.join(f"Baris {r['number']} — Kegiatan: {r['activity']}.\nKelengkapan pemohon pada tahap pengajuan: {r['kelengkapan']}." for r in relevant)
        result.append({**block, 'content': content, 'selected_rows': [r['number'] for r in relevant],
                       'selected_columns': [labels[f] for f in fields]})
    return result


def select_blocks(blocks, question, context_tokens=4096):
    # One UTF-8 byte per token is a conservative upper bound. Reserve room for
    # system/template, the current question, recent history and the answer.
    budget = context_tokens - 1100 - len(question.encode('utf-8'))
    if budget < 256:
        raise ValueError('Konteks SOP tidak muat utuh: anggaran sumber terlalu kecil.')
    def render(block):
        return f"[blok {block['block_id']}; halaman {','.join(map(str,block['page_numbers']))}]\n{block['content']}"
    full = '\n\n'.join(render(b) for b in blocks)
    if len(full.encode('utf-8')) <= budget:
        return full, blocks, []
    words = set(re.findall(r'\w{4,}', question.casefold()))
    service = bool(re.search(r'persyaratan|syarat|bawa|proses|prosedur|lama|waktu|biaya|hasil|layanan|lalu|lanjut', question, re.I))
    ranked = sorted(enumerate(blocks), key=lambda pair: (
        -(20 if service and pair[1]['type'] == 'table' else 0) - sum(w in pair[1]['content'].casefold() for w in words), pair[0]))
    selected, used = [], 160
    for index, block in ranked:
        relevance = (20 if service and block['type'] == 'table' else 0) + sum(w in block['content'].casefold() for w in words)
        if relevance == 0 and selected:
            continue
        size = len(render(block).encode('utf-8')) + 2
        if used + size <= budget:
            selected.append((index, block)); used += size
    if not selected:
        raise ValueError('Konteks SOP tidak muat utuh: satu blok/tabel melebihi anggaran. Blok tidak dipotong.')
    selected.sort()
    included = [b for _, b in selected]
    omitted = [b['block_id'] for b in blocks if b not in included]
    note = f"Konteks bagian terpilih; {len(omitted)} blok lain tidak dimuat. Jangan menyimpulkan isi bagian yang tidak dimuat.\n"
    return note + '\n\n'.join(render(b) for b in included), included, omitted
