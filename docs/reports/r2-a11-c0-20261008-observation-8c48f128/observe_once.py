"""C0 evidence collector: one GET, no application import, retries or redirect follow."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import http.client
import json
import re
import subprocess

out = Path(__file__).resolve().parent
root = out.parents[2]
def now(): return datetime.now(timezone.utc).isoformat()
def save(name, value): (out/name).write_text(json.dumps(value, indent=2), encoding='utf-8')
git = r'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe'
def git_read(*args):
    p = subprocess.run([git,*args],cwd=root,capture_output=True,text=True,check=True)
    return {'stdout':p.stdout,'stderr':p.stderr}
save('GIT_BEFORE.json',{k:git_read(*v) for k,v in {
    'root':['rev-parse','--show-toplevel'],'branch':['branch','--show-current'],
    'head':['rev-parse','HEAD'],'status':['status','--porcelain=v1','--untracked-files=normal'],
    'staged':['diff','--cached','--name-only']}.items()})
assert git_read('rev-parse','HEAD')['stdout'].strip()=='8f86bed38aca8e6b5a0bd365f3351ac9c0825eab'
assert git_read('branch','--show-current')['stdout'].strip()=='codex/fullroot-control-20261007'
assert Path(git_read('rev-parse','--show-toplevel')['stdout'].strip()).resolve()==root
def source_files():
    rows=json.loads((root/'docs/reports/r2-a10-isolation-fix-20261008/SOURCE_BEFORE.json').read_text(encoding='utf-8-sig'))
    result={}
    for row in rows:
        p=Path(row['path'])
        assert p.parts[0] in {'app','tests','control-plane','scripts','service'} or str(p).replace('\\','/') in {'pyproject.toml','nusantara-models/indobert_worker.py'}
        assert p.suffix.lower() not in {'.db','.db-wal','.db-shm'} and not p.is_absolute() and '..' not in p.parts
        result[row['path']]=hashlib.sha256((root/p).read_bytes()).hexdigest()
    return result
before_source=source_files()
save('SOURCE_BEFORE.json',before_source)
def source_snapshot():
    files=[p for p in (root/'app').rglob('*') if p.is_file() and p.suffix in {'.py','.json','.html','.css','.js'}]
    files += [root/'pyproject.toml',root/'nusantara-models/indobert_worker.py']
    digest=hashlib.sha256()
    for p in sorted(files,key=lambda p:p.relative_to(root).as_posix()):
        if not p.is_file() or p.is_symlink(): continue
        try: p.resolve().relative_to(root)
        except ValueError: continue
        name=p.relative_to(root).as_posix().encode(); content=p.read_bytes()
        digest.update(len(name).to_bytes(8,'big')); digest.update(name)
        digest.update(len(content).to_bytes(8,'big')); digest.update(content)
    return 'sha256:'+digest.hexdigest()
save('SOURCE_SNAPSHOT.json',{'class':'SOURCE','current_disk_snapshot':source_snapshot(),'observed_at':now(),'not_active_process_build':True})
for label,p in [('contract',root/'docs/commands/R2-A10 CLOSURE & R2-A11 EXECUTION CONTRACT.md'),('phase_a_report',root/'docs/reports/r2-a11-phase-a-discovery-20261008/REPORT.md')]:
    save(label+'_reference.json',{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
ps=r'''$ErrorActionPreference='Stop'; $items=@(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue); $rows=@(foreach($item in $items){$proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($item.OwningProcess)"; [pscustomobject]@{address=$item.LocalAddress;port=$item.LocalPort;pid=$item.OwningProcess;parent_pid=$proc.ParentProcessId;executable=$proc.ExecutablePath;command_line=$proc.CommandLine;start_time_utc=$proc.CreationDate.ToUniversalTime().ToString('o')}}); ConvertTo-Json -InputObject $rows -Depth 4 -Compress'''
def observe():
    p=subprocess.run(['powershell.exe','-NoProfile','-Command',ps],capture_output=True,text=True,check=True)
    return {'observed_at':now(),'class':'PROCESS_OBSERVED','listeners':json.loads(p.stdout),'stderr':p.stderr}
before=observe(); save('PROCESS_BEFORE.json',before)
listeners=before['listeners']
assert len(listeners)==1 and listeners[0]['address']=='127.0.0.1' and listeners[0]['pid'] and listeners[0]['start_time_utc']
assert 'uvicorn app.main:app' in listeners[0]['command_line']
ledger=out/'REQUEST_ATTEMPT.json'
with ledger.open('x',encoding='utf-8') as f:
    json.dump({'method':'GET','url':'http://127.0.0.1:8000/v1/runtime/attestation','started_at':now(),'max_requests':1,'retries':0,'redirect_follow':False,'max_body_bytes':262144},f,indent=2)
conn=http.client.HTTPConnection('127.0.0.1',8000,timeout=10)
metadata={'started_at':now(),'request_attempts':1,'retry':False,'redirect_follow':False}
try:
    conn.request('GET','/v1/runtime/attestation',headers={'Accept':'application/json','Connection':'close'})
    response=conn.getresponse()
    body=response.read(262145)
    metadata.update(status=response.status,reason=response.reason,received_at=now(),body_bytes=len(body),body_truncated=len(body)>262144,
                    headers={k:v for k,v in response.getheaders() if k.lower() in {'date','content-type','content-length','server','x-request-id'}})
    raw=body[:262144].decode('utf-8',errors='replace')
    redactions=[]
    try:
        value=json.loads(raw)
        def redact(v):
            if isinstance(v,dict):
                for k,x in v.items():
                    if re.search(r'password|credential|secret|(^|_)token($|_)|authorization|api.?key',k,re.I):
                        v[k]='[REDACTED]'; redactions.append(k)
                    else: redact(x)
            elif isinstance(v,list):
                for x in v: redact(x)
        redact(value)
        if redactions: raw=json.dumps(value,indent=2)
    except ValueError: pass
    raw,n=re.subn(r'(?i)Bearer\s+[A-Za-z0-9._~+/-]+','Bearer [REDACTED]',raw)
    metadata['redactions']=redactions+(['bearer-value'] if n else [])
    (out/'RESPONSE_RAW.txt').write_text(raw,encoding='utf-8')
    metadata['preserved_body_sha256']=hashlib.sha256(raw.encode()).hexdigest()
except Exception as exc:
    metadata.update(error_type=type(exc).__name__,error=str(exc),received_at=now())
finally:
    conn.close()
    save('HTTP_RESULT.json',metadata)
    save('PROCESS_AFTER.json',observe())
after_source=source_files()
save('SOURCE_AFTER.json',after_source)
save('SOURCE_STABILITY.json',{'monitored':len(before_source),'changed':[p for p in before_source if before_source[p]!=after_source[p]],'protected_files_read':False})
save('GIT_AFTER.json',{'head':git_read('rev-parse','HEAD'),'staged':git_read('diff','--cached','--name-only'),'tracked_status':git_read('status','--short','--untracked-files=no')})
print(json.dumps(metadata))
