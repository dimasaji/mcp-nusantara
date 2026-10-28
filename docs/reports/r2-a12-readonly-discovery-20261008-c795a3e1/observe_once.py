"""Exactly one read-only attestation GET. No app import, retry, redirect or proxy."""
from datetime import datetime, timezone
import hashlib
import http.client
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit

out=Path(__file__).resolve().parent
def stamp(): return datetime.now(timezone.utc).isoformat()
attempt={'endpoint':'http://127.0.0.1:8000/v1/runtime/attestation','method':'GET','started_at':stamp(),
    'max_bytes':262144,'timeout_seconds':10,'retry':False,'follow_redirect':False}
# Exclusive marker means re-executing this collector cannot send a second request.
with (out/'REQUEST_ATTEMPT.json').open('x',encoding='utf-8') as target:
    json.dump(attempt,target,indent=2)
redactions=[]
def redact(value,path='response'):
    if isinstance(value,dict):
        result={}
        for key,item in value.items():
            if re.fullmatch(r'(?i)(authorization|password|secret|token|api[_-]?key|access[_-]?token|prompt|content)',key):
                result[key]='[REDACTED]';redactions.append(path+'.'+key)
            else: result[key]=redact(item,path+'.'+key)
        return result
    if isinstance(value,list): return [redact(item,path+'[]') for item in value]
    if isinstance(value,str) and value.startswith(('http://','https://')):
        parsed=urlsplit(value)
        if parsed.username or parsed.password or parsed.query:
            redactions.append(path)
            return urlunsplit((parsed.scheme,parsed.netloc.rsplit('@',1)[-1],parsed.path,'',''))
    return value
connection=http.client.HTTPConnection('127.0.0.1',8000,timeout=10)
result={**attempt,'attempts':1}
try:
    connection.request('GET','/v1/runtime/attestation',headers={'Accept':'application/json','Connection':'close'})
    response=connection.getresponse()
    raw=response.read(262145)
    result.update(http_status=response.status,bytes_read=len(raw),truncated=len(raw)>262144,
        wire_sha256=hashlib.sha256(raw).hexdigest(),
        headers={key:response.getheader(key) for key in ('Content-Type','Date','X-Request-ID','Server')})
    if len(raw)>262144: raise ValueError('BOUNDED_RESPONSE_CAP_EXCEEDED')
    payload=json.loads(raw)
    safe=redact(payload)
    preserved=raw if not redactions else json.dumps(safe,indent=2).encode()
    (out/'RESPONSE.json').write_bytes(preserved)
    result.update(redactions=redactions,preserved_sha256=hashlib.sha256(preserved).hexdigest())
except Exception as error:
    result.update(error_type=type(error).__name__,status='NOT_VERIFIED')
finally:
    connection.close()
    result['finished_at']=stamp()
    (out/'HTTP_RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
