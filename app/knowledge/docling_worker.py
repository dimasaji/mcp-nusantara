"""CPU-only subprocess entrypoint; paths originate solely in backend storage."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def convert(source: Path, output: Path):
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
    from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
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
                                         tesseract_cmd=command, path=configuration['tessdata_path']))
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options, pipeline_cls=ruled_grid_pipeline())})
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
        blocks.append(block)
    covered = {p for b in blocks for p in b['page_numbers']}
    from .docling_layout import activity_grid_regions
    for page_number in activity_grid_regions(source):
        tables = [b for b in blocks if b['type'] == 'table' and page_number in b['page_numbers']]
        if not tables:
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
               'effective_options': {'do_ocr': not digital, 'native_text_first': digital, 'device': 'cpu'}}
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    temporary.replace(output)


if __name__ == '__main__':
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
