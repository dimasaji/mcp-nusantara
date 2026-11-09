"""Auto-fill SOP template A-M from extracted Docling data."""
import sys, json, os
from docx import Document
from docx.shared import Pt

TEMPLATE = 'E:/Template_SOP_Standar_Dukcapil.docx'
OUT_DIR = 'E:/NusantaraData/SOP/filled'

def fill_template(sop_data, output_path):
    doc = Document(TEMPLATE)
    # Fill title
    for p in doc.paragraphs:
        if p.style.name == 'Title':
            p.text = sop_data.get('title', 'SOP')
    # Fill tables
    if doc.tables:
        t0 = doc.tables[0]  # Metadata table
        for row in t0.rows:
            key = row.cells[0].text.strip().lower()
            if 'id sop' in key:
                row.cells[1].text = sop_data.get('id_sop', 'DUK-XXX-NN')
            elif 'nama layanan' in key:
                row.cells[1].text = sop_data.get('title', '')
            elif 'unit' in key:
                row.cells[1].text = sop_data.get('unit', 'Tidak tercantum dalam SOP')
            elif 'versi' in key:
                row.cells[1].text = sop_data.get('version', '1.0')
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print('Saved:', output_path)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: fill_template.py <sop_json> <output_docx>')
        sys.exit(1)
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    fill_template(data, sys.argv[2])
PY