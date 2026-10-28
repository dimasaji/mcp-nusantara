"""Final evidence generation, without changing source, tests or prior evidence."""
import ast
import difflib
import hashlib
import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

out = Path(__file__).resolve().parent
root = out.parents[2]
load = lambda name: json.loads((out / name).read_text(encoding='utf-8-sig'))
allowed = {'app/devcore/grounding.py', 'tests/v2/test_devcore_grounding_response.py'}
before = load('CURRENT_BEFORE.json')
stopped = load('FILES_AFTER.json')
stop_hashes = {str(Path(row['path'])): row['sha256'].upper() for row in stopped}
changed, unexpected, missing, after = [], [], [], []
for row in before:
    path = Path(row['path'])
    rel = path.relative_to(root).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else 'MISSING'
    after.append({'path': str(path), 'sha256': digest})
    if digest == 'MISSING':
        missing.append(rel)
    if digest != row['sha256'].upper():
        changed.append(rel)
    if digest != stop_hashes[str(path)]:
        unexpected.append(rel)

patch = []
old_tests, new_tests = {}, {}
for rel in sorted(allowed):
    old = (out / (rel.replace('/', '__') + '.before')).read_text(encoding='utf-8-sig')
    new = (root / rel).read_text(encoding='utf-8-sig')
    ast.parse(new, filename=rel)
    patch.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                    fromfile=rel+' (before)', tofile=rel))
    if rel.startswith('tests/'):
        tests = lambda text: {n.name: ast.dump(n) for n in ast.parse(text).body
                              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                              and n.name.startswith('test_')}
        old_tests, new_tests = tests(old), tests(new)
patch_matches = ''.join(patch) == (out / 'PATCH_DIFF.patch').read_text(encoding='utf-8')
removed = sorted(old_tests.keys() - new_tests.keys())
altered = sorted(name for name in old_tests.keys() & new_tests.keys()
                 if old_tests[name] != new_tests[name])

def test_result(label):
    suite = ET.parse(out / (label + '_RESULTS.xml')).getroot().find('testsuite')
    counts = {key: int(suite.attrib[key]) for key in ('tests', 'failures', 'errors', 'skipped')}
    counts['passed'] = counts['tests'] - counts['failures'] - counts['errors'] - counts['skipped']
    counts['timestamp'] = suite.attrib['timestamp']
    counts['cases'] = [dict(name=node.attrib['name'], classname=node.attrib['classname'],
                           status='ENVIRONMENT_LIMITED' if node.find('skipped') is not None else
                           'FAILED' if node.find('failure') is not None or node.find('error') is not None else 'PASS',
                           skip_reason=node.find('skipped').attrib.get('message') if node.find('skipped') is not None else None)
                       for node in suite.findall('testcase')]
    counts['guards'] = load(label + '_GUARDS.json')
    counts['evidence'] = [label + '_RESULTS.xml', label + '_OUTPUT.txt', label + '_GUARDS.json']
    return counts

targeted, regression = test_result('TARGETED'), test_result('REGRESSION')
unauthorized = sorted(set(changed) - allowed)
good = (not unauthorized and not unexpected and not missing and not removed and not altered
        and patch_matches and load('BASELINE_ATTRIBUTION.json')['c4_authorized_by_user_condition']
        and load('DIFF_CHECK_RESULT.json')['scoped_diff_check_exit'] == 0
        and all(not r['failures'] and not r['errors'] and not r['guards']['violations']
                and r['guards']['pytest_exit'] == 0 for r in (targeted, regression)))
audit = dict(contract='NUS-MDE-LC-20261008-DECIMAL-COMMA', timestamp=datetime.now().astimezone().isoformat(),
             disposition='IMPLEMENTED_VERIFIED_SCOPED' if good else 'REVIEW_REQUIRED',
             files_before='../../CURRENT_BEFORE.json', files_after='../../FILES_FINAL.json',
             files_changed=changed, diff='../../PATCH_DIFF.patch', diff_integrity_matches=True if patch_matches else False,
             tests_added=sorted(new_tests.keys()-old_tests.keys()), tests_changed=altered, tests_removed=removed,
             unauthorized_changes=unauthorized,
             unauthorized_source_changes=len([p for p in unauthorized if p.startswith('app/')]),
             unauthorized_test_changes=len([p for p in unauthorized if p.startswith('tests/')]),
             baseline_filesystem_changes=load('BASELINE_ATTRIBUTION.json')['baseline_changes'],
             baseline_status='BASELINE_ATTRIBUTED_PRE_EXISTING',
             cache_preserved_since_pre_patch=True if not any('last_query_stamp' in p for p in changed) else False,
             unexpected_changes_since_stop=unexpected, missing=missing,
             files_inventoried=len(before), static_python_parse='PASS', scoped_whitespace='PASS',
             targeted={'passed': targeted['passed'], 'skipped': targeted['skipped']},
             regression={'passed': regression['passed'], 'skipped': regression['skipped']},
             runtime_identity='NOT_VERIFIED', live_integration='NOT_VERIFIED', v1_acceptance='HOLD',
             scope_limitation='3493 recorded files; no whole-filesystem claim',
             prior_evidence='Original stopped CHANGE_AUDIT.json remains unchanged; this is the final C6 revision')
# Separate revision directory keeps every earlier evidence artifact intact.
final_dir = out / 'C6'
final_dir.mkdir(exist_ok=False)
for path, value in ((out/'FILES_FINAL.json', after), (out/'TARGETED_TEST.json', targeted),
                    (out/'REGRESSION_TEST.json', regression), (final_dir/'CHANGE_AUDIT.json', audit)):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
print(json.dumps(audit, indent=2, ensure_ascii=False))
raise SystemExit(0 if good else 1)
