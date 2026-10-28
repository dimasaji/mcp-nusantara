"""Report-only exact baseline reconstruction/diff; no application execution."""
from pathlib import Path
import hashlib
import json
import difflib

ROOT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).resolve().parent
before = json.loads((REPORT / 'SOURCE_BEFORE.json').read_text(encoding='utf-8-sig'))
hashes = {item['path'].replace('\\', '/'): item['sha256'] for item in before['files']}


def save_matching(path, normalized):
    for data in (normalized, normalized.replace(b'\n', b'\r\n'),
                 b'\xef\xbb\xbf' + normalized, b'\xef\xbb\xbf' + normalized.replace(b'\n', b'\r\n')):
        if hashlib.sha256(data).hexdigest() == hashes[path]:
            (REPORT / 'before' / path.replace('/', '__')).write_bytes(data)
            return
    raise RuntimeError('Exact captured baseline cannot be reconstructed: ' + path)


path = 'app/api/control_plane.py'
data = (ROOT / path).read_bytes().replace(b'\r\n', b'\n')
branch = b"    if getattr(request.app.state, 'runtime_profile', None) == 'ATTESTATION':\n        owner = getattr(request.app.state, 'runtime_authorization', None)\n        if owner is None:\n            raise HTTPException(503, 'ATTESTATION_AUTHORIZATION_UNAVAILABLE')\n        return owner.evidence()  # Never execute legacy DB/WAL/SHM digest projection.\n"
assert data.count(branch) == 1
save_matching(path, data.replace(branch, b''))

path = 'tests/test_runtime_verification.py'
data = (ROOT / path).read_bytes().replace(b'\r\n', b'\n')
data = data.replace(b"assert not hasattr(app.state, 'runtime_authorization')\n", b'')
data = data.replace(b"'app/core/runtime_identity.py', 'app/core/control_plane_projection.py'}",
                    b"'app/core/runtime_identity.py', 'app/api/control_plane.py', 'app/core/control_plane_projection.py'}")
data = data.replace(b"fullname.startswith(('app.knowledge', 'app.rag', 'app.language'))",
                    b"fullname.startswith(('app.knowledge', 'app.rag', 'app.approval', 'app.language'))")
data = data.replace(b"    import app.api.control_plane as control_plane\n    control_plane.project = forbidden\n    assert client.get('/v1/control-plane/snapshot').json()['live_actions'] == 'LOCKED'\n", b'')
data = data.replace(b"name.startswith(('app.knowledge','app.rag','app.language'))",
                    b"name.startswith(('app.knowledge','app.rag','app.approval','app.language'))")
block = b"assert app.state.runtime_authorization._audit.path is None\nassert app.state.runtime_authorization._policy is None\nassert app.state.runtime_authorization._isolated_transport is None\nassert app.state.runtime_authorization.evidence()['live_actions'] == 'LOCKED'\nassert {name for name in sys.modules if name.startswith('app.approval')} <= {\n    'app.approval','app.approval.audit_trail','app.approval.queue','app.approval.runtime_authorization'}\n"
assert data.count(block) == 1
data = data.replace(block, b'')
data = data.replace(b"'observation':observation,\n    'foundation':app.state.runtime_authorization.evidence()",
                    b"'observation':observation")
save_matching(path, data)

owned = ['app/security/local_operator.py', 'app/main.py', 'app/api/control_plane.py',
         'app/core/runtime_correlation.py', 'app/api/runtime_verification.py',
         'tests/test_runtime_verification.py', 'app/approval/runtime_authorization.py',
         'tests/test_runtime_authorization.py']
patches = []
for path in owned:
    old_path = REPORT / 'before' / path.replace('/', '__')
    if path in hashes:
        old = old_path.read_bytes()
        assert hashlib.sha256(old).hexdigest() == hashes[path], path
        old_lines = old.decode('utf-8-sig').splitlines(keepends=True)
    else:
        old_lines = []
    new_lines = (ROOT / path).read_text(encoding='utf-8-sig').splitlines(keepends=True)
    patch = ''.join(difflib.unified_diff(old_lines, new_lines,
        fromfile='a/' + path if old_lines else '/dev/null', tofile='b/' + path))
    (REPORT / (path.replace('/', '__') + '.diff')).write_text(patch, encoding='utf-8')
    patches.append(patch)
(REPORT / 'IMPLEMENTATION.diff').write_text('\n'.join(patches), encoding='utf-8')
print(json.dumps({'owned_files': len(owned), 'exact_before_hashes_verified': len(hashes.keys() & set(owned))}))
