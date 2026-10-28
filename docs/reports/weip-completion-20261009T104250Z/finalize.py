"""Read hashes/status and write completion evidence only in this new directory."""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
GIT = r'C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
baseline = json.loads((OUT / 'BASELINE.json').read_text(encoding='utf-8-sig'))
allowed = {'app\\knowledge\\web_evidence.py', 'tests\\test_web_evidence_pipeline.py'}
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
current = {k: digest(ROOT / k) if (ROOT / k).is_file() else None for k in baseline['hashes']}
changed = [k for k in current if current[k] != baseline['hashes'][k]]
unexpected = [k for k in changed if k not in allowed]
def git(*args):
    r = subprocess.run([GIT, *args], cwd=ROOT, capture_output=True, text=True)
    return {'exit_code': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}
status = git('status', '--short', '--untracked-files=all')
head = git('rev-parse', 'HEAD')
branch = git('branch', '--show-current')
check = git('diff', '--check', '--', *[k.replace('\\', '/') for k in sorted(allowed)])
patch = []
for name, before in [('app/knowledge/web_evidence.py', 'web_evidence.py.before'),
                     ('tests/test_web_evidence_pipeline.py', 'test_web_evidence_pipeline.py.before')]:
    compile((ROOT / name).read_text(encoding='utf-8'), name, 'exec')
    patch.extend(difflib.unified_diff((OUT / before).read_text(encoding='utf-8').splitlines(True),
        (ROOT / name).read_text(encoding='utf-8').splitlines(True), fromfile='before/'+name, tofile='after/'+name))
(OUT / 'SCOPED_CHANGES.patch').write_text(''.join(patch), encoding='utf-8')
tests = []
for p in sorted(OUT.glob('*/results.xml')):
    suite = ET.parse(p).getroot().find('testsuite')
    guards = json.loads((p.parent / 'guards.json').read_text())
    tests.append({'evidence': str(p.relative_to(ROOT)), 'tests': int(suite.attrib['tests']),
        'failures': int(suite.attrib['failures']), 'errors': int(suite.attrib['errors']),
        'skipped': int(suite.attrib['skipped']), 'guards': guards})
app_hashes = sorted((k.replace('\\', '/'), digest(ROOT / k)) for k in current
                    if k.startswith('app\\') and k.endswith('.py'))
source_fingerprint = hashlib.sha256(''.join(k+'\0'+h+'\n' for k,h in app_hashes).encode()).hexdigest()
audit = {'at_utc': datetime.now(timezone.utc).isoformat(), 'head': head, 'branch': branch,
    'changed_baseline_files': changed, 'unauthorized_baseline_changes': unexpected,
    'before_hashes': {k: baseline['hashes'][k] for k in sorted(allowed)},
    'after_hashes': {k: current[k] for k in sorted(allowed)},
    'database_and_sidecars': {k: {'before': baseline['hashes'][k], 'after': current[k],
                                 'unchanged': baseline['hashes'][k] == current[k]}
                             for k in current if k.startswith('data\\knowledge\\')},
    'git_status_after': status, 'git_diff_check_scoped': check,
    'removed_baseline_status_entries': sorted(set(baseline['git_status']) - set(status['stdout'].splitlines())),
    'syntax_compile': 'PASS_NO_BYTECODE', 'tests': tests,
    'disk_app_py_fingerprint': 'sha256:'+source_fingerprint,
    'fingerprint_algorithm': 'SHA256 sorted app Python paths normalized to / + NUL + file SHA256 + newline; on-disk only, not loaded-process identity',
    'runtime_read_only_observation': {'pid':36084, 'parent_pid':33220, 'port':8000,
        'start_time':'2026-10-09T15:19:07.716904+07:00',
        'executable':r'C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe',
        'process_operations':0, 'application_requests':0},
    'historical_reports': 'PRESERVED; earlier passing results are not new verification',
    'official_fixture': {'status':'NOT_RUN', 'owner_choice':'A', 'path':None, 'approval_reference':None}}
(OUT / 'CHANGE_AUDIT.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
print(json.dumps({'changed_baseline_files': changed, 'unexpected': unexpected,
                 'removed_status_count':len(audit['removed_baseline_status_entries']),
                 'database_unchanged': all(v['unchanged'] for v in audit['database_and_sidecars'].values()),
                 'fingerprint':audit['disk_app_py_fingerprint'], 'tests':tests}, indent=2))
if unexpected or head['stdout'].strip() != baseline['head']:
    raise SystemExit(1)
