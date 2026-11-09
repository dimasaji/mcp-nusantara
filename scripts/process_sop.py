"""Automated SOP processing via Nusantara pipeline API."""
import sys, json, time, urllib.request, hashlib, os

TOKEN = os.environ.get('NUSANTARA_TEST_ADMIN_TOKEN', 'R4H4Si4.')
BASE = 'http://127.0.0.1:8000'

def api(method, path, data=None, headers=None):
    h = {'X-Admin-Token': TOKEN}
    if headers: h.update(headers)
    if data is not None:
        req = urllib.request.Request(BASE+path, data=data if isinstance(data, bytes) else json.dumps(data).encode(), headers={**h, 'Content-Type':'application/json'})
    else:
        req = urllib.request.Request(BASE+path, headers=h)
    req.get_method = lambda: method
    try:
        r = urllib.request.urlopen(req, timeout=300)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.read() else {}

def process_pdf(pdf_path):
    name = os.path.basename(pdf_path)
    raw = open(pdf_path, 'rb').read()
    # Upload
    req = urllib.request.Request(BASE+'/v1/knowledge/pipeline/documents', data=raw, headers={'X-Admin-Token':TOKEN, 'X-Document-Name':name, 'Content-Type':'application/pdf'})
    r = urllib.request.urlopen(req, timeout=120)
    d = json.loads(r.read())
    doc_id = d['document_id']
    status = d['status']
    if status == 'DUPLICATE':
        print(f'{name}: DUPLICATE (already processed)')
        return doc_id, 'DUPLICATE'
    if status == 'FAILED':
        print(f'{name}: FAILED at upload: {d.get("reason")}')
        return doc_id, 'FAILED'
    # Wait for extraction
    for _ in range(60):
        time.sleep(10)
        code, detail = api('GET', f'/v1/knowledge/pipeline/reviews/{doc_id}')
        ext = detail.get('extraction', {}).get('status')
        if ext in ('COMPLETE', 'FAILED'):
            break
    else:
        print(f'{name}: extraction timeout')
        return doc_id, 'TIMEOUT'
    if ext == 'FAILED':
        print(f'{name}: extraction FAILED: {detail.get("extraction",{}).get("error","")[:100]}')
        return doc_id, 'FAILED'
    ver = detail['version_id']
    title = detail.get('title', name)
    # content_ok
    api('POST', f'/v1/knowledge/pipeline/reviews/{doc_id}/decision', {'version_id':ver,'action':'content_ok','note':'Auto: extraction complete.'})
    # metadata
    absent = {'status':'not_stated','value':None,'page_number':None,'note':'Tidak tercantum dalam dokumen.'}
    md = {'schema_version':1, 'logical_sop_id': doc_id, 'official_title':{'status':'present','value':title,'page_number':1,'note':'Judul dari nama file.'},
          'institution':dict(absent),'unit':dict(absent),'sop_number':dict(absent),'jurisdiction':dict(absent),
          'issued_on':dict(absent),'effective_on':dict(absent),'expires_on':dict(absent),'revision':dict(absent),
          'validity':'confirmed_current','validity_note':'Metadata dikonfirmasi otomatis untuk pengujian E2E.'}
    api('POST', f'/v1/knowledge/pipeline/reviews/{doc_id}/metadata', {'version_id':ver,'metadata':md})
    # approve
    code, res = api('POST', f'/v1/knowledge/pipeline/reviews/{doc_id}/decision', {'version_id':ver,'action':'approve','note':'Auto-approved for E2E test.'})
    final_status = res.get('status') if isinstance(res, dict) else 'ERROR'
    print(f'{name}: {final_status} (blocks={len(detail.get("extracted_blocks",[]))})')
    return doc_id, final_status

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: process_sop.py <pdf_path>')
        sys.exit(1)
    process_pdf(sys.argv[1])
