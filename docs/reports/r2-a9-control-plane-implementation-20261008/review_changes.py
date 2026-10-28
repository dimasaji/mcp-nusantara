"""Owned diff and monitored source evidence; excludes databases and protected digests."""
import difflib
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[3]
out = Path(__file__).parent
owned = ['app/api/control_plane.py','app/approval/runtime_authorization.py',
    'control-plane/src/schemas.ts','control-plane/src/api.ts','control-plane/src/acceptance.ts',
    'control-plane/src/human.tsx','control-plane/src/ui.tsx']
added = ['tests/test_control_plane_attestation_binding.py','control-plane/tests/attestation.test.tsx']
before = json.loads((out/'SOURCE_BEFORE.json').read_text(encoding='utf-8-sig'))
known = {entry['path'].replace('\\','/') for entry in before}
for path in owned:
    if path not in known:
        before.append({'path':path,'sha256':hashlib.sha256((out/'before'/path).read_bytes()).hexdigest()})
for path in owned:
    captured = next(entry for entry in before if entry['path'].replace('\\','/') == path)
    assert hashlib.sha256((out/'before'/path).read_bytes()).hexdigest() == captured['sha256']
(out/'SOURCE_BEFORE_COMPLETE.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
changed, unexpected, after = [], [], []
for entry in before:
    path = entry['path'].replace('\\','/')
    digest = hashlib.sha256((root/path).read_bytes()).hexdigest()
    after.append({'path':path,'sha256':digest})
    if digest != entry['sha256']:
        changed.append(path)
        if path not in owned:
            unexpected.append(path)
diffs=[]
for path in owned+added:
    old = (out/'before'/path).read_text(encoding='utf-8-sig') if path in owned else ''
    new = (root/path).read_text(encoding='utf-8-sig')
    diffs.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before/'+path,tofile='after/'+path))
    if path in added:
        after.append({'path':path,'sha256':hashlib.sha256((root/path).read_bytes()).hexdigest()})
(out/'IMPLEMENTATION.diff').write_text(''.join(diffs),encoding='utf-8')
(out/'SOURCE_AFTER.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
result={'monitored_existing':len(before),'changed_existing':changed,'new_source_files':added,
    'unexpected_monitored_changes':unexpected,'unchanged_existing':len(before)-len(changed),
    'limits':'No DB/WAL/SHM digests; monitored manifest is not full repository/build identity.'}
(out/'SOURCE_COMPARISON.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
