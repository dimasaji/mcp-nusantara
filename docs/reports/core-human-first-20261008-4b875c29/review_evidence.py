"""Read-only attribution and routing probes; no services/providers/knowledge."""
import difflib
import hashlib
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[3]
out=Path(__file__).parent
sys.path.insert(0,str(root))
from app.devcore.router import plan

requests=('Periksa masalah RAG dan perbaiki yang aman.',
          'Baca app/main.py dan jelaskan.', 'Apa itu KTP-el?')
probes=[]
for text in requests:
    value=plan(text)
    probes.append({'input':text,'handled':value.handled,'intent':value.intent,
                   'actions':value.actions,'modify_requested':value.modify_requested})
(out/'ROUTING_DISCOVERY.json').write_text(json.dumps({'classification':'PURE_ROUTER_NO_DISPATCH',
    'results':probes,'live_requests':0,'provider_calls':0},indent=2),encoding='utf-8')
before=(out/'core.py.before').read_text(encoding='utf-8')
after=(root/'app/devcore/core.py').read_text(encoding='utf-8')
diff=''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),
    fromfile='before/app/devcore/core.py',tofile='after/app/devcore/core.py'))
name='tests/v2/test_devcore_grounding_response.py'
new=(root/name).read_text(encoding='utf-8')
diff+=''.join(difflib.unified_diff([],new.splitlines(keepends=True),fromfile='/dev/null',tofile=name))
(out/'IMPLEMENTATION.diff').write_text(diff,encoding='utf-8')
baseline=json.loads((out/'FILES_BEFORE.json').read_text(encoding='utf-8-sig'))
comparison=[]
for record in baseline:
    current=hashlib.sha256((root/record['path']).read_bytes()).hexdigest()
    comparison.append({'path':record['path'],'before':record['sha256'],'after':current,
                       'unchanged':current==record['sha256']})
(out/'FILES_COMPARISON.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
print(json.dumps({'monitored_files':len(comparison),
    'changed_existing':[r['path'] for r in comparison if not r['unchanged']],
    'test_created':name,'diff_lines':len(diff.splitlines()),'routing':probes},indent=2))
