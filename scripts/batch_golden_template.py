"""Generate Golden Set + Template A-M for all processed SOPs."""
import os, json, subprocess, sys

OUT_DIR = 'C:/Users/dmaza/mcp-starter/output'
BASE = 'C:/Users/dmaza/mcp-starter'
PYTHON = 'C:/Users/dmaza/mcp-starter/.venv-docling/Scripts/python.exe'

from app.knowledge.engine import KnowledgeEngine
k = KnowledgeEngine()
docs = k.list_documents().documents
print('Total SOPs:', len(docs))

os.makedirs(OUT_DIR, exist_ok=True)
ok = 0
for d in docs:
    doc_id = d.document_id
    title = d.title
    safe = doc_id.replace('/','_').replace('\\','_')
    data_path = os.path.join(OUT_DIR, safe + '_data.json')
    golden_path = os.path.join(OUT_DIR, safe + '_golden_set.json')
    filled_path = os.path.join(OUT_DIR, safe + '_filled.docx')
    
    data = {'id_sop': doc_id, 'title': title, 'unit': title, 'version': '1.0'}
    json.dump(data, open(data_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    
    r1 = subprocess.run([PYTHON, os.path.join(BASE,'scripts','generate_golden_set.py'), data_path, golden_path], capture_output=True, text=True, cwd=BASE)
    r2 = subprocess.run([PYTHON, os.path.join(BASE,'scripts','fill_template.py'), data_path, filled_path], capture_output=True, text=True, cwd=BASE)
    
    status = 'OK' if r1.returncode==0 and r2.returncode==0 else 'ERR'
    if status == 'OK': ok += 1
    print('%s: %s' % (title[:40], status))

print('Done: %d/%d OK' % (ok, len(docs)))
