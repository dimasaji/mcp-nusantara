"""Use ruled PDF geometry to rescue activity grids misclassified as pictures.

Only a bounded grid with explicit procedure headers is eligible. Docling still
owns cell matching and table reconstruction; coordinates come from the PDF.
"""
from pathlib import Path


def activity_grid_regions(source: Path) -> dict[int, list[tuple]]:
    import pymupdf
    regions = {}
    with pymupdf.open(source) as pdf:
        for number, page in enumerate(pdf):
            for table in page.find_tables(strategy='lines_strict').tables:
                for index, row in enumerate(table.extract()):
                    labels = {' '.join((v or '').split()).casefold() for v in row}
                    if {'no.', 'uraian kegiatan'}.issubset(labels):
                        # Include both levels of headings and the whole ruled body.
                        y = min(c[1] for c in table.rows[index].cells if c)
                        regions.setdefault(number + 1, []).append((table.bbox[0], y, table.bbox[2], table.bbox[3]))
                        break
    return regions


def normalize_activity_grids(payload, source: Path):
    """Retain native Docling JSON, repair merged columns from ruled source cells.

    TableFormer can merge the number/activity or several actor columns. A
    digital ruled grid provides an independent, exact cell boundary. This
    normalization never invents values, and records the extraction method.
    """
    import pymupdf
    regions = activity_grid_regions(source)
    if not regions:
        return payload
    blocks, activities, search_text = [], [], []
    labels = {'No.': 'number', 'Uraian Kegiatan': 'activity', 'Kelengkapan': 'kelengkapan',
              'Waktu': 'waktu', 'Output': 'output', 'Keterangan': 'keterangan'}
    clean = lambda value: ' '.join((value or '').split())
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
                for values in body:
                    number = values[columns['number']]
                    if not number.isdigit():
                        raise ValueError('RULED_GRID_ACTIVITY_NUMBER_INVALID')
                    row = {key: values[col] for key, col in columns.items()}
                    activities.append({**row, 'number': int(number), 'page': page_number,
                                       'block_id': key, 'headers': headers})
                escape = lambda value: value.replace('|', '\\|')
                markdown = '\n'.join(['|' + '|'.join(map(escape, headers)) + '|',
                                      '|' + '|'.join(['---'] * len(headers)) + '|'] +
                                     ['|' + '|'.join(map(escape, row)) + '|' for row in body])
                blocks.append({'block_id': key, 'type': 'table', 'content': markdown,
                               'page_numbers': [page_number], 'method': 'pdf-ruled-grid-validated',
                               'table_data': {'headers': headers, 'rows': body, 'num_rows': len(body),
                                              'num_cols': len(headers), 'source_cells': [r.cells for r in table.rows]},
                               'flowchart_nodes': nodes})
    if [r['number'] for r in activities] != list(range(1, len(activities) + 1)):
        raise ValueError('RULED_GRID_SEQUENCE_INVALID')
    pages = sorted({r['page'] for r in activities})
    for block in blocks:
        if block['type'] == 'table':
            block['related_pages'] = [p for p in pages if p not in block['page_numbers']]
    # Native Docling texts supplement scanned/non-grid regions in the search
    # corpus. Whole-document absence must not depend on a context projection.
    search_text.extend(item.get('text', '') for item in payload.get('docling_json', {}).get('texts', []))
    return {**payload, 'blocks': blocks, 'activity_rows': activities,
            'full_document_text': '\n'.join(search_text),
            'markdown': '\n\n'.join(b['content'] for b in blocks),
            'normalization': {'method': 'docling-plus-pdf-ruled-grid', 'source': 'physical PDF cells',
                              'activity_count': len(activities), 'native_docling_json_preserved': True}}


def ruled_grid_pipeline():
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
    from docling.datamodel.base_models import Cluster
    from docling_core.types.doc import BoundingBox, CoordOrigin, DocItemLabel

    class GridLayout:
        def __init__(self, original):
            self.original = original

        def __call__(self, result, pages):
            regions = activity_grid_regions(result.input.file)
            for page in self.original(result, pages):
                for region in regions.get(page.page_no, []):
                    bbox = BoundingBox(l=region[0], t=region[1], r=region[2], b=region[3], coord_origin=CoordOrigin.TOPLEFT)
                    def inside(box):
                        box = box.to_top_left_origin(page.size.height)
                        return bbox.l <= (box.l + box.r) / 2 <= bbox.r and bbox.t <= (box.t + box.b) / 2 <= bbox.b
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
            self.layout_model = GridLayout(self.layout_model)

    return RuledGridPipeline
