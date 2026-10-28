"""Append-only functional closure evidence; no runtime operations or source edits."""
import ast
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
import prepare_baseline as baseline

ROOT, OUT = baseline.ROOT, baseline.OUT
sys.path.insert(0, str(ROOT))
from app.core.runtime_identity import source_build_id

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(name, value):
    with (OUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)

now = datetime.now(timezone(timedelta(hours=7))).isoformat()
before = read(OUT/'BASELINE.json')
after = baseline.snapshot()
old, current = before['preservation']['sha256'], after['sha256']
changed = sorted(p for p in old if p in current and old[p] != current[p])
added = sorted(p for p in current if p not in old)
removed = sorted(p for p in old if p not in current)
allowed = {'app/hermes/agent.py','tests/test_v1_operator_control.py','control-plane/src/api.ts','control-plane/src/assistant.tsx'}
assert set(changed) == allowed and not added and not removed and not after['errors']
files = changed + ['control-plane/tests/assistant.test.tsx']
historical_test_hash = read(ROOT/'docs/reports/v1-user-hermes-implementation/CHANGE_AUDIT.20261009T093819.json')['supplementary_changes']['control-plane/tests/assistant.test.tsx']['after_sha256']
audit = {'timestamp': now, 'status': 'PASS', 'scope': 'Causal source edits relative to fresh baseline; generated dist and frontend test supplement explicit',
    'changed': files, 'added_source_files': added, 'removed': removed, 'unauthorized_source_changes': 0,
    'source_hash_changes': {p:{'before':old[p],'after':current[p]} for p in changed},
    'frontend_test_supplement': {'path':'control-plane/tests/assistant.test.tsx','historical_before_sha256':historical_test_hash,
        'after_sha256':hashlib.sha256((ROOT/'control-plane/tests/assistant.test.tsx').read_bytes()).hexdigest()},
    'graph_cache_unchanged':all(current.get(p)==value for p,value in old.items() if p.startswith('graphify-out/cache/')),
    'contracts_and_historical_reports_unchanged':all(current.get(p)==value for p,value in old.items() if p.startswith(('docs/contracts/','docs/reports/','reports/'))),
    'memory_policy_rag_unchanged':all(current[p]==old[p] for p in ['app/memory/engine.py','app/policy/engine.py','app/core/gate_integration.py','app/knowledge/engine.py','app/knowledge/rag.py','app/knowledge/store.py','app/knowledge/grounding.py']),
    'v2_source_tests_unchanged':all(current.get(p)==value for p,value in old.items() if p.startswith(('app/devcore/','app/api/v2','tests/v2/'))),
    'git_before':before['working_tree'],'git_after':baseline.git('status','--short'),
    'head_before':before['head'],'head_after':baseline.git('rev-parse','HEAD')['stdout'].strip(),
    'limitations':['Baseline excludes control-plane/tests and dist; frontend test attribution supplements historical hash and recorded patches',
        'Compiled frontend rebuilt with --emptyOutDir false; old assets retained, dist index references new build',
        'Initial audit helper read JSON with Windows default encoding and falsely displayed two filename renames; corrected UTF-8 comparison shows zero additions/removals. No filesystem rename occurred.']}
write('CHANGE_AUDIT.json',audit)

def count_xml(folder):
    cases=list(ET.parse(OUT/folder/'results.xml').getroot().iter('testcase'))
    return {'pass':sum(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases),
        'fail':sum(c.find('failure') is not None or c.find('error') is not None for c in cases),
        'skip':sum(c.find('skipped') is not None for c in cases)}

node = r'C:\Users\dmaza\AppData\Local\hermes\node\node.exe'
run_relative=OUT.relative_to(ROOT).as_posix()
commands=[
    f'.venv/Scripts/python.exe -B {run_relative}/prepare_baseline.py',
    f'.venv/Scripts/python.exe -B {run_relative}/verify_backend.py targeted (before and after greeting patch)',
    f'.venv/Scripts/python.exe -B {run_relative}/verify_backend.py regression',
    f'{node} --require ./tests/inspection-preview-network-guard.cjs node_modules/vitest/vitest.mjs run tests/assistant.test.tsx --pool=threads --maxWorkers=1 --minWorkers=1 --reporter=json --outputFile=../{run_relative}/FRONTEND_TARGETED.json',
    f'{node} --require ./tests/inspection-preview-network-guard.cjs node_modules/vitest/vitest.mjs run tests/assistant.test.tsx --pool=threads --maxWorkers=1 --minWorkers=1 --reporter=json --outputFile=../{run_relative}/FRONTEND_REGRESSION.json',
    f'{node} node_modules/typescript/bin/tsc --noEmit',
    f'{node} node_modules/vite/bin/vite.js build --emptyOutDir false',
    f"$env:V1_LOCAL_PROVIDER='1'; & .venv\\Scripts\\python.exe -B {run_relative}/native_candidate.py (port 18013)",
    f'{baseline.GIT} --no-optional-locks diff --check',
    'Read-only GET user port8000 /health and /openapi.json; socket and Win32 process checks; stop only owned candidate PID35788',
    'Browser CUA: root Hallo, + New Chat, mixed greeting/question, Console inventory and refresh',
    'HTTP POST candidate /v1/chat with user_input in Hallo/Halo/Hai/Selamat pagi; GET candidate /v1/control-plane/model-status and authenticated /models',
]
frontend=read(OUT/'FRONTEND_REGRESSION.json')
regression={'timestamp':now,'status':'PASS','commands':commands,
    'initial_reproduction':{'evidence':'targeted-20261009-102003/results.xml',**count_xml('targeted-20261009-102003'),
        'reason':'Five greeting cases returned knowledge-base insufficiency before fix; genuine reproduction retained'},
    'targeted_backend':{'evidence':'targeted-20261009-102040/results.xml',**count_xml('targeted-20261009-102040')},
    'backend_regression':{'evidence':'regression-20261009-102112/results.xml',**count_xml('regression-20261009-102112'),'deselected':1},
    'frontend':{'evidence':'FRONTEND_REGRESSION.json','pass':frontend['numPassedTests'],'fail':frontend['numFailedTests'],'skip':frontend['numPendingTests']},
    'guards':read(OUT/'regression-20261009-102112/guards.json'),
    'typescript':{'status':'PASS','exit':0},'build':{'status':'PASS','exit':0},'python_syntax':{'status':'PASS','files':['app/hermes/agent.py','tests/test_v1_operator_control.py']},
    'whitespace':{'status':'PASS','exit':0},
    'not_run':['Full historical test suites; selected bounded regression reused for changed Hermes/model/projection/grounding path',
        'One pre-existing nested subprocess assembly test DESELECTED due guard, not PASS or SKIP',
        'Native semantic-worker/production RAG/database integration', 'Native symlink operational tests with Windows privilege',
        'Full legacy Playwright suite; direct CUA browser verification used', 'Two-real-model switching; one model installed'],
    'limits':['Guarded backend uses actual Ollama adapter with mock transport and explicit language/retrieval fixtures',
        'Shared pure grounding tests housed under tests/v2 are regression only; no V2 endpoint or implementation changed']}
write('REGRESSION.json',regression)

native=read(OUT/'NATIVE_RUNTIME.json')
cleanup=read(OUT/'CLEANUP.json')
receipt=json.loads((OUT/'LOCAL_PROVIDER_RECEIPTS.jsonl').read_text(encoding='utf-8').splitlines()[-1])
assert receipt['process_id']==native['socket_pid'] and receipt['build_id']==native['status']['source_build_id']==source_build_id()
assert all(receipt[k]=='llama3.2:1b' for k in ['selected_model','payload_model','actual_model'])
assert cleanup['candidate_stopped'] and cleanup['user_runtime_unchanged']
# Validate actual HTTP responses with unchanged public classes, without importing production routes.
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
tree=ast.parse((ROOT/'app/api/routes.py').read_text(encoding='utf-8-sig'))
classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name.startswith('_PublicChat')]
namespace={'BaseModel':BaseModel,'ConfigDict':ConfigDict,'Field':Field,'Literal':Literal}
exec(compile(ast.Module(body=classes,type_ignores=[]),'public_schema_read_only','exec'),namespace)
greetings=read(OUT/'NATIVE_PUBLIC_GREETINGS.json')
for response in greetings:
    namespace['_PublicChatResponse'].model_validate(response)
    assert response['provider_status']=='local_rule' and response['response']=='Halo! Ada yang bisa saya bantu?'
runtime={'timestamp':now,'status':'PASS','scope':'Controlled candidate source/build UI, actual V1/Hermes HTTP and local Ollama execution',
    'source_fingerprint':source_build_id(),'provider_receipt':receipt,'candidate':native,'cleanup':cleanup,
    'bundle_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'control-plane/dist/index.html',ROOT/'control-plane/dist/assets/index-DWlaYDof.js']},
    'browser_observations':['Root Hallo renders natural greeting', '+ New Chat removes displayed previous turn and restores empty state',
        'Loading disables submit and New Chat', 'Mixed greeting/KTP question reaches real Ollama and displays grounded abstention',
        'Console actual model/provider renders; inventory exposes only llama3.2:1b; refresh works', 'No browser error logs'],
    'public_http_greetings':{'status':'PASS','count':len(greetings),'contract_schema':'Unchanged strict backend public response schema'},
    'screenshots':['GREETING_BROWSER.jpg','SUBSTANTIVE_BROWSER.jpg','CONSOLE_BROWSER.jpg'],
    'provider':'ACTUAL_LOCAL_OLLAMA_UNMODIFIED_HTTP_CLIENT','semantic':'EXPLICIT_FIXTURE','retrieval':'EXPLICIT_NON_OFFICIAL_FIXTURE',
    'limitations':['Greeting is nonfactual local_rule, not a model-generated answer; mixed substantive question has actual provider receipt',
        'Provider model name is not loaded-weight attestation', 'App fingerprint is disk/import source snapshot, not all transitive loaded code or frontend bundle; separate bundle hashes recorded',
        'No official knowledge or native semantic/production RAG verified; no port attestation bypass',
        'Current user runtime remains different build with missing model-control endpoints']}
write('RUNTIME_EVIDENCE.json',runtime)

def capability(feature,ui,api,owner,status,evidence,blocker=''):
    return dict(feature=feature,ui_entry=ui,api_endpoint=api,backend_owner=owner,actual_execution_status=status,test_evidence=evidence,remaining_defect_or_blocker=blocker)

matrix=[
    capability('Standalone greetings','/','POST /v1/chat','Existing Hermes.execute_v1/local_rule','PASS','48 backend targeted; 4 actual HTTP greetings; GREETING_BROWSER.jpg','User runtime old build not promoted'),
    capability('Substantive and mixed questions','/','POST /v1/chat','Hermes -> Knowledge -> Ollama -> grounding -> public projector','PASS','257 regression; real browser mixed-question receipt','Insufficient official evidence correctly abstains; native semantic/RAG not verified'),
    capability('+ New Chat','/','No new API; next chat uses new session_id','Existing client session state; legacy MemoryEngine unchanged','PASS','Frontend new-chat regression and browser reset','Client reset does not delete server history or establish authenticated isolation'),
    capability('Submission/response/loading/error/retry','/','POST /v1/chat','UserChat / Hermes','PASS','10 frontend tests; browser loading and response; existing retry test'),
    capability('Long/multiline rendering and follow-up session continuity','/','POST /v1/chat','UserChat transient history / existing session ID','PASS','Frontend complete repeated multiline answer and same-session follow-up tests; backend substantive follow-up tests','Provider token limits still apply; semantic conversation recall not implemented'),
    capability('Conversation recall from memory in model prompt','/','POST /v1/chat','Existing MemoryEngine; prompt helper does not consume stored context','NOT_IMPLEMENTED','Static Hermes.run context=None / _build_user_prompt; bounded regression','Enabling memory read semantics requires CC05 governance decision; no unapproved prompt-memory injection'),
    capability('Durable personal chat history','/','No personal-history persistence API','Existing MemoryEngine process-local deque','NOT_IMPLEMENTED','Static memory/context inspection; UI transient state disclaimer','No new persistence/consent/retention/user isolation guarantees'),
    capability('Legacy memory write/read interface','/','No public memory read endpoint claimed','GateIntegration.memory','PASS','Baseline unchanged memory/gate hashes; write preservation tests','CC05 client-selected sessions, write-before-answer-policy, ownership/retention remain open'),
    capability('Model status/inventory on current candidate','/console','GET /v1/control-plane/model-status; GET /v1/control-plane/models','Existing Settings owner + Ollama adapter','PASS','Native Console browser inventory, candidate diagnostics, backend authorization tests','Full readiness remains NOT_VERIFIED; single-process scope retained'),
    capability('Model status/inventory on user runtime','/console','Same endpoints expected','User PID33160, port8000 old source registration','BLOCKED','USER_RUNTIME_BEFORE.json OpenAPI/health; CLEANUP.json','User runtime does not register endpoints; replacing/restarting requires explicit authorization'),
    capability('Operator selection','/console','POST /v1/control-plane/model-selection','Existing atomic Settings owner','PASS','257 backend regression covers selection/CAS/auth/failure; prior unchanged-source-owner evidence','Current process only; no two-real-model switch or weight proof'),
    capability('Knowledge query/ranking/evidence/grounding','/; /knowledge','POST /v1/knowledge/search; POST /v1/chat','Existing KnowledgeEngine/RAG/store/grounding','PASS','Relevant canonical RAG profile/ranking tests with injected stores/embedding; actual facade fixture/browser abstention','Native semantic/store/production query not verified; relevance is not official authority'),
    capability('Nonempty filter enforcement','/knowledge','POST /v1/knowledge/search','Existing KnowledgeEngine','PASS','HTTP 422 and facade regression reject unsupported filter before retrieval','Approved filter grammar/metadata schema missing; no functional nonempty filtering invented'),
    capability('Public schema/correlation/security','/; /console','Existing /v1 endpoints','Existing projector/admin/local boundary','PASS','48 targeted + 257 regression + strict native HTTP schema + provider request ID','Operational Windows security/policy enforcement gates remain open'),
]
write('CAPABILITY_MATRIX.json',{'timestamp':now,'capabilities':matrix,'status_definition':'PASS covers the stated scope/evidence only; native dependencies and runtime promotion separately blocked'})
implementation={'timestamp':now,'status':'PASS','files_changed':files,'findings':[
    {'id':'GREETING','root_cause':'Hermes had no complete-input nonfactual greeting branch; deterministic helper always None; factual grounding rejects generated greeting without evidence',
     'reproduction':'5 FAIL/43 PASS before patch','fix':'Whole-input greeting whitelist in existing Hermes; reuse existing local_rule after normal core/retrieval/trust/gate stages',
     'preserves_contract':'No response field/type changes; nonfactual text only; trust/policy/gates unchanged; mixed questions remain provider/grounding controlled'},
    {'id':'NEW-CHAT','root_cause':'Existing legacy root exposed + New Chat, but replacement React root omitted it',
     'fix':'Restore client-only reset/new UUID using existing state, disabled in-flight; no server deletion or persistence',
     'preserves_contract':'Same session_id request field, same legacy memory owner; no new endpoint'},
    {'id':'MODEL-404','root_cause':'Frontend requests correct registered source routes; user active runtime OpenAPI has no model-control endpoints and a different fingerprint',
     'fix':'Actionable model-endpoint-specific 404 error; no fabricated fallback or VERIFIED status',
     'remaining':'Actual user-runtime service alignment BLOCKED without explicit restart/replacement authorization'}],
    'why_minimal':'Existing engine, owner, projector, trust/grounding and API preserved; only greeting routing, omitted client reset, and explicit error mapping changed',
    'remaining_confirmed_gaps':['Model runtime registration mismatch on user process', 'Conversation memory context not consumed in prompt; requires governed memory-read decision', 'No durable personal chat persistence implemented']}
write('IMPLEMENTATION_REPORT.json',implementation)
gates=read(ROOT/'docs/reports/v1-user-hermes-implementation/V1_IMPLEMENTATION_REPORT.json')['remaining_blockers']
gates+=['Current user runtime port8000 missing final model-control routes; explicit controlled restart/replacement authorization required',
        'Conversation recall memory-read semantics not defined/implemented; preserve legacy capture until CC05 decision']
write('REMAINING_GATES.json',{'timestamp':now,'v1_acceptance':'HOLD','gates':gates,'v2':'DEFERRED'})
summary={'timestamp':now,'status':'BLOCKED','scope':'Safe functional fixes implemented and verified on controlled candidate; remaining acceptance gates open',
    'implemented_and_verified':['Whole-input greeting route', 'Restored existing New Chat client action', 'Model missing-endpoint error mapping', 'Tests and controlled browser/HTTP integration'],
    'implemented_not_fully_verified':['Full native semantic/RAG integration','Operational/security enforcement','Operator global cross-process behavior'],
    'failed':['Initial greeting reproduction: five failures, resolved by patch; retained evidence'],
    'blocked':['User-runtime 404 service alignment requires explicit restart authorization','Memory governance','Official oracle and filter metadata decisions','Deployment/worker/Windows security target'],
    'not_implemented':['Durable personal chat persistence','Model prompt consumption of conversation memory'],
    'not_in_scope':['V2','Deployment/commit/push/migration','Restart or reconfigure user runtime'],
    'files_changed':files,'evidence':['BASELINE.json','CAPABILITY_MATRIX.json','IMPLEMENTATION_REPORT.json','REGRESSION.json','RUNTIME_EVIDENCE.json','CHANGE_AUDIT.json','REMAINING_GATES.json'],
    'source_fingerprint':source_build_id(),'tests':{'backend':regression['backend_regression'],'frontend':regression['frontend']},
    'v1_acceptance':'HOLD','v2':'DEFERRED','user_runtime_untouched':cleanup['user_runtime_unchanged']}
write('FINAL_REPORT.json',summary)
print(json.dumps({'status':summary['status'],'backend':regression['backend_regression'],'frontend':regression['frontend'],'audit':'PASS','v1_acceptance':'HOLD','report':str(OUT/'FINAL_REPORT.json')}))
