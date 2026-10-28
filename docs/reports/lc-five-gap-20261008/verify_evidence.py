"""Read-only source comparison; writes only this report's verification evidence."""
import ast
import difflib
import hashlib
import json
from datetime import datetime
from pathlib import Path

out = Path(__file__).resolve().parent
root = out.parents[2]
allowed = ['app/devcore/core.py', 'app/devcore/grounding.py', 'app/devcore/tools.py',
           'tests/v2/test_devcore.py', 'tests/v2/test_devcore_grounding_response.py']
before = json.loads((out / 'FILES_BEFORE.json').read_text(encoding='utf-8-sig'))
changed, missing, after = [], [], []
for item in before:
    path = Path(item['path'])
    if not path.is_file():
        missing.append(item['path'])
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    after.append(dict(path=str(path), sha256=digest))
    if digest != item['sha256']:
        changed.append(path.relative_to(root).as_posix())
patch = []
for rel in allowed:
    old = (out / (rel.replace('/', '__') + '.before')).read_text(encoding='utf-8-sig')
    new = (root / rel).read_text(encoding='utf-8-sig')
    ast.parse(new, filename=rel)
    patch.extend(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                    fromfile=rel + ' (LEVEL C before)', tofile=rel))
(out / 'TASK_DIFF.patch').write_text(''.join(patch), encoding='utf-8')
(out / 'FILES_AFTER.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
result = dict(timestamp=datetime.now().astimezone().isoformat(), inventoried_files=len(before),
              changed=changed, missing=missing, unauthorized_changes=sorted(set(changed)-set(allowed)),
              allowed_files=allowed, static_python_parse='PASS',
              unattributed_reports='PRESERVED' if not any(p.startswith('reports/') for p in changed) else 'CHANGED',
              graph='PRESERVED; update omitted because contract restricts mutations to remediation dependencies',
              runtime='NOT_VERIFIED')
(out / 'PRESERVATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
raise SystemExit(1 if missing or result['unauthorized_changes'] else 0)
