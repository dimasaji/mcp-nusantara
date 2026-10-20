"""Exercise the requested conversation against the actual local V1 API."""
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import argparse,json,httpx

parser=argparse.ArgumentParser();parser.add_argument('--baseline',action='store_true');args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
folder=root/'artifacts/sop-conversation'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
folder.mkdir(parents=True,exist_ok=False)
turns=[]
with httpx.Client(base_url='http://127.0.0.1:8765',timeout=90) as c:
    assert c.get('/v1/control-plane/model-status').json()['provider']=='ollama','Local provider required'
    session='sop-conversation-'+uuid4().hex
    for question in ['Mau minta data pribadi, bawa apa?','Kalau prosesnya?','Berapa lama?','Bisa online?']:
        response=c.post('/v1/chat',json={'user_input':question,'session_id':session})
        result=response.json();turns.append({'question':question,'http_status':response.status_code,'result':result})
        print(json.dumps({'question':question,'response':result.get('response'),'grounding':result.get('grounding'),
                          'provider_status':result.get('provider_status'),'intent':result.get('understanding',{}).get('intent')},ensure_ascii=False),flush=True)
(folder/('baseline.json' if args.baseline else 'api.json')).write_text(json.dumps(turns,indent=2,ensure_ascii=False),encoding='utf-8')
print('ARTIFACT:',folder.relative_to(root),flush=True)
if not args.baseline:
    assert all(t['http_status']==200 for t in turns)
    assert all(any('PIAK-03' in e['title'] for e in t['result'].get('evidence',[])) for t in turns)
    assert 'surat permohonan' in turns[0]['result']['response'].lower()
    assert '3' in turns[2]['result']['response'] and 'hari kerja' in turns[2]['result']['response'].lower()
    assert all(t['result']['grounding']['grounded'] for t in turns[:3])
    assert not any(x in turns[3]['result']['response'].lower() for x in ['bisa online','dapat online','tidak bisa online'])
