"""Performance baseline for SOP batch processing."""
import sys, time, os, json, urllib.request, subprocess

TOKEN = 'R4H4Si4.'
BASE = 'http://127.0.0.1:8000'

def process_one(pdf_path):
    name = os.path.basename(pdf_path)
    raw = open(pdf_path, 'rb').read()
    t0 = time.perf_counter()
    # Upload
    req = urllib.request.Request(BASE+'/v1/knowledge/pipeline/documents', data=raw, headers={'X-Admin-Token':TOKEN, 'X-Document-Name':name, 'Content-Type':'application/pdf'})
    r = urllib.request.urlopen(req, timeout=120)
    d = json.loads(r.read())
    doc_id = d['document_id']
    status = d['status']
    if status == 'DUPLICATE':
        elapsed = time.perf_counter() - t0
        print('%s: DUPLICATE (%.1fs)' % (name, elapsed))
        return {'file':name, 'status':'DUPLICATE', 'time_s':round(elapsed,1)}
    if status == 'FAILED':
        elapsed = time.perf_counter() - t0
        print('%s: FAILED at upload (%.1fs): %s' % (name, elapsed, d.get('reason')))
        return {'file':name, 'status':'FAILED', 'time_s':round(elapsed,1), 'reason':d.get('reason')}
    # Wait for extraction
    for i in range(60):
        time.sleep(10)
        req2 = urllib.request.Request(BASE+'/v1/knowledge/pipeline/reviews/'+doc_id, headers={'X-Admin-Token':TOKEN})
        detail = json.loads(urllib.request.urlopen(req2, timeout=60).read())
        ext = detail.get('extraction', {}).get('status')
        if ext in ('COMPLETE', 'FAILED'):
            break
    elapsed = time.perf_counter() - t0
    blocks = len(detail.get('extracted_blocks', []))
    print('%s: %s (%.1fs, %d blocks)' % (name, ext, elapsed, blocks))
    return {'file':name, 'status':ext, 'time_s':round(elapsed,1), 'blocks':blocks}

if __name__ == '__main__':
    pdfs = sys.argv[1:]
    if not pdfs:
        print('Usage: perf_baseline.py <pdf1> <pdf2> ...')
        sys.exit(1)
    results = []
    t0 = time.perf_counter()
    for pdf in pdfs:
        r = process_one(pdf)
        results.append(r)
    total = time.perf_counter() - t0
    print('\n=== BASELINE ===')
    print('SOPs processed:', len(results))
    print('Total time: %.1fs (%.1f min)' % (total, total/60))
    print('Avg time per SOP: %.1fs' % (total/len(results)))
    print('Peak memory: N/A (psutil not available)')
    json.dump({'results':results,'total_s':round(total,1),'avg_s':round(total/len(results),1)}, open('E:/NusantaraData/SOP/perf_baseline.json','w'), indent=2)
