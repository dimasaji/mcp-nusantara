"""CPU-only subprocess entrypoint; paths originate solely in backend storage."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def convert(source: Path, output: Path):
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling_core.types.doc import TableItem, TextItem

    from .docling_layout import ruled_grid_pipeline

    project = Path(__file__).resolve().parents[2]
    from .docling_config import effective_config
    configuration = json.loads(os.environ['NUSANTARA_DOCLING_CONFIG']) if 'NUSANTARA_DOCLING_CONFIG' in os.environ else effective_config()
    command = configuration['tesseract_cmd']
    import pymupdf
    with pymupdf.open(source) as pdf:
        digital = all(len(page.get_text().strip()) >= 40 for page in pdf)
    options = PdfPipelineOptions(artifacts_path=project / 'nusantara-models/docling',
        do_ocr=not digital, do_table_structure=configuration['tables'],
        accelerator_options=AcceleratorOptions(num_threads=configuration['threads'], device=AcceleratorDevice.CPU),
        ocr_options=TesseractCliOcrOptions(lang=configuration['languages'], force_full_page_ocr=configuration['force_full_page_ocr'],
                                         tesseract_cmd=command, path=configuration['tessdata_path'],
                                         psm=configuration.get('tesseract_psm', 6)))
    detected_regions: dict[int, list[tuple]] = {}
    source_headers: dict[int, list[dict]] = {}
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options, pipeline_cls=ruled_grid_pipeline(detected_regions, source_headers))})
    result = converter.convert(source)
    doc = result.document
    blocks = []
    warnings = [str(error) for error in result.errors]
    for item, _ in doc.iterate_items(traverse_pictures=True):
        if not isinstance(item, (TableItem, TextItem)):
            continue
        pages = sorted({p.page_no for p in item.prov})
        content = item.export_to_markdown(doc=doc) if isinstance(item, TableItem) else item.text
        if not content.strip():
            continue
        if not pages:
            warnings.append('Blok tanpa metadata halaman: ' + item.self_ref)
        block = {'block_id': item.self_ref, 'type': 'table' if isinstance(item, TableItem) else 'text',
                 'content': content, 'page_numbers': pages}
        if isinstance(item, TableItem):
            block['table_data'] = item.data.model_dump(mode='json')
            block['source_regions'] = [
                {'page': p.page_no, 'bbox': list(p.bbox.to_top_left_origin(doc.pages[p.page_no].size.height).as_tuple())}
                for p in item.prov]
            from .sop_tables import headers_for_table
            block['header_cells'] = headers_for_table(block, [h for p in pages for h in source_headers.get(p, [])])
            if not digital:
                from .sop_table_ocr import recover_header_cells, recover_number_cells
                block['number_cells'] = recover_number_cells(block, source, configuration)
                block['header_cells'].extend(recover_header_cells(block, source, configuration))
        blocks.append(block)
    covered = {p for b in blocks for p in b['page_numbers']}
    from .docling_layout import missing_activity_grids
    for block in blocks:
        if block['type'] == 'table':
            block['activity_grid'] = any(not missing_activity_grids([block], {page: [region]})
                                         for page in block['page_numbers']
                                         for region in detected_regions.get(page, []))
    for page_number in missing_activity_grids(blocks, detected_regions):
        warnings.append(f'DOCLING_GRID_NOT_RECONSTRUCTED: halaman {page_number}')
    # Flowchart grids can be classified as pictures: retain their nested text,
    # but do not certify flattened labels as a reconstructed activity table.
    if any(p.children for p in doc.pictures) and not any(b['type'] == 'table' for b in blocks):
        warnings.append('DOCLING_NO_STRUCTURED_TABLES: tabel/bagan perlu pemeriksaan; teks tidak membuktikan hubungan sel.')
    if covered != set(doc.pages):
        warnings.append('Halaman tanpa blok teks/tabel: ' + str(sorted(set(doc.pages) - covered)))
    success = str(result.status.value) == 'success' and bool(blocks) and not warnings
    payload = {'status': 'COMPLETE' if success else 'PARTIAL' if blocks else 'FAILED',
               'warnings': warnings, 'blocks': blocks, 'page_count': len(doc.pages),
               'markdown': doc.export_to_markdown(), 'docling_json': doc.export_to_dict(),
               'effective_options': {'do_ocr': not digital, 'native_text_first': digital, 'device': 'cpu',
                                     'activity_grid_pages': sorted(detected_regions),
                                     'activity_grid_regions': detected_regions}}
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    temporary.replace(output)


if __name__ == '__main__':
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
