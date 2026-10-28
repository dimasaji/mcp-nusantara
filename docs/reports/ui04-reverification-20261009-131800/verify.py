"""Read-only Git/hash verification; reports only, no application imports."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
GIT='C:/Users/dmaza/AppData/Local/hermes/git/cmd/git.exe'
FILES=['control-plane/src/api.ts','control-plane/tests/assistant.test.tsx']
def now():return datetime.now(timezone(timedelta(hours=7))).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name,value):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)
spec=importlib.util.spec_from_file_location('baseline',ROOT/'docs/reports/v1-functional-closure-20261009-101736/prepare_baseline.py')
baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline);baseline.OUT=OUT
def snapshot():
    data=baseline.snapshot()
    for rel in ['control-plane/tests','control-plane/dist','control-plane/e2e','control-plane/vitest.config.ts','control-plane/tsconfig.json','config','.env.example','.dockerignore']:
        base=ROOT/rel
        for p in [base] if base.is_file() else base.rglob('*'):
            if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:data['sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    return data
mode=sys.argv[1]
commands=[]
args_list=[['status','--short'],['diff','--check']]
if mode=='before':args_list.append(['diff','--',*FILES])
for args in args_list:
    r=subprocess.run([GIT,'--no-optional-locks',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    commands.append({'command':[GIT,'--no-optional-locks',*args],'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
state={'timestamp':now(),'git_commands':commands,'hashes':{p:sha(ROOT/p) for p in FILES},'snapshot':snapshot()}
write(mode.upper()+'.json',state)
if mode=='after':
    before=read(OUT/'BEFORE.json');b=before['snapshot']['sha256'];a=state['snapshot']['sha256']
    changes={'modified':sorted(p for p in a.keys()&b.keys() if a[p]!=b[p]),'removed':sorted(b.keys()-a.keys()),'added':sorted(a.keys()-b.keys())}
    write('CHANGE_AUDIT.json',{'timestamp':now(),'changes_during_verification':changes,'status':'PASS_SCOPED' if not any(changes.values()) else 'REVIEW_REQUIRED','before_hashes':before['hashes'],'after_hashes':state['hashes'],'limitations':'Existing inaccessible temporary directories retained. New evidence excluded. Active runtime data/environment not opened.'})
print(json.dumps({'mode':mode,'commands':[{'command':r['command'][2:],'exit_code':r['exit_code'],'stdout_lines':len(r['stdout'].splitlines()),'stderr':r['stderr']} for r in commands],'hashes':state['hashes']},indent=2))
