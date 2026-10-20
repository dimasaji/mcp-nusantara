import urllib.request
import json

qs = ['Siapa presiden Indonesia?', 'Apa itu Nusantara?', 'Apa fungsi CPU?']

for q in qs:
    p = json.dumps({
        'session_id': 't1',
        'user_input': q,
        'model': 'llm_model'  # will be replaced
    }).encode()
    r = urllib.request.Request(
        'http://localhost:8000/v1/chat',
        data=p,
        headers={'Content-Type': 'application/json'}
    )
    try:
        d = urllib.request.urlopen(r, timeout=30).read().decode()
        j = json.loads(d)
        resp = j.get('response', '')
        print(f'=== {q} ===')
        print(f'Provider: {j.get("provider_status")} | Model: {j.get("model")}')
        print(f'Response: {resp[:100]}...')
        print()
    except Exception as e:
        print(f'Error: {e}')
        print()
