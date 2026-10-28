"""Append-only implementation evidence; no app import or runtime operation."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
import prepare_baseline as baseline

OUT, ROOT = baseline.OUT, baseline.ROOT
NOW = datetime.now(timezone(timedelta(hours=7))).isoformat()
WRITTEN = {}

def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))

def write(name, value):
    path = OUT / name
    if path.exists():
        path = OUT / (path.stem + '.' + NOW[:19].replace(':', '').replace('-', '') + path.suffix)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
    WRITTEN[name] = path.name
    return path.name

expected = {
    'app/main.py', 'app/api/control_plane.py', 'app/api/routes.py',
    'app/core/config.py', 'app/core/nusantara_config.py', 'app/hermes/agent.py',
    'app/knowledge/engine.py', 'tests/test_effective_rag_profile.py',
    'tests/test_v1_response_projection.py', 'tests/test_v1_operator_control.py',
    'control-plane/src/api.ts', 'control-plane/src/router.tsx',
    'control-plane/src/styles.css', 'control-plane/src/ui.tsx',
    'control-plane/src/assistant.tsx', 'control-plane/vite.config.ts', 'Dockerfile',
    'docs/contracts/NUSANTARA-CONTROL-PLANE-V1.md',
}
before = read('BASELINE.json')['preservation']['sha256']
after = baseline.snapshot()
current = after['sha256']
changed = sorted(p for p in before if p in current and before[p] != current[p])
added = sorted(p for p in current if p not in before)
removed = sorted(p for p in before if p not in current)
unexpected = sorted((set(changed + added) - expected) | set(removed))
supplementary = {
    'control-plane/index.html': 'control-plane.index.html.before',
    'control-plane/e2e/control-plane.spec.ts': 'control-plane.spec.ts.before',
    '.dockerignore': 'dockerignore.before',
    'control-plane/README.md': None,
    'control-plane/tests/assistant.test.tsx': None,
}
supplementary_hashes = {}
for relative, backup in supplementary.items():
    supplementary_hashes[relative] = {
        'after_sha256': hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
        'before_sha256': hashlib.sha256((OUT / backup).read_bytes()).hexdigest() if backup else None,
        'attribution': 'Explicit task edit outside baseline snapshot coverage',
        'reason': 'Entry title / legacy E2E landing page / bundle Docker inclusion / documentation / new UI tests',
    }
audit = {
    'timestamp': NOW, 'status': 'PASS_SCOPED' if not unexpected and not after['errors'] else 'REVIEW_REQUIRED',
    'baseline_files': len(before), 'changed': changed, 'added': added, 'removed': removed,
    'unexpected': unexpected, 'read_errors': after['errors'],
    'causal_hash_changes': {p: {'before': before.get(p), 'after': current[p]} for p in changed + added},
    'supplementary_changes': supplementary_hashes,
    'unauthorized_source_changes': len([p for p in unexpected if p.startswith(('app/', 'control-plane/src/'))]),
    'unauthorized_test_changes': len([p for p in unexpected if p.startswith('tests/')]),
    'graph_cache_unchanged': all(current.get(p) == value for p, value in before.items() if p.startswith('graphify-out/cache/')),
    'memory_gate_orchestration_rag_store_unchanged': all(current.get(p) == before[p] for p in (
        'app/memory/engine.py', 'app/core/gate_integration.py', 'app/orchestration/engine.py',
        'app/knowledge/rag.py', 'app/knowledge/store.py')),
    'v2_source_and_tests_unchanged': all(current.get(p) == value for p, value in before.items() if p.startswith(('app/api/v2', 'app/devcore/', 'tests/v2/'))),
    'historical_evidence_unchanged': all(current.get(p) == value for p, value in before.items() if p.startswith(('reports/', 'docs/reports/'))),
    'pre_existing_changes': 'Original working-tree listing retained in BASELINE.json; not attributed to this task by Git diff alone',
    'generated_bundle': 'Vite rebuilt index/assets with --emptyOutDir false; previous assets retained, BUNDLE_INDEX_BEFORE.html saved',
    'limitations': ['Snapshot excludes frontend tests/e2e/index/README, .dockerignore and generated dist; supplementary hashes listed',
                    'README was appended; no full before hash captured', 'Production data/.env were not inspected; no production database or credential mutation performed'],
    'working_tree': baseline.git('status', '--short'),
    'tests': ['Baseline/current hash comparison', 'git diff --check'],
    'reason': 'Attribute current-task edits separately from preserved existing working-tree changes',
    'files_changed': changed + added + list(supplementary), 'blockers': [],
}
write('CHANGE_AUDIT.json', audit)
if unexpected or after['errors']:
    raise SystemExit('STOP: unexpected changes or audit read errors; CHANGE_AUDIT.json records evidence')

xml = ET.parse(OUT / 'regression-20261009-090953/results.xml').getroot()
cases = list(xml.iter('testcase'))
backend = {'passed': sum(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases),
           'failed': sum(c.find('failure') is not None or c.find('error') is not None for c in cases),
           'skipped': sum(c.find('skipped') is not None for c in cases), 'deselected': 1}
front = read('FRONTEND_REGRESSION.json')
frontend = {'passed': front['numPassedTests'], 'failed': front['numFailedTests'], 'skipped': front['numPendingTests']}
native = read('CANDIDATE_MODEL_STATUS.v2.json')
receipts = [json.loads(line) for line in (OUT / 'LOCAL_PROVIDER_RECEIPTS.jsonl').read_text().splitlines()]
process = read('SOCKET_PROCESS_IDENTITY.v2.json')
receipt = receipts[-1]
identity_matches = all(receipt[key] == native['model'] for key in ('configured_model', 'effective_model', 'selected_model', 'payload_model', 'actual_model')) and receipt['process_id'] == native['process_id'] == process['ProcessId']
native_evidence = {
    'timestamp': NOW, 'status': 'PASS_SCOPED' if identity_matches and not receipt['failed'] else 'FAIL',
    'url': 'http://127.0.0.1:18011/', 'provider': 'ACTUAL_LOCAL_OLLAMA',
    'model': native['model'], 'model_revision': native['revision'], 'identity_matches': identity_matches,
    'process_id': native['process_id'], 'receipt': receipt,
    'source_identity': read('SOURCE_IDENTITY_CHECK.json'),
    'semantic': 'EXPLICIT_FIXTURE', 'retrieval': 'EXPLICIT_NON_OFFICIAL_FIXTURE',
    'observed': ['Authenticated real inventory and selection acknowledgement',
                 'UI sent question to V1 handler; actual existing Hermes executed',
                 'Actual installed model invocation returned matching provider-reported identity',
                 'Grounding rejected unsupported content and public abstention displayed in UI',
                 'No browser error logs after corrected observer'],
    'grounded': native['last_request']['grounded'], 'stages': native['last_request']['stages'],
    'initial_failure': 'Receipt observer incorrectly passed self to a static function; wrapper fixed, app source unchanged. Initial error evidence retained.',
    'limits': ['One installed model only; no switch between distinct actual models',
              'Model name returned by provider is not loaded-weight attestation',
              'Semantic and retrieval fixtures do not prove native semantic/RAG production integration',
              'Current-source identity is app disk fingerprint, not full transitive loaded closure',
              'Port-8000 attestation endpoint refused candidate port with 403; boundary not bypassed; initial null attestation artifact retained'],
    'screenshots': ['LOCAL_PROVIDER_BROWSER.jpg', 'LOCAL_PROVIDER_INITIAL_ERROR.jpg'],
    'cleanup': read('CANDIDATE_CLEANUP.v2.json'),
}
write('LOCAL_PROVIDER_BROWSER_OBSERVATIONS.json', native_evidence)

backend_tests = ['regression-20261009-090953/results.xml', 'regression-20261009-090953/guards.json', 'targeted-20261009-093732/results.xml', 'FINAL_CHECKS.json']
ui_tests = ['FRONTEND_REGRESSION.json', 'BROWSER_OBSERVATIONS.json', WRITTEN['LOCAL_PROVIDER_BROWSER_OBSERVATIONS.json']]
open_gates = ['CC05 consent/session ownership/retention remains open under approved temporary legacy preservation',
              'CC06 official oracle: two REVIEW_REQUIRED cases, one MISSING passport case; issuer/jurisdiction/validity/ingest authorization needed',
              'Approved filter grammar/authority metadata absent; nonempty filter safely rejected, not implemented',
              'Full native semantic-worker plus production RAG/store/model UI integration not verified',
              'Native Windows symlink privilege/security operational enforcement not reverified',
              'Production deployment, provisioned credentials/resources and launch-worker consistency unverified; no deployment authorized']

def phase(name, status, evidence, files, reason, tests, limitations, blockers):
    value = {'timestamp': NOW, 'status': status, 'observed_evidence': evidence,
             'files_changed': files, 'reason': reason, 'tests_run': tests,
             'limitations': limitations, 'remaining_blockers': blockers}
    write(name + '.json', value)
    return value

phases = {}
phases['MODEL_CONTROL'] = phase('MODEL_CONTROL', 'PASS_SCOPED',
    ['Existing immutable Settings owner snapshot/revision replaces only validated model leaf', 'Invalid model/auth/inventory failure/stale revision/race fail closed',
     'In-flight snapshot stable; subsequent fixture request consumes selected fixture-b', 'Native browser/receipt confirms selected llama3.2:1b, revision 1, process 29356'],
    ['app/core/config.py', 'app/core/nusantara_config.py', 'app/api/control_plane.py', 'app/api/routes.py', 'control-plane/src/api.ts', 'control-plane/src/assistant.tsx'],
    'Implement approved operator-global selection on the existing configuration authority', backend_tests + ui_tests,
    ['CURRENT_PROCESS_ONLY, volatile, declared NORMAL single worker', 'Cross-process/restart consistency not implemented', 'Only one real installed model; distinct-real-model switch unverified'],
    ['Verify launch topology before operator-global deployment'])
phases['MEMORY_PRESERVATION'] = phase('MEMORY_PRESERVATION', 'PASS_SCOPED',
    ['Memory engine and gate integration unchanged from baseline', 'Existing user/assistant memory writes asserted in actual V1/Hermes guarded regression',
     'No migration, deletion, format change or V2 memory import'], ['app/hermes/agent.py', 'app/api/routes.py', 'tests/test_v1_operator_control.py'],
    'Preserve approved legacy behavior while moving execution ownership', backend_tests,
    ['User write still precedes answer policy; client session ownership/retention not solved', 'UI history is component lifetime only; navigating away resets client history'], [open_gates[0]])
phases['HERMES_EXECUTION'] = phase('HERMES_EXECUTION', 'PASS_SCOPED',
    ['Existing Hermes.run is called by execute_v1', 'V1 pipeline relocated into same Hermes agent; route has no provider.generate bypass',
     'Browser candidate status records HERMES_RUN through PUBLIC_PROJECTION; actual Ollama receipt matches process/model'],
    ['app/hermes/agent.py', 'app/api/routes.py', 'tests/test_v1_response_projection.py', 'tests/test_v1_operator_control.py'],
    'Make existing Hermes the V1 execution owner without another engine', backend_tests + ui_tests,
    ['Native semantic worker remains fixture in guarded candidates', 'Existing stage diagnostics are observations, not full runtime attestation'], [open_gates[3]])
phases['RESPONSE_PROJECTION'] = phase('RESPONSE_PROJECTION', 'PASS_SCOPED',
    ['Existing public projector consumes V1CoreResult', 'Strict public/nested schema asserted; internal gates/reasoning/memory excluded',
     'Frontend rejects invalid/private response with human error; provider failure is sanitized'],
    ['app/api/routes.py', 'app/hermes/agent.py', 'control-plane/src/api.ts', 'tests/test_v1_response_projection.py', 'control-plane/tests/assistant.test.tsx'],
    'Preserve CC01 public contract across Hermes ownership change', backend_tests + ['FRONTEND_REGRESSION.json'],
    ['Current public contract only; no full production runtime promotion'], [])
phases['DEVELOPER_CONSOLE'] = phase('DEVELOPER_CONSOLE', 'PASS_SCOPED',
    ['Existing React console shell/routes retained', 'Authenticated inventory/selection with acknowledgement; bad token fails without false model state',
     'Safe model/revision/process/source/last-request diagnostics', 'RAG/memory/approval readiness shown as REVIEW_REQUIRED or NOT_VERIFIED'],
    ['control-plane/src/assistant.tsx', 'control-plane/src/router.tsx', 'control-plane/src/ui.tsx', 'control-plane/src/api.ts'],
    'Add supported operator controls to existing console; keep technical views separate from user root', ui_tests,
    ['Readiness is not inferred from object construction; no risky execution controls', 'Operator token exists only in component memory'], open_gates)
phases['USER_UI'] = phase('USER_UI', 'PASS_SCOPED',
    ['Actual built root opens and submits V1 chat without model override', 'Answers/errors/in-flight state/history/citations visible',
     'Mobile viewport clientWidth=scrollWidth=375; navigation works', 'Native provider grounded abstention displayed'],
    ['control-plane/src/assistant.tsx', 'control-plane/src/api.ts', 'control-plane/src/router.tsx', 'control-plane/src/ui.tsx', 'control-plane/src/styles.css',
     'control-plane/vite.config.ts', 'control-plane/index.html', 'app/main.py', 'Dockerfile', '.dockerignore'],
    'Provide usable user chat at / with separate Console, using existing application and API', ui_tests + ['TypeScript --noEmit exit 0', 'Vite build exit 0 (--emptyOutDir false)'],
    ['Transient component history; no new persistence', 'Dockerfile includes prebuilt bundle; Docker image build/deployment not run', 'Vite development proxy not independently browser-tested'], [open_gates[3], open_gates[5]])
phases['KNOWLEDGE_RAG'] = phase('KNOWLEDGE_RAG', 'PARTIAL',
    ['Nonempty/invalid filter rejected before canonical retrieval; HTTP 422', 'Empty/default canonical query and effective profile regression pass',
     'Existing RAG/store unchanged; official fixtures not promoted to oracle', 'Native provider browser uses clearly non-official retrieval fixture'],
    ['app/knowledge/engine.py', 'app/api/routes.py', 'tests/test_effective_rag_profile.py', 'tests/test_v1_operator_control.py'],
    'Prevent silently ignored filters without inventing unapproved authority semantics', backend_tests,
    ['No functional nonempty filtering schema implemented', 'Historical official oracle findings not closed by fixtures'], [open_gates[1], open_gates[2], open_gates[3]])
phases['UI_E2E'] = phase('UI_E2E', 'PARTIAL',
    ['Actual localhost browser, built UI, real HTTP V1 handlers, existing Hermes and public projection observed',
     'Two-model fixture selection flow and safe invalid-token path observed', 'One actual local model generation observed with matching socket PID/source/request receipt'],
    ['control-plane/e2e/control-plane.spec.ts', 'control-plane/tests/assistant.test.tsx'],
    'Separate observed browser integration from mocked and unverified native dependencies', ui_tests + ['SOCKET_PROCESS_IDENTITY.json', 'SOCKET_PROCESS_IDENTITY.v2.json', 'LOCAL_PROVIDER_RECEIPTS.jsonl', 'SOURCE_IDENTITY_CHECK.json'],
    native_evidence['limits'] + ['Legacy Playwright CLI suite not run; CUA browser flow exercised directly', 'User backend PID 33160 left untouched; candidates stopped'], [open_gates[3], open_gates[5]])
phases['SECURITY'] = phase('SECURITY', 'PASS_SCOPED',
    ['Existing admin authentication retained; missing/bad token/external origin/evidence mode rejected', 'CAS and immutable request capture avoid stale/racing selection',
     'Public response schema/error sanitation asserted; no production credential writes', 'Guarded backend: no network/SQLite/arbitrary subprocess/production writes',
     'Local-provider candidate allows only loopback Ollama 11434 and new evidence writes'],
    ['app/api/control_plane.py', 'app/api/routes.py', 'control-plane/src/api.ts', 'tests/test_v1_operator_control.py'],
    'Enforce existing authorization and safe transport on new controls', backend_tests + ['FRONTEND_REGRESSION.json', 'OPERATOR_ERROR_BROWSER.jpg'],
    ['Scoped control/response security; not complete production security certification', 'Existing legacy memory governance risk remains open'], [open_gates[0], open_gates[4], open_gates[5]])
phases['REGRESSION'] = phase('REGRESSION', 'PASS_SCOPED',
    [{'backend': backend, 'frontend': frontend}, 'TypeScript --noEmit and final Vite build exit 0',
     'git diff --check exit 0', 'No tests deleted; previous failed run evidence preserved'],
    ['tests/test_v1_operator_control.py', 'tests/test_v1_response_projection.py', 'tests/test_effective_rag_profile.py', 'control-plane/tests/assistant.test.tsx', 'control-plane/e2e/control-plane.spec.ts'],
    'Validate model/configuration/Hermes/projection/memory/grounding/filter/auth/UI regressions', backend_tests + ['FRONTEND_REGRESSION.json'],
    ['One nested subprocess assembly case DESELECTED because guard blocks arbitrary subprocess; not a PASS or SKIP',
     'Earlier 243-pass/3-fail run involved harness cwd/subprocess guard and formerly ignored-filter expectation; retained and resolved',
     'Initial frontend targeted run lacked required fixture paths; full correctly configured run 67 pass',
     'Historical native Windows privilege SKIP not rerun or represented as current PASS', 'Full exhaustive V1/production suite not claimed'], [open_gates[4]])

report = {
    'timestamp': NOW, 'status': 'PARTIAL', 'implementation': 'IMPLEMENTED_SCOPED',
    'repository': str(ROOT), 'branch': read('BASELINE.json')['branch'], 'head': read('BASELINE.json')['head'],
    'authorization': 'Latest NUSANTARA V1 architecture decisions implementation & user-to-Hermes repair mandate',
    'approved_decisions': read('BASELINE.json')['approved_decisions'],
    'phase_status': {key: value['status'] for key, value in phases.items()},
    'observed_evidence': ['BASELINE.json', WRITTEN['CHANGE_AUDIT.json'], WRITTEN['LOCAL_PROVIDER_BROWSER_OBSERVATIONS.json'], 'BROWSER_OBSERVATIONS.json', 'FINAL_CHECKS.json'] + [WRITTEN[key + '.json'] for key in phases],
    'files_changed': audit['files_changed'], 'reason': 'Repair existing V1 user/Console-to-Hermes path under approved architecture decisions',
    'tests_run': {'backend': backend, 'frontend': frontend, 'typescript': 'PASS', 'frontend_build': 'PASS', 'whitespace': 'PASS'},
    'causal_changes': {'unauthorized_source_changes': audit['unauthorized_source_changes'], 'unauthorized_test_changes': audit['unauthorized_test_changes'], 'removed_files': removed},
    'limits': native_evidence['limits'] + ['Old baseline blocker text is inherited history; approved MODEL/MEMORY decisions supersede those questions, not remaining governance gates',
        'Final whitespace-only edits to Hermes/main change source fingerprint after browser capture; FINAL_CHECKS.json distinguishes observed candidate from final source. No claim final source was executed by old candidate.',
        'Initial report version prematurely stated git diff --check PASS; actual check found 3 whitespace findings. Those were corrected and verified; this report and FINAL_CHECKS supersede that assertion.'],
    'remaining_blockers': open_gates,
    'additional_decisions_required': ['V1 memory consent/ownership/retention disposition beyond temporary preservation',
        'Approved source-filter semantics and authority metadata', 'Official source issuer/jurisdiction/validity/ingest authorization',
        'Controlled target/resources/security privileges for full native integration; verified single-process topology or separately approved cross-process consistency'],
    'production_runtime': 'NOT_VERIFIED; user backend PID33160 untouched; both controlled candidates stopped',
    'v1_acceptance': 'HOLD', 'v2': 'V2_DEFERRED', 'hermes_freeze': 'NOT_PERFORMED',
}
write('V1_IMPLEMENTATION_REPORT.json', report)
write('EVIDENCE_MANIFEST.json', {'timestamp': NOW, 'files': {
    p.relative_to(OUT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in OUT.rglob('*') if p.is_file() and not p.is_symlink()
    and not any(part in ('temporary', '__pycache__') for part in p.relative_to(OUT).parts)
    and p.name != 'EVIDENCE_MANIFEST.json'}, 'limitations': 'Manifest excludes test temporary directory; no production data inspected'})
print(json.dumps({'audit': audit['status'], 'backend': backend, 'frontend': frontend, 'native_identity_matches': identity_matches, 'v1_acceptance': 'HOLD'}))
