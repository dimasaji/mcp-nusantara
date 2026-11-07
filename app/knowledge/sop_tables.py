"""Map source table cells to the activity contract without repairing OCR text."""
from __future__ import annotations

import re

FIELDS = ('activity', 'kelengkapan', 'waktu', 'output', 'keterangan')
_LABELS = {'no': 'number', 'nomor': 'number', 'kegiatan': 'activity',
           'uraian kegiatan': 'activity', 'kelengkapan': 'kelengkapan',
           'waktu': 'waktu', 'output': 'output', 'keterangan': 'keterangan'}


def column_field(text):
    label = ' '.join(re.sub(r'[^\w\s]', ' ', text.casefold()).split())
    label = re.sub(r'^mutu baku\s+', '', label)
    return _LABELS.get(label)


def headers_for_table(block, headers):
    """Keep labels only from this table's physical-page provenance box."""
    result = []
    for header in headers:
        box = header.get('bbox', {})
        if box.get('coord_origin') != 'TOPLEFT':
            continue
        for region in block.get('source_regions', []):
            left, top, right, bottom = region['bbox']
            if (header.get('page_number') == region['page']
                    and left-1 <= box['l'] <= box['r'] <= right+1
                    and top-1 <= box['t'] <= box['b'] <= bottom+1):
                result.append(header)
                break
    return result


def _table_rows(block):
    data = block.get('table_data', {})
    cells = data.get('table_cells', [])
    if not cells:
        return None
    # Keep the original extraction untouched. Supplement unreadable numbers
    # only with explicit OCR crop evidence; conflicting readable values fail.
    cells = [dict(c) for c in cells]
    for recovered in block.get('number_cells', []):
        matches = [c for c in cells if c['start_row_offset_idx'] == recovered['start_row_offset_idx']
                   and c['start_col_offset_idx'] == recovered['start_col_offset_idx']]
        if any(re.fullmatch(r'\d+[.)]?', c['text'].strip())
               and int(c['text'].strip().rstrip('.)')) != int(recovered['text']) for c in matches):
            raise ValueError('ACTIVITY_TABLE_NUMBER_CONFLICT')
        cells = [c for c in cells if c not in matches] + [recovered]
    columns, header_end = {}, 0
    ambiguous = False
    for cell in cells:
        if cell['start_row_offset_idx'] >= 3:
            continue
        field = column_field(cell['text'])
        if not field:
            continue
        col = cell['start_col_offset_idx']
        if cell['end_col_offset_idx'] != col + 1 or (field in columns and columns[field] != col):
            ambiguous = True
        columns[field] = col
        header_end = max(header_end, cell['end_row_offset_idx'])
    if not {'activity', 'kelengkapan'}.issubset(columns):
        if block.get('activity_grid'):
            raise ValueError('ACTIVITY_TABLE_HEADERS_INCOMPLETE')
        return None  # Metadata and unrelated tables remain available as source.
    if ambiguous or len(block.get('page_numbers', [])) != 1:
        raise ValueError('ACTIVITY_TABLE_HEADERS_AMBIGUOUS')
    # Table reconstruction sometimes drops an OCR header that is still present
    # on the page. Use its source coordinates only when one body column spans
    # the header centre. Ambiguous geometry never supplies a semantic label.
    body_cells = [c for c in cells if c['start_row_offset_idx'] >= header_end and c.get('bbox')]
    body_top = min((c['bbox']['t'] for c in body_cells if c['bbox'].get('coord_origin') == 'TOPLEFT'), default=0)
    header_columns = {}
    for header in headers_for_table(block, block.get('header_cells', [])):
        field = column_field(header['text'])
        if field not in FIELDS or field in columns:
            continue
        box = header['bbox']
        if box.get('coord_origin') != 'TOPLEFT' or box['b'] > body_top:
            continue
        x = (box['l'] + box['r']) / 2
        candidates = set()
        for c in body_cells:
            b = c['bbox']
            if (b.get('coord_origin') == 'TOPLEFT' and b['l'] <= x <= b['r']
                    and c['end_col_offset_idx'] == c['start_col_offset_idx'] + 1):
                candidates.add(c['start_col_offset_idx'])
        header_columns.setdefault(field, set()).update(candidates)
    for field, candidates in header_columns.items():
        if len(candidates) == 1 and not candidates.intersection(columns.values()):
            columns[field] = candidates.pop()
    if 'number' not in columns:
        # A damaged short header may be absent. Accept only one preceding
        # column carrying explicit row numbers; never synthesize numbering.
        candidates = []
        for col in range(columns['activity']):
            values = [c['text'].strip() for c in cells
                      if c['start_col_offset_idx'] == col and c['end_col_offset_idx'] == col + 1
                      and c['start_row_offset_idx'] >= header_end and c['text'].strip()]
            if values and all(re.fullmatch(r'\d+[.)]?', value) for value in values):
                candidates.append(col)
        if len(candidates) != 1:
            raise ValueError('ACTIVITY_TABLE_NUMBER_COLUMN_AMBIGUOUS')
        columns['number'] = candidates[0]
    rows = []
    for index in range(header_end, data['num_rows']):
        values, sources = {}, {}
        for field, col in columns.items():
            matches = [c for c in cells if c['start_row_offset_idx'] <= index < c['end_row_offset_idx']
                       and c['start_col_offset_idx'] <= col < c['end_col_offset_idx']]
            if len(matches) > 1:
                raise ValueError('ACTIVITY_TABLE_CELLS_OVERLAP')
            if matches:
                cell = matches[0]
                if cell['end_col_offset_idx'] != cell['start_col_offset_idx'] + 1:
                    raise ValueError('ACTIVITY_TABLE_COLUMNS_MERGED')
                if field in {'number', 'activity'} and cell['end_row_offset_idx'] != index + 1:
                    raise ValueError('ACTIVITY_TABLE_ROWS_MERGED')
                values[field] = ' '.join(cell['text'].split())
                sources[field] = dict(cell)
        if not any(values.values()):
            continue
        if not re.fullmatch(r'\d+[.)]?', values.get('number', '')) or not values.get('activity'):
            raise ValueError('ACTIVITY_TABLE_ROW_INCOMPLETE')
        rows.append({**{f: values.get(f, '') for f in FIELDS},
                     'number': int(values['number'].rstrip('.)')), 'page': block['page_numbers'][0],
                     'block_id': block['block_id'], 'source_cells': sources,
                     'headers': list(columns), 'method': 'docling-source-cells'})
    if not rows:
        raise ValueError('ACTIVITY_TABLE_BODY_EMPTY')
    return rows


def normalize_docling_tables(payload):
    """Unify native and OCR activity rows; ambiguous tables stay unpublishable."""
    rows = list(payload.get('activity_rows', []))
    warnings = list(payload.get('warnings', []))
    errors = []
    existing = {r['block_id'] for r in rows}
    for block in payload['blocks']:
        if block['type'] != 'table' or block['block_id'] in existing:
            continue
        try:
            parsed = _table_rows(block)
            if parsed:
                rows.extend(parsed)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f'ACTIVITY_TABLE_INVALID: {block["block_id"]}: {exc}')
    if not rows and not errors:
        return payload
    block_order = {b['block_id']: index for index, b in enumerate(payload['blocks'])}
    rows.sort(key=lambda r: (r['page'], block_order[r['block_id']]))
    if rows and [r['number'] for r in rows] != list(range(1, len(rows) + 1)):
        errors.append('ACTIVITY_TABLE_SEQUENCE_INVALID')
    if errors:
        return {**payload, 'status': 'PARTIAL', 'warnings': warnings + errors,
                'activity_rows': [], 'activity_validation': {'status': 'INVALID', 'errors': errors}}
    block_text = '\n\n'.join(b['content'] for b in payload['blocks'])
    text = payload.get('full_document_text', '')
    if block_text and block_text not in text:
        text = '\n\n'.join(filter(None, [text, block_text]))
    return {**payload, 'activity_rows': rows, 'full_document_text': text,
            'activity_validation': {'status': 'VALID', 'row_count': len(rows),
                                    'pages': sorted({r['page'] for r in rows})}}
