"""Compare exact task baseline without importing application or protected owners."""
import difflib
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[2]
rows = json.loads((here/'FILES_BEFORE.json').read_text(encoding='utf-8-sig'))
changes = []
for row in rows:
    path = root/row['path']
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != row['sha256']:
        changes.append({'path': row['path'], 'before': row['sha256'], 'after': digest})
allowed = {'app/devcore/core.py', 'app/devcore/router.py', 'graphify-out/graph.json', 'graphify-out/GRAPH_REPORT.md'}
assert {row['path'] for row in changes} <= allowed
(here/'PRESERVATION.json').write_text(json.dumps({'monitored_existing_files': len(rows),
    'changes': changes, 'outside_allowlist': [], 'new_source': ['app/devcore/inspection.py'],
    'new_test': ['tests/v2/test_devcore_inspection.py']}, indent=2), encoding='utf-8')
diff = []
for name in ('core', 'router'):
    before = (here/(name+'.before.py.txt')).read_text(encoding='utf-8').splitlines(keepends=True)
    after = (root/'app/devcore'/(name+'.py')).read_text(encoding='utf-8').splitlines(keepends=True)
    diff.extend(difflib.unified_diff(before, after, fromfile='task-before/app/devcore/'+name+'.py', tofile='task-after/app/devcore/'+name+'.py'))
for rel in ('app/devcore/inspection.py', 'tests/v2/test_devcore_inspection.py'):
    diff.extend(difflib.unified_diff([], (root/rel).read_text(encoding='utf-8').splitlines(keepends=True), fromfile='/dev/null', tofile=rel))
(here/'TASK_DIFF.patch').write_text(''.join(diff), encoding='utf-8')
before = set((here/'GIT_BEFORE.txt').read_text(encoding='utf-8-sig').splitlines())
after = set((here/'GIT_AFTER.txt').read_text(encoding='utf-8-sig').splitlines())
(here/'GIT_DELTA.json').write_text(json.dumps({'added_entries': sorted(after-before),
    'removed_entries': sorted(before-after)}, indent=2), encoding='utf-8')
print(json.dumps({'monitored': len(rows), 'changed': [row['path'] for row in changes]}, indent=2))
