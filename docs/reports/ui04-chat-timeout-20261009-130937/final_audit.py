"""Use explicit UTF-8 and LF for trustworthy audit/diff on Windows."""
import difflib
import hashlib
import importlib.util
import json
import sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
FILES=['control-plane/src/api.ts','control-plane/tests/assistant.test.tsx']
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,ensure_ascii=False)
before=read(OUT/'BASELINE.json')
spec=importlib.util.spec_from_file_location('evidence',OUT/'evidence.py')
sys.argv.append('snapshot_only')
evidence=importlib.util.module_from_spec(spec);spec.loader.exec_module(evidence)
after=evidence.snapshot();b=before['snapshot']['sha256'];a=after['sha256']
changes={'modified':sorted(p for p in a.keys()&b.keys() if a[p]!=b[p]),'removed':sorted(b.keys()-a.keys()),'added':sorted(a.keys()-b.keys())}
patch=''.join(''.join(difflib.unified_diff((OUT/('before-'+Path(p).name)).read_text(encoding='utf-8').splitlines(True),(ROOT/p).read_text(encoding='utf-8').splitlines(True),fromfile='a/'+p,tofile='b/'+p)) for p in FILES)
with (OUT/'UI04_EXACT_LF.diff').open('xb') as stream:stream.write(patch.encode('utf-8'))
write('CHANGE_AUDIT_UTF8.json',{'timestamp':datetime.now(timezone(timedelta(hours=7))).isoformat(),'changes':changes,'unauthorized_modified':[p for p in changes['modified'] if p not in FILES],'status':'PASS_SCOPED' if changes['modified']==FILES and not changes['added'] and not changes['removed'] else 'REVIEW_REQUIRED','before_hashes':{p:sha(OUT/('before-'+Path(p).name)) for p in FILES},'after_hashes':{p:sha(ROOT/p) for p in FILES},'errors':after['errors'],'head_after':evidence.baseline.git('rev-parse','HEAD'),'note':'Supersedes initial CHANGE_AUDIT.json decoded with Windows default cp1252. Apparent docs filename changes were decoding artifacts, not filesystem changes. Earlier diffs used CRLF/default decoding; authoritative diff is UI04_EXACT_LF.diff encoded UTF-8/LF. Failed checks preserved.'})
print(json.dumps({'changes':changes,'hashes':{p:sha(ROOT/p) for p in FILES}}))
