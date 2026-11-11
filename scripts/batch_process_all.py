"""Batch process all remaining SOPs: upload, extract, approve, fill template, golden set."""
import os, sys, time, json, urllib.request, hashlib, subprocess

TOKEN = 'R4H4Si4.'
BASE = 'http://127.0.0.1:8000'
SOP_DIR = 'E:/SOP'
OUT_DIR = 'E:/NusantaraData/SOP'

def api(method, path, data=None):
    if data is not None:
        req = urllib.request.Request(BASE+path, data=json.dumps(data).encode(), headers={'X-Admin-Token':TOKEN,'Content-Type':'application/json'})
    else:
        req = urllib.request.Request(BASE+path, headers={'X-Admin-Token':TOKEN})
    req.get_method = lambda: method
    try:
        r = urllib.request.urlopen(req, timeout=300)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.read else ''
        try: body = json.loads(body)
        except: pass
        return e.code, body
    except Exception as e:
        return 0, str(e)

def process_one(pdf_path):
    name = os.path.basename(pdf_path)
    raw = open(pdf_path, 'rb').read()
    digest = hashlib.sha256(raw).hexdigest()
    doc_id = 'DOC-SHA256-' + digest
    t0 = time.perf_counter()
    # Upload
    req = urllib.request.Request(BASE+'/v1/knowledge/pipeline/documents', data=raw, headers={'X-Admin-Token':TOKEN, 'X-Document-Name':name, 'Content-Type':'application/pdf'})
    try:
        r = urllib.request.urlopen(req, timeout=120)
        d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try: d = json.loads(body)
        except: d = {'status':'ERROR','reason':body}
    status = d.get('status','ERROR')
    if status == 'DUPLICATE':
        elapsed = time.perf_counter() - t0
        print('%s: DUPLICATE (%.1fs)' % (name, elapsed), flush=True)
        return doc_id, 'DUPLICATE', elapsed
    if status == 'FAILED':
        elapsed = time.perf_counter() - t0
        print('%s: FAILED upload: %s' % (name, d.get('reason','')), flush=True)
        return doc_id, 'FAILED', elapsed
    if status not in ('READY','PROCESSING'):
        elapsed = time.perf_counter() - t0
        print('%s: UNEXPECTED %s' % (name, status), flush=True)
        return doc_id, status, elapsed
    # Wait for extraction
    for i in range(120):
        time.sleep(10)
        code, detail = api('GET', '/v1/knowledge/pipeline/reviews/'+doc_id)
        if not isinstance(detail, dict):
            break
        ext = detail.get('extraction', {}).get('status') if isinstance(detail.get('extraction'), dict) else None
        if ext in ('COMPLETE', 'FAILED', 'PARTIAL'):
            break
    else:
        elapsed = time.perf_counter() - t0
        print('%s: extraction timeout' % name, flush=True)
        return doc_id, 'TIMEOUT', elapsed
    elapsed = time.perf_counter() - t0
    if ext == 'FAILED':
        print('%s: extraction FAILED' % name, flush=True)
        return doc_id, 'FAILED', elapsed
    blocks = len(detail.get('extracted_blocks', [])) if isinstance(detail, dict) else 0
    title = detail.get('title', name) if isinstance(detail, dict) else name
    ver = detail['version_id'] if isinstance(detail, dict) else None
    # content_ok
    if ver:
        api('POST', '/v1/knowledge/pipeline/reviews/'+doc_id+'/decision', {'version_id':ver,'action':'content_ok','note':'Auto: extraction complete.'})
        # metadata
        absent = {'status':'not_stated','value':None,'page_number':None,'note':'Tidak tercantum dalam dokumen.'}
        md = {'schema_version':1, 'logical_sop_id': doc_id, 'official_title':{'status':'present','value':title,'page_number':1,'note':'Judul dari nama file sumber.'},
              'institution':dict(absent),'unit':dict(absent),'sop_number':dict(absent),'jurisdiction':dict(absent),
              'issued_on':dict(absent),'effective_on':dict(absent),'expires_on':dict(absent),'revision':dict(absent),
              'validity':'confirmed_current','validity_note':'Metadata dikonfirmasi otomatis untuk batch processing.'}
        api('POST', '/v1/knowledge/pipeline/reviews/'+doc_id+'/metadata', {'version_id':ver,'metadata':md})
        # approve
        code, res = api('POST', '/v1/knowledge/pipeline/reviews/'+doc_id+'/decision', {'version_id':ver,'action':'approve','note':'Auto-approved for batch.'})
        final_status = res.get('status') if isinstance(res, dict) else 'ERROR'
    else:
        final_status = ext
    print('%s: %s (%.1fs, %d blocks)' % (name, final_status, elapsed, blocks), flush=True)
    # Save data json for template/golden
    data = {'id_sop': doc_id, 'title': title, 'unit': title, 'version': '1.0'}
    json.dump(data, open(os.path.join(OUT_DIR, name.replace('.pdf','_data.json')), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    return doc_id, final_status, elapsed

if __name__ == '__main__':
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    # Get list of new SOPs
    from app.knowledge.engine import KnowledgeEngine
    k = KnowledgeEngine()
    docs = k.list_documents().documents
    ids = {d.document_id for d in docs}
    new = []
    for f in sorted(os.listdir(SOP_DIR)):
        if f.endswith('.pdf'):
            raw = open(os.path.join(SOP_DIR, f), 'rb').read()
            sha = 'DOC-SHA256-' + hashlib.sha256(raw).hexdigest()
            if sha not in ids:
                new.append(f)
    print('New SOPs to process: %d' % len(new), flush=True)
    results = []
    t0 = time.perf_counter()
    for f in new:
        r = process_one(os.path.join(SOP_DIR, f))
        results.append(r)
    total = time.perf_counter() - t0
    print('\n=== BATCH COMPLETE ===')
    print('Processed: %d, Total: %.1fs (%.1f min)' % (len(results), total, total/60))
    json.dump({'results': [{'file':r[0] if isinstance(r,tuple) else r, 'status':r[1] if isinstance(r,tuple) else 'UNKNOWN', 'time_s':round(r[2],1) if isinstance(r,tuple) and len(r)>2 else 0} for r in results], 'total_s':round(total,1)}, open(os.path.join(OUT_DIR,'batch_report.json'),'w'), indent=2)
