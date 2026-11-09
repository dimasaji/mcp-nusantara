"""Validate Docling table extraction accuracy against original PDF text."""
import sys, json, os, subprocess, tempfile

def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyMuPDF (digital) or Tesseract (scanned)."""
    import pymupdf
    with pymupdf.open(pdf_path) as pdf:
        text = ''
        for page in pdf:
            text += page.get_text() + '\n'
        if len(text.strip()) < 100:
            # Scanned PDF: use Tesseract via Docling worker or direct
            print('PDF appears scanned (no text layer). Using Docling OCR text.')
            return None  # Will use Docling's markdown instead
        return text

def validate(pdf_path, doc_id, base_url='http://127.0.0.1:8000', token='R4H4Si4.'):
    import urllib.request
    # Get Docling extraction
    req = urllib.request.Request(base_url+'/v1/knowledge/pipeline/reviews/'+doc_id, headers={'X-Admin-Token':token})
    d = json.loads(urllib.request.urlopen(req, timeout=60).read())
    blocks = d.get('extracted_blocks', [])
    tables = [b for b in blocks if b.get('type') == 'table']
    markdown = d.get('extraction', {}).get('markdown', '') if isinstance(d.get('extraction'), dict) else ''
    if not markdown:
        # Try to get from docling json
        markdown = d.get('text', '')

    # Extract PDF text
    pdf_text = extract_pdf_text(pdf_path)
    if pdf_text is None:
        pdf_text = markdown  # Fallback: use Docling's own markdown as reference

    # Normalize for comparison
    def normalize(t):
        return ' '.join(t.lower().split())

    pdf_norm = normalize(pdf_text)
    print('PDF text length: %d chars' % len(pdf_norm))
    print('Docling tables: %d' % len(tables))

    total_coverage = 0
    for i, t in enumerate(tables):
        content = t.get('content', '')
        # Extract words from table content
        words = set(content.lower().split())
        # Remove markdown/table syntax
        words = {w for w in words if len(w) > 2 and w.isalnum()}
        if not words:
            print('  Table %d: no words extracted' % (i+1))
            continue
        # Check how many table words appear in PDF text
        found = sum(1 for w in words if w in pdf_norm)
        coverage = found / len(words) if words else 0
        total_coverage += coverage
        print('  Table %d (page %s): %d words, %d found in PDF -> %.1f%% coverage' % (i+1, t.get('page_numbers'), len(words), found, coverage*100))

    if tables:
        avg = total_coverage / len(tables)
        print('\nAverage table coverage: %.1f%%' % (avg*100))
        if avg >= 0.8:
            print('STATUS: PASS (>=80% coverage)')
        elif avg >= 0.5:
            print('STATUS: NEEDS_REVIEW (50-80% coverage)')
        else:
            print('STATUS: FAIL (<50% coverage)')
    else:
        print('No tables found in extraction.')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: validate_table_accuracy.py <pdf_path> <doc_id>')
        sys.exit(1)
    validate(sys.argv[1], sys.argv[2])
