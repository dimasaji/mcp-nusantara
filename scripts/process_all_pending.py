"""Process all pending SOPs through review -> content_ok -> metadata -> approve."""
import time, json, urllib.request, os
from app.knowledge.engine import KnowledgeEngine
from app.knowledge.sop_review import SOPReview

TOKEN = 'R4H4Si4.'
BASE = 'http://127.0.0.1:8000'

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
        body = e.read().decode()
        try: body = json.loads(body)
        except: pass
        return e.code, body
    except Exception as e:
        return 0, str(e)

k = KnowledgeEngine()
docs = k.list_documents().documents
rev = SOPReview(k)
processed = 0
for d in docs:
    doc_id = d.document_id
    title = d.title
    try:
        detail = rev.detail(doc_id)
    except Exception as e:
        print('%s: detail error %s' % (title, e))
        continue
    status = detail['status']
    if status == 'Aktif':
        continue
    if status == 'Ditunda':
        print('%s: Ditunda (skip)' % title)
        continue
    # Trigger extraction if not done
    ver = detail['version_id']
    ext_status = None
    if detail.get('extraction_job_id'):
        # check extraction status
        code, det = api('GET', '/v1/knowledge/pipeline/reviews/'+doc_id)
        if isinstance(det, dict):
            ext_status = det.get('extraction', {}).get('status') if isinstance(det.get('extraction'), dict) else None
    if ext_status not in ('COMPLETE',):
        # process
        code, res = api('POST', '/v1/knowledge/pipeline/reviews/'+doc_id+'/process', {'version_id': ver})
        print('%s: process -> %s' % (title, res.get('status') if isinstance(res, dict) else res))
        # wait for extraction
        for _ in range(60):
            time.sleep(10)
            code, det = api('GET', '/v1/knowledge/pipeline/reviews/'+doc_id)
            if isinstance(det, dict):
                ext_status = det.get('extraction', {}).get('status') if isinstance(det.get('extraction'), dict) else None
                if ext_status in ('COMPLETE', 'FAILED', 'PARTIAL'):
                    break
        if ext_status != 'COMPLETE':
            print('%s: extraction %s (skip)' % (title, ext_status))
            continue
    # Re-read detail
    detail = rev.detail(doc_id)
    ver = detail['version_id']
    if not detail['can_approve']:
        # content_ok
        api('POST', '/v1/knowledge/pipeline/reviews/'+doc_id+'/decision', {'version_id':ver,'action':'content_ok','note':'Auto: extraction complete.'})
        detail = rev.detail(doc_id)
        ver = detail['version_id']
        if not detail['can_approve']:
            # confirm metadata
            absent = {'status':'not_stated','value':None,'page_number':None,'note':'Tidak tercantum.'}
            md = {'schema_version':1, 'logical_sop_id': doc_id, 'official_title':{'status':'present','value':title,'page_number':1,'note':'Judul dari file.'},
                  'institution':dict(absent),'unit':dict(absent),'sop_number':dict(absent),'jurisdiction':dict(absent),
                  'issued_on':dict(absent),'effective_on':dict(absent),'expires_on':dict(absent),'revision':dict(absent),
                  'validity':'confirmed_current','validity_note':'Auto metadata for batch.'}
            api('POST', '/v1/knowledge/pipeline/reviews/'+doc_id+'/metadata', {'version_id':ver,'metadata':md})
            detail = rev.detail(doc_id)
            ver = detail['version_id']
    if detail['can_approve']:
        code, res = api('POST', '/v1/knowledge/pipeline/reviews/'+doc_id+'/decision', {'version_id':ver,'action':'approve','note':'Auto-approved for batch.'})
        final = res.get('status') if isinstance(res, dict) else res
        print('%s: %s' % (title, final))
        processed += 1
    else:
        print('%s: cannot approve (status=%s)' % (title, detail['status']))

print('\nProcessed: %d' % processed)
PY