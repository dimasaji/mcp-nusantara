"""Assemble immutable evidence and scope audit; no runtime/application imports."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
from prepare_baseline import snapshot, write

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
baseline = json.loads((OUT / 'BASELINE.json').read_text(encoding='utf-8'))
now = datetime.now(timezone(timedelta(hours=7))).isoformat()
before = baseline['preservation']['sha256']
after = snapshot()
changed = [p for p, h in before.items() if after['sha256'].get(p) != h]
added = sorted(set(after['sha256']) - set(before))
allowed_added = ['docs/contracts/NUSANTARA-CONTROL-PLANE-V1.md']
unattributed = [p for p in added if p not in allowed_added]
audit = {'existing_files_checked': len(before), 'modified_or_missing_existing_files': changed,
         'added_outside_evidence_directory': added, 'unattributed_added': unattributed,
         'read_errors': after['errors'], 'source_test_configuration_changes': [],
         'cache_preserved': all(after['sha256'].get(p) == h for p, h in before.items() if p.startswith('graphify-out/cache/')),
         'historical_evidence_preserved': not any(p.startswith(('reports/', 'docs/reports/')) for p in changed)}

def test_result(mode):
    path = OUT / (mode + '-v3-results.xml')
    suite = ET.parse(path).getroot().find('testsuite')
    guards = json.loads((OUT / (mode + '-v3-guards.json')).read_text(encoding='utf-8-sig'))
    return {'passed': int(suite.attrib['tests']) - int(suite.attrib['failures']) - int(suite.attrib['errors']) - int(suite.attrib['skipped']),
            'failed': int(suite.attrib['failures']), 'errors': int(suite.attrib['errors']), 'skipped': int(suite.attrib['skipped']),
            'evidence': path.name, 'guard_evidence': mode + '-v3-guards.json', 'guard_violations': guards['violations']}

targeted, regression = test_result('targeted'), test_result('regression')
process = {'inspection': 'Read-only Win32_Process discovery; not socket owner or active-build correlation',
           'observed_backend_candidates': [
               {'pid': 37704, 'parent_pid': 20228, 'executable': str(ROOT / '.venv/Scripts/python.exe'), 'created_at': '2026-10-08T20:03:49.613978+07:00'},
               {'pid': 33160, 'parent_pid': 37704, 'executable': r'C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe', 'created_at': '2026-10-08T20:03:49.631080+07:00'}],
           'launch_application': 'app.main:app', 'launch_host': '127.0.0.1', 'launch_port': 8000,
           'reload': False, 'active_source_build': 'NOT_VERIFIED', 'runtime_profile': 'NOT_VERIFIED',
           'effective_provider_model': 'NOT_VERIFIED', 'health_openapi_chat_requests_sent': 0}

common = {'timestamp': now, 'repository': baseline['repository'], 'branch': baseline['branch'], 'head': baseline['head'],
          'changes': 'Evidence and new draft Control Plane contract only; stopped at unresolved architectural decisions',
          'files_changed': [], 'source_changes': [], 'test_changes': [], 'configuration_changes': [],
          'runtime_identity': process, 'live_integration_verified': False,
          'unauthorized_changes': len(changed) + len(unattributed), 'change_audit': audit,
          'limitations': ['Pure isolated verification is not HTTP/runtime/official-source integration proof',
                          'No provider/model/worker, live DB, production restart, deployment or graph query executed',
                          'No V2 implementation or Hermes freeze performed']}

def report(name, scope, status, results, tests=None, decisions=None):
    value = {**common, 'scope': scope, 'results': results, 'tests': tests or {'executed': False},
             'decisions_required': decisions or [], 'final_status': status}
    value['files_changed'] = ['docs/reports/v1-closure-20261008/' + name]
    write(name, value)

report('CC01_RESPONSE_PROJECTION.json', 'Existing V1 public projection, internal result preservation and contract fields', 'PASS_SCOPED',
       {'source': ['app/api/routes.py:108', 'app/api/routes.py:156', 'app/api/routes.py:1328'],
        'current_projection': 'Strict public schema and explicit projection already implemented; no duplicate schema or patch',
        'checks': ['11 current-source pure tests: internal sentinel exclusion, internal input preservation, public key/citation preservation, strict invalid-value rejection'],
        'historical_http_evidence': 'reports/V1_CC01_OPTION_C_IMPLEMENTATION.json; not a current HTTP rerun',
        'backward_compatibility': 'Historical explicitly approved Option C public boundary retained; no new response changes',
        'current_http_and_live_registration': 'NOT_VERIFIED'}, targeted)

report('CC05_MEMORY_GOVERNANCE.json', 'V1 READ/WRITE/REJECT/NO-MEMORY enforcement', 'REVIEW_REQUIRED',
       {'source': ['app/core/gate_integration.py:34', 'app/core/gate_integration.py:84', 'app/core/gate_integration.py:106', 'app/api/routes.py:93', 'app/api/routes.py:1307'],
        'WRITE': 'Automatic user write before answer policy and automatic assistant write',
        'READ': 'Client session keyed memory.context, including shared default web; no V1 ownership guard',
        'REJECT': 'No per-operation memory rejection contract implemented', 'NO-MEMORY': 'No explicit V1 control implemented',
        'governance_acceptance': 'NOT_SATISFIED', 'provenance': 'Memory metadata/timestamps do not establish consent or ownership',
        'existing_test_interpretation': 'Passing legacy capture tests confirms current behavior; it is not a governance PASS',
        'implementation': 'STOPPED; no V2 adapter substitution or new memory engine'},
       {'existing_gate_tests': 'Included in selected regression; memory capture test passed'}, [baseline['active_blockers'][0]['decision_required']])

oracle = json.loads((ROOT / 'reports/V1_CLOSURE_ORACLE_AUDIT.json').read_text(encoding='utf-8-sig'))
cases = [{k: case.get(k) for k in ('id', 'domain', 'oracle_status', 'authoritative_status', 'closure_status')} for case in oracle['cases']]
report('CC06_KNOWLEDGE_RAG.json', 'Filter, reranker, grounding, relevance/authority and official oracle', 'REVIEW_REQUIRED',
       {'source': ['app/knowledge/engine.py:33', 'app/knowledge/rag.py:448', 'app/knowledge/rag.py:707'],
        'filter': 'IGNORED: del filter; not an access/source policy boundary',
        'reranker': 'Receipt labels actual simple_keyword_overlap when requested and enabled; facade does not request rerank. Not a learned reranker proof.',
        'grounding': 'LC-DECIMAL-001 D4 PASS preserved; current grounding tests included in selected regression',
        'trust': 'Relevance-based supports_claim does not certify official authority',
        'oracle_cases_historical': cases, 'live_database_inventory': 'NOT_INSPECTED',
        'official_oracle': 'OPEN: two REVIEW_REQUIRED cases and one MISSING case remain in historical authoritative audit; no later closure evidence established',
        'non_government': 'Nasi goreng remains fixture/non-government; never promoted to official knowledge',
        'implementation': 'STOPPED; filter semantics/approved authority schema and official sources not invented'},
       {'grounding_regression': '26 existing tests passed within selected suite; not a RAG/official oracle integration run'},
       [baseline['active_blockers'][1]['decision_required'], baseline['active_blockers'][2]['decision_required']])

report('SECURITY.json', 'Repository security boundary review; selected isolated checks', 'PARTIAL_REVIEW_REQUIRED',
       {'path_traversal_sensitive_paths': 'Earlier scoped developer-core hardening and D4 evidence preserved; native symlink requirement remains ENVIRONMENT_LIMITED historically',
        'prompt_injection': 'Cannot certify end-to-end prompt injection isolation from projection/grounding tests alone',
        'unauthorized_modification_database_runtime_command': 'Verification runner blocks writes outside fresh evidence, DB, network, subprocess and real app imports; production boundary not newly exercised',
        'admin_auth': 'Existing require_admin rejects absent configured token or absent/mismatched submitted token',
        'provider_credentials_public_api': 'No secret values read/reported; current pure public projection excludes internal sentinels; full credential exposure audit NOT_VERIFIED',
        'risky_action_policy': 'Existing PolicyEngine blocks listed sensitive actions; Control Plane permission → actual operation approval linkage NOT_VERIFIED',
        'unsafe_configuration_mutation': 'Existing owner immutable/compose-once; no runtime settings API added',
        'container_finding': 'docker-compose.yml database password has change-me fallback; production target/credential provisioning requires review',
        'mandatory_security_acceptance': 'OPEN'}, {'selected_regression': regression, 'native_symlink': 'NOT_RERUN; historical missing privilege remains unresolved'})

report('DEPLOYMENT.json', 'Static deployment/startup/configuration/provider identity review; no deployment', 'NOT_VERIFIED',
       {'files': ['app/main.py', 'Dockerfile', 'docker-compose.yml', 'pyproject.toml'],
        'startup': 'NORMAL import constructs existing knowledge/language dependencies; not started by verification',
        'health_chat': 'No live request sent; current build correlation absent',
        'config_identity': 'Existing configuration owner contract tests and provider/router identity unit tests passed; not installed-model proof',
        'container': 'Dockerfile creates separate IndoBERT worker venv, runs non-root uvicorn on 8000; compose binds loopback 8000, data volume and optional .env',
        'dependencies': 'Static declarations read; no package installation/change/build or container dependency verification',
        'port_profile': 'Process launch flags observed; actual listening owner and effective profile not verified',
        'build_deploy_restart': 'NOT_PERFORMED', 'target': 'UNRESOLVED'}, {'controlled_configuration_router': 'Included in selected regression'}, [baseline['active_blockers'][7]['decision_required']])

report('CONTROL_PLANE.json', 'Human-facing contract and actual runtime control readiness', 'PARTIAL_REVIEW_REQUIRED',
       {'draft_contract': 'docs/contracts/NUSANTARA-CONTROL-PLANE-V1.md',
        'existing_capability': baseline['control_plane_capability'],
        'new_capability': 'None; contract documents real capabilities and missing decisions without cosmetic selectors',
        'mapping': 'Human intent → API → existing authority → actual execution not implemented',
        'ui_changes': 'NONE; blocked before dependency-specific UI implementation',
        'blocked_controls': ['model profiles', 'execution modes', 'source policy', 'answer level', 'risky permission execution'],
        'implementation_stop_reason': 'Unknown selection ownership/lifecycle and mode/source semantics require architecture decisions'},
       decisions=[b['decision_required'] for b in baseline['active_blockers'][3:6]])

report('MODEL_SWITCHING.json', 'Real Control Plane model selection → V1 chat provider identity', 'PARTIAL_REVIEW_REQUIRED',
       {'existing_owner': 'Settings.effective_configuration -> immutable NusantaraConfig; second composition with changes rejected',
        'request_override': 'Existing ChatRequest.model -> OllamaProvider(model=...) supported; not a human profile API',
        'registry': 'ModelRouter operates on registered providers; no approved Cepat/Pintar/Hemat catalog',
        'effective_model_proof': '14 provider/router configuration unit tests passed; no UI selection receipt or chat switching E2E',
        'installed_availability': 'NOT_VERIFIED', 'two_profile_acceptance': 'NOT_SATISFIED', 'implementation': 'STOPPED'},
       {'provider_router_unit_tests': 14, 'full_switching_e2e': 'NOT_RUN'}, [baseline['active_blockers'][3]['decision_required']])

report('ORCHESTRATION_CONTROL.json', 'Selectable existing V1 execution paths consumed by chat', 'FAIL_REVIEW_REQUIRED',
       {'source': ['app/orchestration/engine.py:8', 'app/core/gate_integration.py', 'app/api/routes.py:93'],
        'existing_engine': 'Collects supplied stage artifacts; does not select/execute different mode paths',
        'chat': 'Current internal branch selection exists; request has no orchestration/source/permission selection contract',
        'two_mode_acceptance': 'NOT_SATISFIED', 'implementation': 'STOPPED; no new engine, LangGraph or V2 inserted'},
       {'legacy_stage_tests': 'Passed in selected regression; not mode-selection proof'}, [baseline['active_blockers'][4]['decision_required']])

report('UI_E2E.json', 'Mandatory UI → API → runtime → Hermes cases', 'FAIL_REVIEW_REQUIRED',
       {'cases': {case: 'NOT_RUN_UNSUPPORTED_CONTROL' for case in ['Cepat effective model', 'Pintar effective model', 'orchestration consumed by chat', 'source policy consumed by runtime', 'risky permission approval enforced']},
        'existing_ui': 'Evidence and acceptance workflow; no functioning model/source/orchestration settings control',
        'vite': 'Existing proxy covers control-plane, health, preview; not assistant /v1/chat',
        'cosmetic_controls_added': False, 'new_live_chat_requests': 0, 'mandatory_acceptance': 'NOT_SATISFIED'},
       decisions=[baseline['active_blockers'][5]['decision_required']])

report('REGRESSION.json', 'Selected current-source pure targeted and regression checks', 'PASS_SCOPED',
       {'targeted': targeted, 'selected_regression': regression,
        'full_v1_regression': 'NOT_RUN; real application/provider/worker/store imports intentionally blocked',
        'interpretation': 'Passing legacy memory/stage tests does not close new governance/control gates',
        'harness_preflight': [{'revision': 1, 'result': 'Stopped before tests: existing routes file UTF-8 BOM requires utf-8-sig reader'},
                              {'revision': 2, 'result': '11 tests collected but not run: installed asyncio plugin required by strict existing config'},
                              {'revision': 3, 'result': 'Existing asyncio plugin explicitly loaded; no source/test/dependency changes; tests PASS'}],
        'environment_changes': 'Child-process testing variables only; no .env or service environment changes',
        'historical_regression': 'Not substituted as proof of current full V1'}, {'targeted': targeted, 'selected_regression': regression})

report('V1_CLOSURE_REPORT.json', 'All mandatory V1 acceptance gates and stop decision', 'HOLD',
       {'V1_STATUS': 'HOLD', 'BLOCKERS': baseline['active_blockers'],
        'gates': {'CC01': 'PASS_SCOPED', 'LC-DECIMAL-001': 'D4_PASS_SCOPED', 'CC05': 'REVIEW_REQUIRED',
                  'CC06_FILTER': 'REVIEW_REQUIRED', 'CC06_OFFICIAL_ORACLE': 'OPEN_REVIEW_REQUIRED',
                  'SECURITY': 'PARTIAL_ENVIRONMENT_LIMITED', 'DEPLOYMENT_RUNTIME': 'NOT_VERIFIED',
                  'CONTROL_PLANE': 'PARTIAL', 'MODEL_SWITCHING': 'PARTIAL', 'ORCHESTRATION': 'FAIL',
                  'UI_API_RUNTIME': 'FAIL', 'SELECTED_REGRESSION': 'PASS', 'FULL_V1_REGRESSION': 'NOT_VERIFIED'},
        'CONTROL_PLANE': 'PARTIAL', 'MODEL_SWITCHING': 'PARTIAL', 'ORCHESTRATION': 'FAIL',
        'UI_API_RUNTIME': 'FAIL', 'REGRESSION': 'PASS_SCOPED_ONLY', 'HERMES_FREEZE': 'NOT_PERFORMED',
        'implementation': 'Stopped on unresolved architectural blockers as explicitly directed; evidence-only changes',
        'acceptance_rule': 'Mandatory missing gates keep V1 HOLD regardless of passing isolated tests',
        'required_review': 'Resolve model selection owner/profile mappings, memory policy, V1 mode semantics and source authority/filter contract; supply approved official snapshots and controlled runtime/environment proof'},
       {'targeted': targeted, 'selected_regression': regression}, [b['decision_required'] for b in baseline['active_blockers']])

write('CHANGE_AUDIT.json', {**common, 'scope': 'Preservation of existing source/tests/config/cache/evidence',
                           'final_status': 'PASS' if not changed and not unattributed and not after['errors'] else 'REVIEW_REQUIRED',
                           'files_changed': ['docs/contracts/NUSANTARA-CONTROL-PLANE-V1.md', 'docs/reports/v1-closure-20261008/ (new artifacts only)'],
                           'tests': {'targeted': targeted, 'selected_regression': regression}, 'results': audit})
print(json.dumps({'reports': 12, 'targeted': targeted['passed'], 'selected_regression': regression['passed'],
                  'existing_file_changes': changed, 'unattributed_additions': unattributed, 'status': 'HOLD'}))
