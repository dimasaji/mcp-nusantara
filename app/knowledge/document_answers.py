"""Source-backed answers for validated document cells; model wording is optional.

No service facts live here. Values are read from the selected immutable PDF
extraction. A failed model rewrite keeps the verified quote and its provenance.
"""
import re

from .pdf_sop import table_facts


def document_answer_facts(question, evidence):
    if len(evidence or []) != 1:
        return None
    item = evidence[0]
    metadata = getattr(item, 'metadata', {})
    rows = metadata.get('sop_rows', [])
    if not rows:
        return None
    facet = ('requirements' if re.search(r'persyaratan|syarat|bawa', question, re.I) else
             'duration' if re.search(r'berapa lama|waktu|durasi', question, re.I) else
             'procedure' if re.search(r'proses|prosedur|bagaimana|lalu|lanjut', question, re.I) else None)
    if facet:
        facts = table_facts({'facet': facet}, evidence)
        if facts and facet == 'requirements':
            value = rows[0]['kelengkapan'].rstrip('.')
            quote = 'Kelengkapan: ' + value + '.'
            facts.update(quote=quote, source=quote, rewrite_quote=quote, fallback='Siapkan ' + value + '.',
                         proof=[{'title': item.title, 'chunk': quote, 'score': item.score}])
        return facts
    full = metadata.get('full_document_text', '')
    def make(quote, fallback, facet, selected, unknown=False):
        return {'topic': item.title, 'title': item.title, 'document_id': item.document_id, 'source': quote,
                'quote': quote, 'rewrite_quote': quote, 'fallback': fallback, 'facet': facet, 'unknown': unknown,
                'score': item.score, 'pages': sorted({r['page'] for r in selected}),
                'proof': [{'title': item.title, 'chunk': quote, 'score': item.score}],
                'table_derived': True}
    if re.search(r'biaya|tarif|harga', question, re.I):
        if full and not re.search(r'\b(?:biaya|tarif|harga|rupiah|rp|idr|pungutan|retribusi|pembayaran|gratis|bebas)\b|\d[\d.]+,\s*-', full, re.I):
            return make(full, 'Informasi biaya belum tercantum dalam SOP ini.', 'cost', rows, True)
    if re.search(r'hasil|produk', question, re.I):
        selected = [r for r in rows if re.match(r'^Menerima\b', r['activity'], re.I)]
        if len(selected) == 1:
            value = re.sub(r'^Menerima\s+', '', selected[0]['activity'], flags=re.I).rstrip('.')
            return make(selected[0]['activity'], 'Hasil layanannya: ' + value + '.', 'product', selected)
    contact = re.search(r'\b(?:whatsapp|telepon|email)\b', question, re.I)
    if contact and full and not re.search(r'\b(?:whatsapp|wa|w\.a|telepon|telp|hp|kontak|hubungi|email|e-mail)\b|\b0[8-9]\d{6,}', full, re.I):
        return make(full, f'Informasi {contact[0]} belum tercantum dalam SOP ini.', 'missing', rows, True)
    return None
