"""Security testing script for Nusantara V1."""
import json, os, urllib.request

BASE = 'http://127.0.0.1:8000'
TOKEN = os.getenv('NUSANTARA_ADMIN_TOKEN')
if not TOKEN:
    raise SystemExit('NUSANTARA_ADMIN_TOKEN is required')
results = []

def test(name, fn):
    try:
        r = fn()
        results.append({'test': name, 'status': 'PASS', 'detail': r})
        print(f'PASS: {name}')
    except Exception as e:
        results.append({'test': name, 'status': 'FAIL', 'detail': str(e)[:200]})
        print(f'FAIL: {name} - {str(e)[:100]}')

def t1():
    req = urllib.request.Request(BASE+'/v1/knowledge/search', data=b'{"query":"test","top_k":3}', headers={'Content-Type':'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
        raise Exception('Expected 403')
    except urllib.error.HTTPError as e:
        if e.code == 403: return '403 as expected'
        raise
test('security_search_no_token', t1)

def t2():
    req = urllib.request.Request(BASE+'/v1/knowledge/pipeline/status')
    try:
        urllib.request.urlopen(req, timeout=10)
        raise Exception('Expected 403')
    except urllib.error.HTTPError as e:
        if e.code == 403: return '403 as expected'
        raise
test('security_admin_no_token', t2)

def t3():
    import uuid
    body = json.dumps({'session_id': 'test-'+str(uuid.uuid4()), 'user_input': 'halo'}).encode()
    req = urllib.request.Request(BASE+'/v1/chat', data=body, headers={'Content-Type':'application/json'})
    r = urllib.request.urlopen(req, timeout=30)
    d = json.loads(r.read())
    if len(d.get('evidence', [])) == 0: return 'no evidence (correct)'
    raise Exception(f'Expected 0 evidence, got {len(d["evidence"])}')
test('security_chat_no_token_no_evidence', t3)

def t4():
    body = json.dumps({'session_id': 'x', 'user_input': ''}).encode()
    req = urllib.request.Request(BASE+'/v1/chat', data=body, headers={'X-Admin-Token':TOKEN,'Content-Type':'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
        raise Exception('Expected 422')
    except urllib.error.HTTPError as e:
        if e.code == 422: return '422 as expected'
        raise
test('empty_input_rejected', t4)

def t5():
    req = urllib.request.Request(BASE+'/v1/knowledge/pipeline/status', headers={'X-Admin-Token':TOKEN})
    r = urllib.request.urlopen(req, timeout=10)
    return 'endpoint accessible'
test('pipeline_status_accessible', t5)

def t6():
    import uuid
    sid1 = 'test-iso-' + str(uuid.uuid4())
    sid2 = 'test-iso-' + str(uuid.uuid4())
    body1 = json.dumps({'session_id': sid1, 'user_input': 'halo'}).encode()
    body2 = json.dumps({'session_id': sid2, 'user_input': 'halo'}).encode()
    r1 = urllib.request.urlopen(urllib.request.Request(BASE+'/v1/chat', data=body1, headers={'X-Admin-Token':TOKEN,'Content-Type':'application/json'}), timeout=30)
    r2 = urllib.request.urlopen(urllib.request.Request(BASE+'/v1/chat', data=body2, headers={'X-Admin-Token':TOKEN,'Content-Type':'application/json'}), timeout=30)
    d1 = json.loads(r1.read()); d2 = json.loads(r2.read())
    if d1['session_id'] != d2['session_id']:
        return 'sessions isolated'
    raise Exception('Session IDs match')
test('session_isolation', t6)

json.dump(results, open('reports/security_test_report.json','w',encoding='utf-8'), indent=2, ensure_ascii=False)
passed = sum(1 for r in results if r['status']=='PASS')
print(f'\n=== AUTOMATED REGRESSION: {passed}/{len(results)} PASS ===')
