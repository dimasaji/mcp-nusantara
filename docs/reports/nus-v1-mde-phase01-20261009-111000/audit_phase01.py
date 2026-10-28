"""NUS-V1-MDE-WORK-CONTRACT-001 Phase0/1: static audit and safe GET only."""
import ast
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
CONTRACT=Path('C:/Users/dmaza/.codex/attachments/addb901b-7c72-4c07-af45-731c888b10b3/Pasted text.txt')
def now():return datetime.now(timezone(timedelta(hours=7))).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name,data):
    with (OUT/name).open('x',encoding='utf-8') as stream:json.dump(data,stream,ensure_ascii=False,indent=2)
spec=importlib.util.spec_from_file_location('baseline',ROOT/'docs/reports/v1-functional-closure-20261009-101736/prepare_baseline.py')
baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline);baseline.OUT=OUT
tree=ast.parse((ROOT/'app/core/runtime_identity.py').read_text(encoding='utf-8'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='source_build_id')
ns={'ROOT':ROOT,'Path':Path,'hashlib':hashlib};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<existing-fingerprint>','exec'),ns)
def snapshot():
    value=baseline.snapshot()
    for rel in ['control-plane/dist','control-plane/tests','control-plane/e2e','config','service','control-plane/vitest.config.ts','ROLLBACK_PLAN.md','.env.example','.dockerignore']:
        base=ROOT/rel
        for p in [base] if base.is_file() else base.rglob('*'):
            if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:
                value['sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    return value
before={'timestamp':now(),'head':baseline.git('rev-parse','HEAD'),'branch':baseline.git('branch','--show-current'),'git_status':baseline.git('status','--short'),'fingerprint':ns['source_build_id'](),'preservation':snapshot()}
write('BASELINE.json',before)
contract_meta={'contract_id':'NUS-V1-MDE-WORK-CONTRACT-001','version':'1.0.0','path':str(CONTRACT),'sha256':sha(CONTRACT),'declared_status':'PROPOSED_PENDING_IMPLEMENTATION','invocation':'User instructed execution and attached exact contract. Phase0/1 read-only audit authorized; section9 requires review and further source-change authorization. No runtime/data/provider/deployment authorization inferred.'}
write('CONTRACT_REFERENCE.json',contract_meta)
inventory={};routes=[];parse_errors=[]
for p in (ROOT/'app').rglob('*.py'):
    if '__pycache__' in p.parts or p.is_symlink():continue
    rel=p.relative_to(ROOT).as_posix()
    if '/v2' in rel or rel.startswith('app/devcore/'):
        inventory[rel]={'sha256':sha(p),'status':'V2_DEFERRED_NOT_INSPECTED'};continue
    try:
        module=ast.parse(p.read_text(encoding='utf-8-sig'))
        symbols=[{'name':n.name,'line':n.lineno,'kind':type(n).__name__} for n in module.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
        imports=[ast.unparse(n) for n in module.body if isinstance(n,(ast.Import,ast.ImportFrom))]
        inventory[rel]={'sha256':sha(p),'symbols':symbols,'imports':imports,'evidence':'AST_STATIC_NOT_RUNTIME_EXECUTION'}
        prefix=''
        for n in module.body:
            if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='APIRouter':
                for k in n.value.keywords:
                    if k.arg=='prefix' and isinstance(k.value,ast.Constant):prefix=k.value.value
        for n in module.body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                for d in n.decorator_list:
                    if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr in ['get','post','put','delete','patch'] and d.args and isinstance(d.args[0],ast.Constant):
                        routes.append({'file':rel,'line':n.lineno,'symbol':n.name,'method':d.func.attr.upper(),'path':prefix+d.args[0].value,'status':'SOURCE_DECLARATION_ONLY'})
    except (SyntaxError,UnicodeError) as exc:parse_errors.append({'file':rel,'error':type(exc).__name__})
frontend=[];test_inventory=[]
for base in [ROOT/'control-plane/src',ROOT/'control-plane/tests',ROOT/'control-plane/e2e']:
    for p in base.rglob('*'):
        if not p.is_file() or p.suffix not in ['.ts','.tsx','.css']:continue
        text=p.read_text(encoding='utf-8-sig')
        frontend.append({'path':str(p),'sha256':sha(p),'exports':re.findall(r'export (?:async )?(?:function|const|class) (\w+)',text)})
        if base.name in ['tests','e2e']:
            test_inventory.append({'file':str(p),'sha256':sha(p),'test_names':re.findall(r"(?:it|test)(?:\.each\([^\n]*?\))?\(['\"]([^'\"]+)",text),'execution':'NOT_RUN_THIS_AUDIT'})
for p in (ROOT/'tests').rglob('*.py'):
    if '__pycache__' in p.parts:continue
    rel=p.relative_to(ROOT).as_posix()
    if '/v2/' in rel:continue
    try:
        module=ast.parse(p.read_text(encoding='utf-8-sig'))
        names=[{'name':n.name,'line':n.lineno} for n in ast.walk(module) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')]
        test_inventory.append({'file':rel,'sha256':sha(p),'tests':names,'execution':'NOT_RUN_THIS_AUDIT'})
    except (SyntaxError,UnicodeError):pass
contracts=[{'path':str(p),'sha256':sha(p)} for p in (ROOT/'docs/contracts').glob('*.md')]
write('ARCHITECTURE_INVENTORY.json',{'contract_id':contract_meta['contract_id'],'phase':0,'timestamp':now(),'modules':inventory,'source_route_declarations':routes,'frontend':frontend,'tests':test_inventory,'contracts':contracts,'parse_errors':parse_errors,'source_startup_boundary':'app.main NORMAL branch imports V1 routes (KnowledgeEngine/LanguageEngine construction, SQLite/native resource side effects). No application import/startup performed; ATTESTATION/evidence-only modes are not substitutes for NORMAL proof.','source_fingerprint_scope':'app executable source/assets + pyproject.toml + worker if present; not frontend dist/dependency/environment/data or full loaded closure.'})
observations={}
for path in ['/health','/openapi.json','/','/console','/v1/control-plane/model-status','/v1/control-plane/models','/v1/runtime/attestation']:
    record={'timestamp':now(),'method':'GET','url':'http://127.0.0.1:8000'+path,'request_body':None,'credentials_sent':False}
    try:
        try:response=urlopen(record['url'],timeout=8)
        except HTTPError as exc:response=exc
        with response:
            raw=response.read(1024*1024+1);record.update(status=response.status,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),request_id=response.headers.get('X-Request-ID'))
            if len(raw)>1024*1024:record['limitation']='BODY_LIMIT_REACHED'
            elif 'json' in response.headers.get('Content-Type',''):record['body']=json.loads(raw)
            else:
                text=raw.decode('utf-8',errors='replace');title=re.search(r'<title>(.*?)</title>',text,re.I|re.S)
                record.update(title=title.group(1) if title else None,compiled_assets_marker='/assets/index-' in text)
    except Exception as exc:record.update(status='NOT_VERIFIED',error=type(exc).__name__)
    observations[path]=record
write('RUNTIME_OBSERVATIONS.json',observations)
prior=[]
for rel in ['docs/reports/v1-functional-closure-20261009-101736/REGRESSION.json','docs/reports/v1-functional-closure-20261009-101736/RUNTIME_EVIDENCE.json','docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json','docs/reports/v1-rollback-investigation-20261009-105200/INVESTIGATION_REPORT.json']:
    p=ROOT/rel;prior.append({'path':str(p),'sha256':sha(p),'status':read(p).get('status'),'evidence_age':'HISTORICAL_NOT_REEXECUTED'})
write('HISTORICAL_EVIDENCE_REFERENCES.json',prior)
matrix=[
 {'id':'UI01','requirement':'Console/User routes reach intended V1 API','source':'router.tsx / UserChat and /console OperatorConsole; api.ts relative /v1 paths; main.py NORMAL static bundle routes; vite exact chat proxy','actual':'Current runtime old UI root and missing /console/model routes; see runtime observations','tests':'assistant.test.tsx HTTP mocks; historical controlled candidate/browser evidence','decision':'BLOCKED_RUNTIME_ALIGNMENT'},
 {'id':'UI02','requirement':'New Chat/session lifecycle','source':'assistant.tsx newChat rotates client UUID and clears in-memory UI, disabled pending; subsequent requests reuse UUID','actual':'Does not delete server memory or durable data; server accepts client session_id default web without authenticated principal binding','tests':'Existing New Chat and follow-up tests; not rerun','decision':'PARTIAL_CC05_REQUIRED'},
 {'id':'UI03','requirement':'Authenticated user ownership and session isolation','source':'ChatRequest session_id; chat(request:ChatRequest) no authenticated user dependency; GateIntegration memory keyed by supplied session_id','actual':'Server ownership validation not established; UUID generation is not authorization. No live cross-session exploitation/read attempted and no new leak claim','tests':'SessionMemory tests import app.memory.session_adapter, not V1 MemoryEngine; cannot close this gate','decision':'BLOCKED_APPROVED_IDENTITY_MEMORY_POLICY'},
 {'id':'UI04','requirement':'Loading/error/timeout/retry','source':'pending disables send/New Chat; errors preserve question; manual retry; runtimeFetch returns mapped HTTP errors; no bounded AbortSignal/deadline for chat/model API','actual':'Static gap: fetch that never settles keeps pending indefinitely. Backend stage timeout is not browser transport deadline. No reproducer/new tests executed','tests':'Unavailable503 question retention exists; hung fetch/cancel/manual-retry lifecycle acceptance missing','decision':'PARTIAL_SOURCE_CHANGE_REQUIRES_REVIEW'},
 {'id':'UI05','requirement':'Status and installed/selected/executed model distinction','source':'model-status uses Settings owner; inventory requires_admin then provider.list_models; selection CAS expected_revision, single NORMAL worker, real inventory validation','actual':'Runtime endpoints404. Status configured model is not execution readiness. Source distinguishes status/availability and last_request, model weights never attested','tests':'operator control auth/race/in-flight/conflict tests and frontend inventory mocks; historical only','decision':'BLOCKED_RUNTIME_AND_ACTUAL_VALIDATION'},
 {'id':'UI06','requirement':'History/privacy/consent/retention/delete','source':'UserChat messages only component state; explicit legacy-memory disclosure; MemoryEngine bounded deque process-local; no durable user history/prompts-memory lifecycle','actual':'CC05 open under temporary approved legacy preservation; consent/read-write ownership/retention/deletion contract not approved here; UI reset not persistence deletion','tests':'No proven V1 ownership/durable/prompt-memory acceptance suite','decision':'BLOCKED_POLICY_AND_UNIMPLEMENTED_REQUIREMENTS'},
 {'id':'UI07','requirement':'Public contract/privacy and request correlation','source':'PublicChatSchema strict and backend _project_v1_chat_response strict explicit fields; middleware X-Request-ID','actual':'Frontend chat transport does not return/expose response request-ID header; public body has no request_id. Current read-only GET header observations recorded. No live chat validation','tests':'Projection tests plus frontend rejects private fields; historical only','decision':'PARTIAL_PUBLIC_CHAT_CORRELATION_NOT_VERIFIED'},
 {'id':'UI08','requirement':'Actual Console→API→Hermes→Knowledge→provider acceptance','source':'sendUserChat -> POST/v1/chat -> settings.configuration_snapshot -> OllamaProvider -> HermesAgent.execute_v1 -> public projection','actual':'Static wiring and historical fixture candidate available; native semantic/production RAG and current runtime chat not verified','tests':'Historical257 backend/10 frontend/48 targeted passes; not new results; model receipt limited to single llama3.2:1b and fixture retrieval/semantic','decision':'BLOCKED_NATIVE_ACCEPTANCE_AUTHORIZATION'},
]
write('CONSOLE_USER_MATRIX.json',{'contract_id':contract_meta['contract_id'],'phase':1,'timestamp':now(),'status':'BLOCKED','matrix':matrix,'policy':'Observed current behavior, not approval of new memory/identity/filter/oracle policy. No new acceptance requirements invented outside contract.','required_new_tests':[{'case':'Hung fetch releases loading with bounded timeout and preserves question','status':'NOT_RUN_NOT_IMPLEMENTED','effect':'Future isolated mocked frontend test after reviewed patch'}, {'case':'Authenticated owner rejects reused/forged session IDs and separates user history','status':'BLOCKED_POLICY','effect':'Requires approved V1 identity/consent/session contract; no V2 adapter substitution'}, {'case':'Actual NORMAL Console/API/public chat/model selection route binding','status':'BLOCKED_RUNTIME_AUTHORIZATION','effect':'Would require controlled runtime and provider/memory/model mutation approvals'}, {'case':'Durable history/prompt memory/retention/deletion semantics','status':'BLOCKED_POLICY_AND_IMPLEMENTATION','effect':'No invented policy or persistence changes now'}]})
write('HERMES_CALL_GRAPH.json',{'contract_id':contract_meta['contract_id'],'phase':'0 inventory for phase3, no phase3 PASS','timestamp':now(),'source_path':['router.tsx UserChat -> assistant.tsx send -> api.ts sendUserChat -> POST /v1/chat','routes.chat -> Settings.configuration_snapshot -> OllamaProvider(snapshot)','routes.chat -> HermesAgent.execute_v1 with shared LanguageEngine, KnowledgeEngine, GateIntegration, TrustEngine, EvidenceGroundingGuard','Hermes execute_v1 -> provider.health_check -> language/run_sync -> ProblemEngine/classifier -> knowledge retrieval -> trust/gates -> deterministic/evidence/provider response branches -> grounding -> remember_response','provider branch -> system/user prompt -> OllamaProvider.generate -> Ollama HTTP client','routes.chat -> _project_v1_chat_response -> record_v1_execution -> public body'],'memory':'GateIntegration remembers user before answer policy; bounded MemoryEngine keyed by client session. execute_v1 passes context=None to language; generated user prompt builds user/intent/entities/problem/evidence, not validated prompt-memory recall.','diagram_mermaid':'flowchart LR\n U[UserChat] --> A[sendUserChat]\n A --> R[POST /v1/chat]\n R --> C[Settings snapshot]\n R --> H[Hermes execute_v1]\n H --> L[Language/Problem]\n H --> K[Knowledge retrieval]\n H --> T[Trust/Gates/Grounding]\n H --> P[Provider branch]\n H --> M[Legacy memory]\n H --> O[Public projection]','limits':'Static calls and historical scoped tests. No startup/provider execution or new assertion of native runtime call closure.'})
after={'timestamp':now(),'head':baseline.git('rev-parse','HEAD'),'git_status':baseline.git('status','--short'),'fingerprint':ns['source_build_id'](),'preservation':snapshot()}
b=before['preservation']['sha256'];a=after['preservation']['sha256']
changes={'modified':sorted(p for p in b.keys()&a.keys() if b[p]!=a[p]),'removed':sorted(b.keys()-a.keys()),'added':sorted(a.keys()-b.keys())}
write('CHANGE_AUDIT.json',{'timestamp':now(),'status':'PASS_SCOPED' if not any(changes.values()) and before['head']==after['head'] else 'REVIEW_REQUIRED','changes':changes,'before':before,'after':after,'scope':'Existing auditable source/tests/reports/cache/config/bundle hashed; new report excluded. Existing inaccessible temporary directories remain limits. No env values or live DB opened. Runtime may count read-only HTTP observations.'})
print(json.dumps({'source':after['fingerprint'],'modules':len(inventory),'source_routes':len(routes),'test_files':len(test_inventory),'parse_errors':parse_errors,'runtime_status':{p:r['status'] for p,r in observations.items()},'changes':changes}))
