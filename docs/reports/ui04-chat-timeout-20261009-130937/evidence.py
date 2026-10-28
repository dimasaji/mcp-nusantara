"""Capture evidence only, without importing application code."""
import difflib
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
FILES=['control-plane/src/api.ts','control-plane/tests/assistant.test.tsx']
def now():return datetime.now(timezone(timedelta(hours=7))).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,ensure_ascii=False)
spec=importlib.util.spec_from_file_location('baseline',ROOT/'docs/reports/v1-functional-closure-20261009-101736/prepare_baseline.py')
baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline);baseline.OUT=OUT
def snapshot():
    data=baseline.snapshot()
    for rel in ['control-plane/dist','control-plane/tests','control-plane/e2e','control-plane/vitest.config.ts','control-plane/tsconfig.json','config','service','.dockerignore','.env.example','ROLLBACK_PLAN.md']:
        base=ROOT/rel
        for p in [base] if base.is_file() else base.rglob('*'):
            if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:data['sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    return data
if sys.argv[1]=='before':
    for rel in FILES:
        with (OUT/('before-'+Path(rel).name)).open('xb') as stream:stream.write((ROOT/rel).read_bytes())
    write('BASELINE.json',{'timestamp':now(),'head':baseline.git('rev-parse','HEAD'),'git_status':baseline.git('status','--short'),'snapshot':snapshot(),'before_hashes':{p:sha(ROOT/p) for p in FILES},'preexisting_target_git_diff':baseline.git('diff','--',*FILES),'note':'Target files already part of untracked control-plane directory; use captured bytes for task-only diff, not Git HEAD.'})
elif sys.argv[1]=='after':
    before=json.loads((OUT/'BASELINE.json').read_text());after=snapshot();b=before['snapshot']['sha256'];a=after['sha256']
    changes={'modified':sorted(p for p in a.keys()&b.keys() if a[p]!=b[p]),'removed':sorted(b.keys()-a.keys()),'added':sorted(a.keys()-b.keys())}
    patches=[]
    for rel in FILES:
        original=(OUT/('before-'+Path(rel).name)).read_text();final=(ROOT/rel).read_text()
        patches.extend(difflib.unified_diff(original.splitlines(True),final.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    with (OUT/'UI04_TASK_ONLY.diff').open('x',encoding='utf-8') as stream:stream.write(''.join(patches))
    write('CHANGE_AUDIT.json',{'timestamp':now(),'head_after':baseline.git('rev-parse','HEAD'),'git_after':baseline.git('status','--short'),'changes':changes,'authorized_files':FILES,'unauthorized_modified':[p for p in changes['modified'] if p not in FILES],'before_hashes':before['before_hashes'],'after_hashes':{p:sha(ROOT/p) for p in FILES},'read_errors':after['errors'],'scope':'New evidence directory excluded; existing source/tests/reports/config/cache/bundle checked. Active DB/environment secret values not read. No claimed full filesystem coverage.'})
    print(json.dumps({'changes':changes,'hashes':{p:sha(ROOT/p) for p in FILES}},indent=2))
