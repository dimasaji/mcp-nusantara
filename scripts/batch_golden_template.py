"""Generate Golden Set + Template A-M for all processed SOPs."""
import os, json, subprocess, sys

OUT_DIR = 'E:/NusantaraData/SOP'
PYTHON = 'C:/Users/dmaza/mcp-starter/.venv-docling/Scripts/python.exe'
BASE = 'C:/Users/dmaza/mcp-starter'

from app.knowledge.engine import KnowledgeEngine
k = KnowledgeEngine()
docs = k.list_documents().documents
print('Total SOPs:', len(docs))

for d in docs:
    doc_id = d.document_id
    title = d.title
    data_path = os.path.join(OUT_DIR, doc_id.replace('DOC-SHA256-','').replace('sop_','')[:12] + '_data.json')
    # Use a simpler naming
    safe = doc_id.replace('/','_').replace('\\','_')
    data_path = os.path.join(OUT_DIR, safe + '_data.json')
    golden_path = os.path.join(OUT_DIR, safe + '_golden_set.json')
    filled_path = os.path.join(OUT_DIR, safe + '_filled.docx')
    
    # Create data json
    data = {'id_sop': doc_id, 'title': title, 'unit': title, 'version': '1.0'}
    json.dump(data, open(data_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    
    # Run golden set
    r1 = subprocess.run([PYTHON, os.path.join(BASE,'scripts','generate_golden_set.py'), data_path, golden_path], capture_output=True, text=True, cwd=BASE)
    # Run template fill
    r2 = subprocess.run([PYTHON, os.path.join(BASE,'scripts','fill_template.py'), data_path, filled_path], capture_output=True, text=True, cwd=BASE)
    
    status = 'OK' if r1.returncode==0 and r2.returncode==0 else 'ERR'
    print('%s: %s' % (title[:40], status))

print('Done')
PY