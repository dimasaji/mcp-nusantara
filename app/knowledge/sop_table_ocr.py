"""Read damaged row numbers from bounded source crops using existing Tesseract."""
from __future__ import annotations

import csv
import io
import re
import subprocess

from .sop_tables import column_field


def _read_words(page, rect, mode, scale, configuration, *, digits=False):
    import pymupdf

    rect = pymupdf.Rect(rect) & page.rect
    if rect.is_empty:
        return []
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=rect, alpha=False)
    command = [configuration['tesseract_cmd'], 'stdin', 'stdout', '--tessdata-dir',
               configuration['tessdata_path'], '-l', 'eng' if digits else 'ind+eng', '--psm', mode]
    if digits:
        command += ['-c', 'tessedit_char_whitelist=0123456789']
    result = subprocess.run([*command, 'tsv'], input=pixmap.tobytes('png'), capture_output=True,
                            timeout=10, check=True)
    words = []
    for word in csv.DictReader(io.StringIO(result.stdout.decode('utf-8')), delimiter='\t'):
        text = word['text'].strip()
        if not text or float(word['conf']) < 90:
            continue
        if digits and (not text.isascii() or not text.isdigit()):
            continue
        x, y = rect.x0 + int(word['left'])/scale, rect.y0 + int(word['top'])/scale
        words.append({'text': text, 'confidence': float(word['conf']),
                      'bbox': {'l': x, 't': y, 'r': x + int(word['width'])/scale,
                               'b': y + int(word['height'])/scale, 'coord_origin': 'TOPLEFT'}})
    return words


def recover_header_cells(block, source, configuration):
    """Retain exact semantic labels lost from a reconstructed table header."""
    import pymupdf

    cells = block.get('table_data', {}).get('table_cells', [])
    activity = [c for c in cells if c['start_row_offset_idx'] < 3 and column_field(c['text']) == 'activity']
    if len(activity) != 1 or len(block.get('source_regions', [])) != 1:
        return []
    first, col = activity[0]['end_row_offset_idx'], activity[0]['start_col_offset_idx']
    body = [c for c in cells if c['start_row_offset_idx'] >= first
            and c['start_col_offset_idx'] == col and c.get('bbox')]
    if not body or any(c['bbox'].get('coord_origin') != 'TOPLEFT' for c in body):
        return []
    region = block['source_regions'][0]
    x0, y0, x1, _ = region['bbox']
    bottom = min(c['bbox']['t'] for c in body) - 2
    if bottom <= y0 + 1:
        return []
    with pymupdf.open(source) as pdf:
        page = pdf[region['page'] - 1]
        words = [_read_words(page, (x0+1, y0+1, x1-1, bottom), mode, 4, configuration)
                 for mode in ('6', '11')]
    return [{**word, 'page_number': region['page'], 'method': 'tesseract-header-crop'}
            for result in words for word in result if column_field(word['text'])]


def recover_number_cells(block, source, configuration):
    """Return additional OCR evidence; never change Docling's original cells.

    Whole-column and single-cell reads complement each other. Conflicting
    high-confidence reads are refused; sequence positions are never labels.
    """
    import pymupdf

    cells = block.get('table_data', {}).get('table_cells', [])
    activity = [c for c in cells if c['start_row_offset_idx'] < 3 and column_field(c['text']) == 'activity']
    quality = [c for c in cells if c['start_row_offset_idx'] < 3 and column_field(c['text']) == 'kelengkapan']
    if len(activity) != 1 or not quality or len(block.get('page_numbers', [])) != 1:
        return []
    col, first = activity[0]['start_col_offset_idx'], max(activity[0]['end_row_offset_idx'], quality[0]['end_row_offset_idx'])
    if col != 1 or not block.get('source_regions'):
        return []  # More than one preceding column does not identify numbering.
    body = [c for c in cells if c['start_col_offset_idx'] == col and c['end_col_offset_idx'] == col + 1
            and c['start_row_offset_idx'] >= first and c.get('bbox')]
    raw_numbers = [c for c in cells if c['start_col_offset_idx'] == 0 and c['start_row_offset_idx'] >= first]
    if len(raw_numbers) == len(body) and all(re.fullmatch(r'\d+[.)]?', c['text'].strip()) for c in raw_numbers):
        return []
    if not body or any(c['end_row_offset_idx'] != c['start_row_offset_idx'] + 1 for c in body):
        return []
    page_number = block['page_numbers'][0]
    regions = [r['bbox'] for r in block['source_regions'] if r['page'] == page_number]
    if len(regions) != 1:
        return []
    with pymupdf.open(source) as pdf:
        page = pdf[page_number - 1]
        # Cell bboxes in the Docling adapter are physical TOPLEFT coordinates.
        if any(c['bbox'].get('coord_origin') != 'TOPLEFT' for c in body):
            return []
        left = regions[0][0] + 3
        right = min(c['bbox']['l'] for c in body) - 3
        top, bottom = min(c['bbox']['t'] for c in body) - 3, regions[0][3]
        if right-left < 2:
            return []

        def read(rect, mode, scale):
            return _read_words(page, rect, mode, scale, configuration, digits=True)

        column = read((left, top, right, bottom), '6', 5)
        recovered = []
        for cell in body:
            box = cell['bbox']
            local = read((left, box['t']-2, right, box['b']+2), '7', 6)
            whole = [w for w in column if box['t']-3 <= (w['bbox']['t'] + w['bbox']['b'])/2 <= box['b']+3]
            # Each observation must identify one number; high-confidence
            # disagreement is evidence of uncertainty, not a reason to vote.
            if len(local) > 1 or len(whole) > 1:
                continue
            observations = local + whole
            if not observations or len({w['text'] for w in observations}) != 1:
                continue
            best = max(observations, key=lambda w: w['confidence'])
            recovered.append({**best, 'start_row_offset_idx': cell['start_row_offset_idx'],
                              'end_row_offset_idx': cell['end_row_offset_idx'],
                              'start_col_offset_idx': 0, 'end_col_offset_idx': 1,
                              'row_span': 1, 'col_span': 1, 'method': 'tesseract-number-cell',
                              'page_number': page_number})
    return recovered
