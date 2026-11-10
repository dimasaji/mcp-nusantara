"""Use ruled PDF geometry to rescue activity grids misclassified as pictures.

Only a bounded grid with explicit procedure headers is eligible. Docling still
owns cell matching and table reconstruction; coordinates come from the PDF.
"""
from pathlib import Path


def scanned_activity_grid_regions(page) -> list[tuple]:
    """Locate ruled raster grids, accepting only procedure headers read by OCR.

    Run after OCR, before layout postprocessing assigns cells to containers.
    Image geometry proposes a box; it never supplies text or table cell values.
    """
    import re

    import cv2
    import numpy as np

    if page.size is None or not page.cells:
        return []
    image = page.get_image(scale=2)
    if image is None:
        return []
    gray = np.asarray(image.convert('L'))
    ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    height, width = ink.shape
    horizontal = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(20, width // 20), 1)))
    vertical = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(20, height // 20))))
    joined = cv2.dilate(horizontal | vertical, np.ones((3, 3), dtype=np.uint8))
    contours, _ = cv2.findContours(joined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    scale_x, scale_y = page.size.width / width, page.size.height / height
    regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < width / 3 or h < height / 10:
            continue
        # Reject boxes without a grid of intersecting horizontal/vertical rules.
        crop_h = horizontal[y:y+h, x:x+w]
        crop_v = vertical[y:y+h, x:x+w]
        h_count = cv2.connectedComponents(crop_h)[0] - 1
        v_count = cv2.connectedComponents(crop_v)[0] - 1
        if h_count < 3 or v_count < 3:
            continue
        left, top, right, bottom = x*scale_x, y*scale_y, (x+w)*scale_x, (y+h)*scale_y
        header_text = []
        for cell in page.cells:
            box = cell.rect.to_bounding_box().to_top_left_origin(page.size.height)
            cx, cy = (box.l + box.r) / 2, (box.t + box.b) / 2
            if left <= cx <= right and top <= cy <= top + (bottom-top) / 4:
                header_text.append(cell.text)
        text = ' '.join(header_text).casefold()
        if (re.search(r'\b(?:no|pelaksana)\b', text) and re.search(r'\bkegiatan\b', text)
                and re.search(r'\b(?:kelengkapan|mutu\s+baku)\b', text)):
            regions.append((left, top, right, bottom))
    return sorted(regions, key=lambda box: (box[1], box[0]))


def activity_grid_regions(source: Path) -> dict[int, list[tuple]]:
    import pymupdf
    regions = {}
    # Header keywords that indicate an activity/procedure grid (flexible).
    _HEADER_KEYS = {'no', 'no.', 'nomor', 'kegiatan', 'aktivitas', 'uraian',
                    'uraian kegiatan', 'prosedur', 'langkah', 'pelaksana',
                    'kelengkapan', 'mutu baku', 'waktu', 'output', 'keterangan'}
    with pymupdf.open(source) as pdf:
        for number, page in enumerate(pdf):
            found = False
            for strategy in ('lines_strict', 'lines', 'text'):
                try:
                    tables = page.find_tables(strategy=strategy).tables
                except Exception:
                    tables = []
                for table in tables:
                    if len(table.rows) < 2 or (table.rows and len(table.rows[0].cells) < 3):
                        continue
                    for index, row in enumerate(table.extract()):
                        labels = {' '.join((v or '').split()).casefold() for v in row}
                        # Accept if at least 2 header keywords match (flexible).
                        if len(labels & _HEADER_KEYS) >= 2:
                            try:
                                y = min(c[1] for c in table.rows[index].cells if c)
                            except Exception:
                                y = table.bbox[1]
                            regions.setdefault(number + 1, []).append(
                                (table.bbox[0], y, table.bbox[2], table.bbox[3]))
                            found = True
                            break
                    if found:
                        break
                if found:
                    break
            # Fallback: any table with >= 3 rows and >= 3 cols (no header match).
            if not found:
                try:
                    tables = page.find_tables(strategy='lines').tables
                except Exception:
                    tables = []
                for table in tables:
                    if len(table.rows) >= 2 and (table.rows and len(table.rows[0].cells) >= 3):
                        regions.setdefault(number + 1, []).append(
                            (table.bbox[0], table.bbox[1], table.bbox[2], table.bbox[3]))
                        found = True
                        break
    return regions


def missing_activity_grids(blocks, detected_regions) -> list[int]:
    """Require reconstructed table provenance to cover each proposed grid."""
    missing = set()
    for page, regions in detected_regions.items():
        for left, top, right, bottom in regions:
            area = (right-left) * (bottom-top)
            matched = False
            for block in blocks:
                if block['type'] != 'table':
                    continue
                for source in block.get('source_regions', []):
                    if source['page'] != page:
                        continue
                    x0, y0, x1, y1 = source['bbox']
                    overlap = max(0, min(right, x1)-max(left, x0)) * max(0, min(bottom, y1)-max(top, y0))
                    table_area = (x1-x0) * (y1-y0)
                    union = area + table_area - overlap
                    if union > 0 and overlap / union >= .8:
                        matched = True
            if not matched:
                missing.add(page)
    return sorted(missing)


def normalize_activity_grids(payload, source: Path):
    """Retain native Docling JSON, repair merged columns from ruled source cells.

    TableFormer can merge the number/activity or several actor columns. A
    digital ruled grid provides an independent, exact cell boundary. This
    normalization never invents values, and records the extraction method.
    """
    import pymupdf

    from .sop_tables import normalize_docling_tables
    regions = activity_grid_regions(source)
    if not regions:
        return normalize_docling_tables(payload)
    blocks, activities, search_text = [], [], []
    labels = {'No.': 'number', 'Uraian Kegiatan': 'activity', 'Kelengkapan': 'kelengkapan',
              'Waktu': 'waktu', 'Output': 'output', 'Keterangan': 'keterangan'}
    def clean(value):
        return ' '.join((value or '').split())
    with pymupdf.open(source) as pdf:
        for page_number, page in enumerate(pdf, 1):
            search_text.append(f'Halaman {page_number}\n' + page.get_text('text'))
            page_regions = regions.get(page_number, [])
            if not page_regions:
                blocks.extend(b for b in payload['blocks'] if page_number in b['page_numbers'])
                continue
            top = min(r[1] for r in page_regions)
            # Read the metadata columns separately: native layout sometimes
            # puts legal grounds beneath the qualification heading.
            if top > 100:
                left, right = min(r[0] for r in page_regions), max(r[2] for r in page_regions)
                middle = (left + right) / 2
                for candidate in page.find_tables(strategy='lines_strict').tables:
                    for cell in candidate.rows[0].cells:
                        if cell and abs(cell[0] - left) < 1 and cell[1] < top and (right-left)/3 < cell[2]-left < 2*(right-left)/3:
                            middle = cell[2]
                            break
                for side, x0, x1 in [('left', left, middle), ('right', middle, right)]:
                    content = '\n'.join(' '.join(line.split()) for line in page.get_text('text', clip=(x0, 0, x1, top), sort=True).splitlines() if line.strip())
                    if content:
                        blocks.append({'block_id': f'pdf-metadata-{page_number}-{side}', 'type': 'text',
                                       'content': content, 'page_numbers': [page_number], 'method': 'pdf-native-column'})
            uncovered = {}
            for word in page.get_text('words'):
                x, y = (word[0] + word[2]) / 2, (word[1] + word[3]) / 2
                if top > 100 and y < top and left <= x <= right:
                    continue  # Already retained as metadata columns.
                if any(r[0] <= x <= r[2] and r[1] <= y <= r[3] for r in page_regions):
                    continue
                uncovered.setdefault((word[5], word[6]), []).append(word)
            for (block_no, line_no), words in uncovered.items():
                words.sort(key=lambda w: w[0])
                blocks.append({'block_id': f'pdf-outside-{page_number}-{block_no}-{line_no}', 'type': 'text',
                               'content': ' '.join(w[4] for w in words), 'page_numbers': [page_number],
                               'method': 'pdf-native-outside-grid'})
            for index, region in enumerate(page_regions):
                tables = page.find_tables(clip=region, strategy='lines_strict').tables
                if len(tables) != 1:
                    raise ValueError('RULED_GRID_AMBIGUOUS')
                table = tables[0]
                raw_rows = table.extract()
                rows = [[clean(v) for v in row] for row in raw_rows]
                header_count = 2 if len(rows) > 1 and not rows[1][0].isdigit() else 1
                headers = []
                parent = ''
                for col, value in enumerate(rows[0]):
                    parent = value or parent
                    child = rows[1][col] if header_count == 2 else ''
                    headers.append(parent + ' / ' + child if child and child != parent else parent)
                body = rows[header_count:]
                key = f'pdf-grid-{page_number}-{index}'
                nodes = []
                for drawing in page.get_drawings():
                    fill, rect = drawing.get('fill'), drawing['rect']
                    if drawing['type'] != 'fs' or not fill or max(fill) - min(fill) < .1 or not (5 < rect.width < 50 and 3 < rect.height < 30):
                        continue
                    x, y = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
                    for rindex in range(header_count, len(rows)):
                        for col, cell in enumerate(table.rows[rindex].cells):
                            if cell and cell[0] <= x <= cell[2] and cell[1] <= y <= cell[3] and headers[col].startswith('Pelaksana / '):
                                nodes.append({'row_number': rows[rindex][0], 'column_header': headers[col],
                                              'bbox': list(rect), 'path_items': len(drawing['items']), 'page_number': page_number})
                columns = {labels[label.split(' / ')[-1]]: col for col, label in enumerate(headers)
                           if label.split(' / ')[-1] in labels}
                if not {'number', 'activity', 'kelengkapan'}.issubset(columns):
                    raise ValueError('RULED_GRID_HEADERS_INCOMPLETE')
                for rindex, values in enumerate(body, header_count):
                    number = values[columns['number']]
                    if not number.isdigit():
                        raise ValueError('RULED_GRID_ACTIVITY_NUMBER_INVALID')
                    row = {key: values[col] for key, col in columns.items()}
                    activities.append({**row, 'number': int(number), 'page': page_number,
                                       'block_id': key, 'headers': headers,
                                       'method': 'pdf-ruled-grid-validated',
                                       'source_cells': {field: {'text': raw_rows[rindex][col] or '',
                                           'bbox': table.rows[rindex].cells[col], 'page_number': page_number,
                                           'start_row_offset_idx': rindex, 'start_col_offset_idx': col}
                                                        for field, col in columns.items()}})
                def escape(value):
                    return value.replace('|', '\\|')
                markdown = '\n'.join(['|' + '|'.join(map(escape, headers)) + '|',
                                      '|' + '|'.join(['---'] * len(headers)) + '|'] +
                                     ['|' + '|'.join(map(escape, row)) + '|' for row in body])
                blocks.append({'block_id': key, 'type': 'table', 'content': markdown,
                               'page_numbers': [page_number], 'method': 'pdf-ruled-grid-validated',
                               'table_data': {'headers': headers, 'rows': body, 'num_rows': len(body),
                                              'num_cols': len(headers), 'source_cells': [r.cells for r in table.rows]},
                               'flowchart_nodes': nodes})
    pages = sorted({r['page'] for r in activities})
    for block in blocks:
        if block['type'] == 'table':
            block['related_pages'] = [p for p in pages if p not in block['page_numbers']]
    # Native Docling texts supplement scanned/non-grid regions in the search
    # corpus. Whole-document absence must not depend on a context projection.
    search_text.extend(item.get('text', '') for item in payload.get('docling_json', {}).get('texts', []))
    return normalize_docling_tables({**payload, 'blocks': blocks, 'activity_rows': activities,
            'full_document_text': '\n'.join(search_text),
            'markdown': '\n\n'.join(b['content'] for b in blocks),
            'normalization': {'method': 'docling-plus-pdf-ruled-grid', 'source': 'physical PDF cells',
                              'activity_count': len(activities), 'native_docling_json_preserved': True}})


def ruled_grid_pipeline(detected_regions: dict[int, list[tuple]] | None = None, source_headers=None):
    from docling.datamodel.base_models import Cluster
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
    from docling_core.types.doc import BoundingBox, CoordOrigin, DocItemLabel

    class GridAfterOcr:
        def __init__(self, original):
            self.original = original

        def __call__(self, result, pages):
            regions = activity_grid_regions(result.input.file)
            for page in self.original(result, pages):
                page_regions = regions.get(page.page_no, []) or scanned_activity_grid_regions(page)
                if page_regions and detected_regions is not None:
                    detected_regions[page.page_no] = page_regions
                if page_regions and source_headers is not None:
                    from .sop_tables import column_field
                    headers = []
                    for cell in page.cells:
                        if not column_field(cell.text):
                            continue
                        box = cell.rect.to_bounding_box().to_top_left_origin(page.size.height)
                        x, y = (box.l + box.r)/2, (box.t + box.b)/2
                        if any(left <= x <= right and top <= y <= top+(bottom-top)/4
                               for left, top, right, bottom in page_regions):
                            headers.append({'text': cell.text, 'bbox': box.model_dump(mode='json'),
                                            'page_number': page.page_no, 'method': 'page-ocr-header'})
                    source_headers[page.page_no] = headers
                for region in page_regions:
                    bbox = BoundingBox(l=region[0], t=region[1], r=region[2], b=region[3], coord_origin=CoordOrigin.TOPLEFT)
                    def inside(box, region_bbox=bbox, height=page.size.height):
                        box = box.to_top_left_origin(height)
                        return (region_bbox.l <= (box.l + box.r) / 2 <= region_bbox.r
                                and region_bbox.t <= (box.t + box.b) / 2 <= region_bbox.b)
                    cells = [c for c in page.cells if inside(c.rect.to_bounding_box())]
                    if not cells:
                        continue
                    clusters = page.predictions.layout.clusters
                    retained = [c for c in clusters if not inside(c.bbox)]
                    retained.append(Cluster(id=max((c.id for c in clusters), default=0) + 1,
                                            label=DocItemLabel.TABLE, bbox=bbox, cells=cells, confidence=1.))
                    page.predictions.layout.clusters = sorted(retained, key=lambda c: (c.bbox.t, c.bbox.l))
                yield page

    class RuledGridPipeline(StandardPdfPipeline):
        def _init_models(self):
            super()._init_models()
            # Modify raw detections before Docling assigns cells and container
            # children. Replacing postprocessed clusters leaves dangling refs.
            # Docling 2.142 predicts raw layout BEFORE OCR. Wrap the OCR stage,
            # whose output already has layout predictions and readable cells.
            self.ocr_model = GridAfterOcr(self.ocr_model)

    return RuledGridPipeline
