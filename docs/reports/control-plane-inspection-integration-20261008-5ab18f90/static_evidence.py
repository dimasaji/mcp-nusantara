"""Read source syntax only; never import application, call HTTP or inspect data."""
import ast
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[2]
names = ('control-plane/src/api.ts', 'control-plane/vite.config.ts',
         'app/api/v2_routes.py', 'app/security/auth.py', 'app/main.py',
         'app/devcore/core.py', 'app/devcore/router.py')
sources = {name: (root/name).read_text(encoding='utf-8') for name in names}
tree = ast.parse(sources['app/api/v2_routes.py'])
request = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'DevRequest')
fields = [node.target.id for node in request.body if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)]
endpoint = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'dev_chat')
calls = [ast.unparse(node.func) for node in ast.walk(endpoint) if isinstance(node, ast.Call)]
checks = {
    'frontend_client_has_no_devcore_request': '/v2/dev' not in sources['control-plane/src/api.ts'],
    'existing_proxy_has_no_v2_path': "'/v2" not in sources['control-plane/vite.config.ts'],
    'request_fields_are_general_input_only': set(fields) == {'session_id', 'user_input'},
    'dev_route_requires_admin': '_require_admin' in calls,
    'dev_route_constructs_provider': 'OllamaProvider' in calls,
    'dev_route_contains_generation_callback': 'provider.generate' in calls,
    'dev_route_delegates_general_request_to_core': 'core.handle' in calls,
    'dev_route_absent_in_attestation_composition': 'if not _READ_ONLY_EVIDENCE and not _ATTESTATION:\n    app.include_router(api_router)\n    app.include_router(v2_router)' in sources['app/main.py'],
}
assert all(checks.values()), 'STATIC_OBSERVATION_CONFLICT'
references = []
for name, terms in {
    'control-plane/src/api.ts': ('fetchSnapshot', 'submitIntention'),
    'control-plane/vite.config.ts': ('proxy:',),
    'app/api/v2_routes.py': ('class DevRequest', 'async def dev_chat', '_require_admin(x_admin_token)',
                             'provider = OllamaProvider(nusantara_config=_configuration)', 'return await core.handle'),
    'app/security/auth.py': ('def require_admin', 'NUSANTARA_ADMIN_TOKEN'),
    'app/main.py': ('allow_origins=', 'app.include_router(v2_router)'),
    'app/devcore/core.py': ('if self.generate:', 'if p.inspection is not None:', 'self._resolve_reads('),
}.items():
    for number, line in enumerate(sources[name].splitlines(), 1):
        if any(term in line for term in terms):
            references.append({'file': name, 'line': number, 'source': line.strip()})
(here/'STATIC_EVIDENCE.json').write_text(json.dumps({'evidence_kind': 'CURRENT_DISK_SOURCE_ONLY',
    'checks': checks, 'dev_request_fields': fields, 'endpoint_call_names': calls,
    'references': references, 'live_requests': 0, 'ui_tests_run': 0,
    'runtime_profile_observed': False, 'provider_invocations': 0}, indent=2), encoding='utf-8')
baseline = json.loads((here/'FILES_BEFORE.json').read_text(encoding='utf-8-sig'))
changed = [row['path'] for row in baseline if hashlib.sha256((root/row['path']).read_bytes()).hexdigest() != row['sha256']]
assert changed == [], 'PRESERVATION_CONFLICT'
(here/'PRESERVATION.json').write_text(json.dumps({'monitored_existing_files': len(baseline),
    'changed': changed, 'application_modifications': [], 'ui_modifications': [],
    'protected_files_read_or_hashed': False}, indent=2), encoding='utf-8')
print(json.dumps({'static_checks_confirmed': len(checks), 'monitored_unchanged': len(baseline),
                  'UI_INTEGRATION': 'BLOCKED / OUT-OF-SCOPE', 'live_observation': 'NOT_PERFORMED'}, indent=2))
