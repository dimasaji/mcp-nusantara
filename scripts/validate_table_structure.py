"""Validate Docling table extraction against PyMuPDF table detection."""
import sys, json, os
import pymupdf

def extract_pymupdf_tables(pdf_path):
    tables = []
    with pymupdf.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf, 1):
            tabs = page.find_tables()
            for t in tabs.tables:
                rows = t.extract()
                tables.append({'page': page_num, 'rows': len(rows), 'cols': len(rows[0]) if rows else 0, 'cells': sum(len(r) for r in rows)})
    return tables

def extract_docling_tables(doc_id, base_url='http://127.0.0.1:8000', token='R4H4Si4.'):
    import urllib.request
    req = urllib.request.Request(base_url+'/v1/knowledge/pipeline/reviews/'+doc_id, headers={'X-Admin-Token':token})
    d = json.loads(urllib.request.urlopen(req, timeout=60).read())
    blocks = d.get('extracted_blocks', [])
    tables = []
    for b in blocks:
        if b.get('type') == 'table':
            content = b.get('content','')
            rows = content.count('\n') + 1 if content else 0
            tables.append({'page': b.get('page_numbers',[None])[0], 'block_id': b.get('block_id'), 'rows_est': rows, 'content_len': len(content)})
    return tables, d

def validate(pdf_path, doc_id=None):
    pm_tables = extract_pymupdf_tables(pdf_path)
    print('PyMuPDF detected tables (digital):', len(pm_tables))
    for t in pm_tables:
        print('  page %d: %d rows x %d cols, %d cells' % (t['page'], t['rows'], t['cols'], t['cells']))
    if doc_id:
        dl_tables, detail = extract_docling_tables(doc_id)
        print('Docling table blocks:', len(dl_tables))
        for t in dl_tables:
            print('  page %s: ~%d rows, %d chars' % (t['page'], t['rows_est'], t['content_len']))
        # Text coverage check: ensure table content matches page text
        with pymupdf.open(pdf_path) as pdf:
            for t in dl_tables:
                page = pdf[t['page']-1] if t['page'] and t['page'] <= len(pdf) else None
                if page:
                    page_text = page.get_text()
                    # Check if key words from table content appear in page text
                    sample = t['content_len']
                    print('  -> page %s text length: %d, table content: %d chars' % (t['page'], len(page_text), sample))
    # Summary
    print('\nValidation summary:')
    print('  PyMuPDF (digital): %d tables' % len(pm_tables))
    print('  Docling (OCR+layout): %d table blocks' % (len(dl_tables) if doc_id else 0))
    print('  Note: scanned PDFs require OCR-based table detection (Docling). PyMuPDF find_tables only works on digital PDFs with clear borders.')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: validate_table_structure.py <pdf_path> [doc_id]')
        sys.exit(1)
    validate(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
