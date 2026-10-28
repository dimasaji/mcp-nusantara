"""Read-only runtime alignment investigation; writes only new audit evidence."""
import ast
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PREVIOUS = ROOT/'docs/reports/v1-functional-closure-20261009-101736'
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
EXPECTED = 'sha256:9916a16a8411c1d892157fad11e3bfdf4200efe4e20a259ec23dd9de74b90fcd'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(name, value):
    with (OUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False)

def now():
    return datetime.now(timezone(timedelta(hours=7))).isoformat()

spec = importlib.util.spec_from_file_location('alignment_baseline', PREVIOUS/'prepare_baseline.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
baseline.OUT = OUT
from app.core.runtime_identity import source_build_id

def snapshot():
    data = baseline.snapshot()
    for relative in ['control-plane/tests','control-plane/e2e','control-plane/dist','control-plane/index.html','control-plane/README.md','.dockerignore']:
        base = ROOT/relative
        for path in [base] if base.is_file() else base.rglob('*'):
            if path.is_file() and not path.is_symlink():
                data['sha256'][path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return data

def get(path):
    url = 'http://127.0.0.1:8000' + path
    result = {'timestamp':now(),'method':'GET','url':url,'provider_invoked':False,'request_body':None}
    try:
        try:
            response=urlopen(url,timeout=8)
        except HTTPError as error:
            response=error
        with response:
            raw=response.read(512*1024+1)
            result.update(status=response.status,headers=dict(response.headers),sha256=hashlib.sha256(raw).hexdigest(),bytes_observed=len(raw))
            if len(raw)>512*1024:
                result['limit']='BODY_LIMIT_REACHED'; return result
            if 'json' in response.headers.get('Content-Type',''):
                result['body']=json.loads(raw)
            else:
                text=raw.decode('utf-8',errors='replace')
                title=re.search(r'<title>(.*?)</title>',text,re.I|re.S)
                result['html_title']=title.group(1) if title else None
                result['contains_new_chat']='New Chat' in text
                result['contains_built_control_plane_assets']='/assets/index-' in text
    except Exception as error:
        result.update(status='NOT_VERIFIED',error_type=type(error).__name__,reason=str(error))
    return result

if sys.argv[1]=='inspect':
    names=['BASELINE.json','CAPABILITY_MATRIX.json','IMPLEMENTATION_REPORT.json','REGRESSION.json','RUNTIME_EVIDENCE.json','CHANGE_AUDIT.json','REMAINING_GATES.json']
    artifacts={name:read((PREVIOUS/name).resolve(strict=True)) for name in names}
    write('EVIDENCE_INPUTS.json',{'timestamp':now(),'files':{name:{'path':str((PREVIOUS/name).resolve()),'sha256':hashlib.sha256((PREVIOUS/name).read_bytes()).hexdigest(),'status':value.get('status')} for name,value in artifacts.items()},
        'baseline':{k:artifacts['BASELINE.json'].get(k) for k in ['timestamp','branch','head','approved_decisions']},
        'candidate_fingerprint':artifacts['RUNTIME_EVIDENCE.json']['source_fingerprint'],
        'candidate_pid':artifacts['RUNTIME_EVIDENCE.json']['candidate']['socket_pid'],
        'candidate_limitations':artifacts['RUNTIME_EVIDENCE.json']['limitations'],
        'historical_tests':{'backend':artifacts['REGRESSION.json']['backend_regression'],'frontend':artifacts['REGRESSION.json']['frontend']}})
    before={'timestamp':now(),'branch':baseline.git('branch','--show-current'),'head':baseline.git('rev-parse','HEAD'),
            'git_status':baseline.git('status','--short'),'source_fingerprint':source_build_id(),'snapshot':snapshot()}
    write('BASELINE.json',before)
    endpoints=['/health','/openapi.json','/v1/control-plane/model-status','/v1/control-plane/models','/v1/runtime/attestation','/','/console']
    responses={path:get(path) for path in endpoints}
    write('HTTP_OBSERVATIONS.json',responses)
    oracle=read(ROOT/'app/evaluation/datasets/v1_recovery_oracle.json')
    cases=oracle['cases'] if isinstance(oracle,dict) else oracle
    unresolved=[{key:case.get(key) for key in ['id','oracle_status','source','source_authority','service_region','effective_date','effective_date_status','metadata_review_status','authoritative_status']} for case in cases if case.get('oracle_status') in ['REVIEW_REQUIRED','MISSING']]
    metadata_tree=ast.parse((ROOT/'app/knowledge/schemas.py').read_text(encoding='utf-8-sig'))
    metadata_class=next(node for node in metadata_tree.body if isinstance(node,ast.ClassDef) and node.name=='DocumentMetadata')
    metadata_fields=[node.target.id for node in metadata_class.body if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name)]
    write('UNRESOLVED_REQUIREMENTS.json',{'timestamp':now(),'filter':{'status':'BLOCKED_DECISION','current_behavior':'Nonempty filter rejected before retrieval; empty/default query preserved','metadata_fields':metadata_fields,
        'missing_decisions':['Supported filter keys/operators/types and combination semantics','Authority and jurisdiction vocabulary with trust/approval source','Validity/version/conflict rules and missing-metadata fail-closed behavior','Enforcement before ranking/top-k and test oracles'],
        'implementation_defect':'No new confirmed filter implementation defect; approved nonempty filter grammar is absent'},
        'oracle':{'status':'BLOCKED_DATA_AND_AUTHORIZATION','case_counts':dict(Counter(case.get('oracle_status') for case in cases)),'unresolved_cases':unresolved,
            'required_evidence':['Approved issuer and jurisdiction','Source snapshot and content hash with provenance','Valid-from/valid-to evidence, not inferred publication date','Ingest authorization and approved expected answers/required evidence'],
            'implementation_defect':'Missing or unapproved authority/oracle data is not repaired by fabricating source requirements'},
        'memory':{'durable_personal_history':'NOT_IMPLEMENTED','prompt_memory_integration':'NOT_IMPLEMENTED','current_owner':'Existing MemoryEngine process-local bounded deque, client session_id',
            'implemented':'Legacy user/assistant capture plus transient client turn history/New Chat; no server deletion by New Chat',
            'blocked_decisions':['Consent and authenticated ownership of sessions','Read/write authority and sensitive-content policy','Retention/deletion and rejected-answer capture','Which contextual turns may be used in prompts and what remains evidence-only'],
            'no_changes':'Legacy preservation disposition retained; no new memory persistence or prompt injection'},
        'missing_security_evidence':['Current-source native Windows symlink/path boundary execution with required privileges','Operational enforcement of approval/policy before sensitive side effects','Current user/session isolation and memory authorization contract', 'Operational auth/local-origin configuration on intended target'],
        'missing_deployment_evidence':['Native full semantic-worker/RAG/store integration from final source; candidate used explicit fixtures','Target dependency/model/embedding availability and verified configuration provenance','Single-worker launch topology and cross-process consistency constraints','Startup/load/resource limits, graceful shutdown and restart verification','Immutable rollback artifact for old user runtime; current working tree cannot reconstruct old loaded build','Controlled deployment target and operational credentials; no deployment performed']})
    paths=responses['/openapi.json'].get('body',{}).get('paths',{})
    print(json.dumps({'current_source':before['source_fingerprint'],'expected_match':before['source_fingerprint']==EXPECTED,
        'responses':{path:value['status'] for path,value in responses.items()},'model_paths_in_openapi':[p for p in paths if '/model' in p]}))
elif sys.argv[1]=='finish':
    before=read(OUT/'BASELINE.json'); after=snapshot(); original=before['snapshot']['sha256']; current=after['sha256']
    changes={'modified':[p for p in original if p in current and original[p]!=current[p]],'removed':[p for p in original if p not in current],'added':[p for p in current if p not in original],'errors':after['errors']}
    write('CHANGE_AUDIT.json',{'timestamp':now(),'status':'PASS' if not any(changes.values()) else 'REVIEW_REQUIRED','changes':changes,
        'head_before':before['head'],'head_after':baseline.git('rev-parse','HEAD'),'git_before':before['git_status'],'git_after':baseline.git('status','--short'),
        'limits':'New report directory excluded; historical reports, source, tests, contracts, cache and frontend bundle hash-protected. Runtime memory observability counters may record read-only HTTP requests.'})
    responses=read(OUT/'HTTP_OBSERVATIONS.json'); inputs=read(OUT/'EVIDENCE_INPUTS.json')
    process_before=read(OUT/'PROCESS_BEFORE.json'); process_after=read(OUT/'PROCESS_AFTER.json')
    health=responses['/health'].get('body',{})
    attestation=responses['/v1/runtime/attestation'].get('body',{}).get('attestation',{})
    runtime_hash=attestation.get('build',{}).get('source_build_hash') or health.get('build_id')
    runtime_routes=responses['/openapi.json'].get('body',{}).get('paths',{})
    required_routes={'/v1/control-plane/model-status':'get','/v1/control-plane/models':'get','/v1/control-plane/model-selection':'post'}
    route_presence={path:method in runtime_routes.get(path,{}) for path,method in required_routes.items()}
    unchanged=process_before['process']==process_after['process'] and process_before['socket']['OwningProcess']==process_after['socket']['OwningProcess']
    launch="Set-Location -LiteralPath 'C:\\Users\\dmaza\\mcp-starter'\n& 'C:\\Users\\dmaza\\mcp-starter\\.venv\\Scripts\\python.exe' -B -m uvicorn app.main:app --app-dir 'C:\\Users\\dmaza\\mcp-starter' --host 127.0.0.1 --port 8000 --workers 1"
    plan={'timestamp':now(),'status':'BLOCKED_PENDING_AUTHORIZATION_AND_ROLLBACK_PREFLIGHT',
        'exact_404_cause':'Running application does not register the model-control paths: direct GET returns404 and OpenAPI omits all three. Source has existing matching prefixes; candidate registered them. Different import-source fingerprint and pre-implementation process start corroborate stale in-memory application registration.',
        'source_changes_required':'None established for this routing mismatch; do not add duplicate routes or change frontend URLs',
        'configuration_changes_required':'None established; intended bootstrap must be reviewed through existing configuration owner. Inherited process environment is not observable from this audit and cannot be assumed identical to a new shell.',
        'restart_necessary':True,'restart_reason':'Existing launch has no --reload; Python imports/FastAPI router table remain in memory. Replacing this application process is required to consume current source; no hot patch or forced reconfiguration is proposed.',
        'authorization':'Explicit approval required for controlled shutdown/replacement of identified port8000 process. This audit issues no signal and performs no startup.',
        'preconditions':['Source fingerprint remains '+EXPECTED,'Verify final frontend index/assets hashes against previous runtime evidence',
            'Prepare an immutable, runnable rollback artifact with known dependencies/configuration; old b7455 fingerprint is not recoverable from health metadata or Git HEAD alone',
            'Review native NORMAL bootstrap configuration and worker/embedding/model resources; candidate used semantic/retrieval fixtures',
            'Review existing knowledge-store startup initialization side effects; no DB migration/delete/ingest authorized',
            'Arrange a brief interruption; drain in-flight requests and use original foreground console/service owner for graceful stop after approval',
            'Verify port8000 is free; do not launch competing process or kill a stale remembered PID'],
        'operator_shutdown':'After explicit approval and identity recheck, operator uses Ctrl+C in the original foreground server console. If service-managed or unavailable, obtain its verified owner-controlled shutdown procedure; do not use blanket Stop-Process.',
        'proposed_launch_command':launch,'launch_command_executed':False,
        'expected_impact':['Brief chat/Console unavailability while replacing process','In-flight requests must finish or be handled before stop','Process-local legacy conversation memory may be lost on restart; no deletion/migration command proposed','Volatile operator model revision resets to bootstrap; single-process selection contract unchanged','NORMAL startup initializes existing native dependencies; successful bootstrap and native chat are not established by fixture candidate'],
        'verification_after_approval':['Socket PID/start/command line and source import fingerprint must be newly captured','GET /health and real port8000 attestation using legitimate loopback boundary; verify limited loaded-code binding without full-closure claim',
            'OpenAPI contains three required model-control methods; GET model-status succeeds; unauthenticated /models rejects and operator-authenticated inventory succeeds',
            'New UI root and New Chat render expected compiled bundle','Only if separately approved for memory/provider effects, send controlled greeting and substantive request, correlate native provider receipt and public response',
            'Keep HOLD if native semantic/RAG/security/oracle/memory gates remain open'],
        'rollback':['Do not stop current runtime until a verified immutable rollback artifact and launch configuration are available','If replacement fails, operator gracefully stops only the newly created replacement','Launch the verified prior artifact from its separate preserved directory with its recorded interpreter/configuration on free port8000','Check socket ownership, health/source identity, routes and required behavior against rollback baseline','Never reset/clean/checkout/discard the current working tree; restarting current checkout is not an exact rollback to old loaded source'],
        'rollback_command':'BLOCKED: no verified path/artifact for prior loaded build is available; do not invent a runnable rollback command'}
    write('ALIGNMENT_PLAN.json',plan)
    report={'timestamp':now(),'status':'BLOCKED','runtime_aligned':False,'repository':str(ROOT),'head':before['head'],
        'candidate_source_fingerprint':inputs['candidate_fingerprint'],'disk_source_fingerprint':source_build_id(),'expected_candidate':EXPECTED,
        'candidate_matches_disk':inputs['candidate_fingerprint']==source_build_id()==EXPECTED,
        'user_runtime_source_fingerprint':runtime_hash,'runtime_matches_candidate':runtime_hash==EXPECTED,
        'user_process':process_before,'process_unchanged_after_read_only_audit':unchanged,'routes_registered':route_presence,
        'route_responses':{path:responses[path] for path in ['/v1/control-plane/model-status','/v1/control-plane/models']},
        'user_ui_responses':{path:responses[path] for path in ['/','/console']},
        'loaded_application_evidence':attestation,'loaded_source_limit':'Health/attestation source hash is import-time disk snapshot. Loaded manifest covers registered handler/dispatch/identity code only, not globals, closures, assets, transitive dependencies or model weights.',
        'source_runtime_differences':['Expected current model-control registrations absent in running process','Current source supports Hermes greeting and new React UI; no live chat was sent to old process to assert its execution behavior','Exact old file-by-file source diff cannot be reconstructed from aggregate fingerprint or nontransitive loaded manifest'],
        'independent_v1_review':read(OUT/'UNRESOLVED_REQUIREMENTS.json'),
        'plan':'ALIGNMENT_PLAN.json','source_change_audit':changes,'prior_tests_reused':inputs['historical_tests'],
        'tests_this_turn':'No chat/provider/selection requests, no candidate start and no test rerun: source unchanged and prior exact-fingerprint scoped tests reused',
        'commands_executed':['Read seven exact latest-run JSON artifacts and supporting current source/contracts/oracle data',
            'Get-NetTCPConnection -LocalPort 8000 -State Listen; Get-CimInstance Win32_Process using observed socket PID and parent PID (before/after)',
            '.venv/Scripts/python.exe -B docs/reports/v1-runtime-alignment-20261009-103149/audit.py inspect',
            'Read-only GET '+', GET '.join('http://127.0.0.1:8000'+path for path in responses),
            baseline.GIT+' --no-optional-locks branch --show-current / rev-parse HEAD / status --short',
            '.venv/Scripts/python.exe -B docs/reports/v1-runtime-alignment-20261009-103149/audit.py finish'],
        'next_action':'Review ALIGNMENT_PLAN and supply explicit process replacement authorization only after rollback/native-bootstrap preconditions are satisfied',
        'v1_acceptance':'HOLD','v2':'DEFERRED','limitations':['No restart/deploy/commit/push/migration or source/configuration/test changes','Full runtime alignment and native semantic/RAG execution remain unverified','HTTP inspection updates normal observability counters; no persistence/provider/model actions invoked']}
    write('RUNTIME_ALIGNMENT_REPORT.json',report)
    print(json.dumps({'status':report['status'],'disk':report['disk_source_fingerprint'],'runtime':runtime_hash,'candidate_matches_disk':report['candidate_matches_disk'],
        'route_presence':route_presence,'attestation_http_status':responses['/v1/runtime/attestation']['status'],'unchanged':unchanged,'source_changes':changes,'report':str(OUT/'RUNTIME_ALIGNMENT_REPORT.json')}))
