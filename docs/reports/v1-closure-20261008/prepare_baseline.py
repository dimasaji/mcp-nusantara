"""Evidence-only baseline. Never imports the application or writes existing files."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
GIT = r'C:\Users\dmaza\AppData\Local\hermes\git\cmd\git.exe'

def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)

def git(*args):
    result = subprocess.run([GIT, '--no-optional-locks', *args], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    return {'stdout': result.stdout, 'stderr': result.stderr}

def snapshot():
    hashes, errors = {}, []
    roots = ['app', 'tests', 'control-plane/src', 'docs', 'reports', 'scripts',
             'graphify-out/cache', 'pyproject.toml', 'Dockerfile', 'docker-compose.yml',
             'control-plane/package.json', 'control-plane/package-lock.json',
             'control-plane/vite.config.ts']
    for relative in roots:
        base = ROOT / relative
        files = [base] if base.is_file() else base.rglob('*')
        for path in files:
            if path.is_relative_to(OUT) or any(p in ('__pycache__', 'node_modules', '.pytest_cache') for p in path.parts):
                continue
            try:
                if path.is_file() and not path.is_symlink():
                    hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                errors.append({'path': str(path), 'error': type(exc).__name__})
    return {'sha256': hashes, 'errors': errors}

if __name__ == '__main__':
    blockers = [
        {'id': 'CC05', 'finding': 'V1 memory stores user/assistant turns unconditionally; client-selected session defaults to web. Policy evaluates answer after the user write. No V1 consent/ownership/retention contract is implemented.', 'files': ['app/core/gate_integration.py', 'app/api/routes.py', 'app/memory/engine.py'], 'decision_required': 'V1 memory ownership and consent policy; keep legacy history or make the V1 route NO-MEMORY. Do not import V2 SessionMemory.'},
        {'id': 'CC06-FILTER', 'finding': 'KnowledgeEngine discards filter; canonical retrieval/store do not accept filters. Source-policy semantics and supported metadata/authority fields are not specified.', 'files': ['app/knowledge/engine.py', 'app/knowledge/rag.py', 'app/knowledge/store.py'], 'decision_required': 'Approved filter/authority schema and enforcement before candidate scoring/top-k.'},
        {'id': 'CC06-ORACLE', 'finding': 'Latest historical oracle audit records two REVIEW_REQUIRED official cases and one MISSING passport requirements case; fixtures do not establish official authority.', 'files': ['reports/V1_CLOSURE_ORACLE_AUDIT.json', 'reports/V1_RECOVERY_PROGRESS.json'], 'decision_required': 'Approved official snapshots with issuer, jurisdiction, validity and ingestion authorization; no invented oracle.'},
        {'id': 'MODEL-CONTROL', 'finding': 'Existing configuration owner is immutable and compose-once. Chat has per-request technical model override; there is no human profile registry or Control Plane selection owner consumed by chat.', 'files': ['app/core/config.py', 'app/core/nusantara_config.py', 'app/api/routes.py', 'app/models/ollama.py', 'app/models/router.py', 'app/api/control_plane.py'], 'decision_required': 'Profile to actual installed model mapping; whether selection is request/session/operator-wide; authorized owner lifecycle, scope and expiry without a second configuration truth.'},
        {'id': 'ORCHESTRATION-CONTROL', 'finding': 'Existing orchestration assembles supplied stage artifacts. Chat chooses its branches internally, without a user-selected orchestration field or source/answer/permission settings.', 'files': ['app/orchestration/engine.py', 'app/hermes/agent.py', 'app/api/routes.py'], 'decision_required': 'Approved semantics for direct/evidence modes, mandatory safety stages and treatment of missing evidence. Do not invent another engine.'},
        {'id': 'UI-E2E', 'finding': 'Existing UI is an evidence/acceptance console. API has no model/mode/source settings selection equivalent; Vite does not proxy /v1/chat. Mandatory end-to-end selection cases cannot pass.', 'files': ['control-plane/src/human.tsx', 'control-plane/src/router.tsx', 'control-plane/src/api.ts', 'control-plane/vite.config.ts'], 'decision_required': 'Depends on MODEL-CONTROL and ORCHESTRATION-CONTROL decisions before UI implementation.'},
        {'id': 'SECURITY-ENV', 'finding': 'Historical native symlink boundary test skipped for missing Windows privilege; current live enforcement and approval linkage not verified.', 'files': ['reports/V1_RECOVERY_PROGRESS.json', 'app/policy/engine.py', 'app/security/auth.py'], 'decision_required': 'Controlled supported test environment, without production restart/deployment.'},
        {'id': 'DEPLOYMENT', 'finding': 'No current-source startup/health/chat/container integration proof. Existing Docker compose declares a default database password; operational target and provisioned official/worker/model resources not established.', 'files': ['Dockerfile', 'docker-compose.yml', 'app/main.py', 'reports/V1_RECOVERY_PROGRESS.json'], 'decision_required': 'Approved target and explicit credentials/resources; no deployment or restart in this task.'},
    ]
    baseline = {
        'scope': 'V1 acceptance closure baseline; read-only discovery before implementation',
        'timestamp': datetime.now(timezone(timedelta(hours=7))).isoformat(),
        'repository': str(ROOT), 'branch': git('branch', '--show-current')['stdout'].strip(),
        'head': git('rev-parse', 'HEAD')['stdout'].strip(), 'working_tree': git('status', '--short'),
        'preservation': snapshot(), 'active_blockers': blockers,
        'closed_scoped': {'CC01': 'Existing strict public projection plus historical scoped tests; current isolated recheck pending', 'LC-DECIMAL-001': 'D4 PASS scoped only; not V1 acceptance'},
        'tests_available': ['tests/test_v1_response_projection.py', 'tests/test_configuration_contract.py', 'tests/test_configuration_integration.py', 'tests/test_model_router_configuration.py', 'tests/test_gate_integration.py', 'tests/test_gates_8_16.py', 'tests/test_effective_rag_profile.py', 'tests/v2/test_devcore_grounding_response.py'],
        'runtime_path': 'app.main -> /v1 app.api.routes.chat -> OllamaProvider(snapshot, request.model override) -> Hermes language/problem -> KnowledgeEngine -> TrustEngine -> shadow GateIntegration -> local/evidence/provider branch -> grounding -> remember_response -> public projection',
        'ui_path': 'control-plane/src/router.tsx -> human.tsx; api.ts transports evidence/acceptance/preview, not assistant model or orchestration control',
        'configuration_path': 'Settings.effective_configuration -> compose_configuration once -> immutable NusantaraConfig; Ollama request override supported, hot recompose explicitly rejected',
        'orchestration_path': 'GateIntegration -> OrchestrationEngine.run collects stage artifacts; no selectable V1 execution modes',
        'control_plane_capability': 'Evidence and review console with authenticated preview; not a runtime preference controller',
        'runtime_identity': 'NOT_VERIFIED_CURRENT_PROCESS', 'live_integration_verified': False,
        'changes': [], 'files_changed': [], 'tests': 'NOT_RUN_AT_BASELINE',
        'limitations': ['Historical runtime evidence is not current-source runtime proof', 'No environment secrets or live database inspected', 'Git reports five pre-existing inaccessible temporary directories', 'Graph query deliberately not run: it mutates last_query_stamp; existing cache must be preserved'],
        'unauthorized_changes': 0, 'final_status': 'HOLD_REVIEW_REQUIRED',
    }
    write('BASELINE.json', baseline)
    print(json.dumps({'branch': baseline['branch'], 'head': baseline['head'], 'hashed_files': len(baseline['preservation']['sha256']), 'read_errors': len(baseline['preservation']['errors']), 'blockers': len(blockers)}))
