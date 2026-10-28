"""Consolidate already captured read-only evidence; exclusive new report write."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
before=read(OUT/'BASELINE.json')
audit=read(OUT/'CHANGE_AUDIT.json')
http=read(OUT/'HTTP_OBSERVATIONS.json')
artifacts=read(OUT/'ARTIFACT_INSPECTION.json')
boot=read(OUT/'BOOTSTRAP_INSPECTION.json')
p1=read(OUT/'PROCESS_BEFORE.json'); p2=read(OUT/'PROCESS_AFTER.json')
historical=read(ROOT/'docs/reports/v1-functional-closure-20261009-101736/RUNTIME_EVIDENCE.json')
plan=read(ROOT/'docs/reports/v1-runtime-alignment-20261009-103149/ALIGNMENT_PLAN.json')
def find_bundle(obj):
    if isinstance(obj,dict):
        if 'control-plane/dist/index.html' in obj: return obj
        for value in obj.values():
            found=find_bundle(value)
            if found: return found
    return None
old_bundle=find_bundle(historical)
bundle_match=bool(old_bundle) and all(boot['frontend_hashes'].get(k)==v for k,v in old_bundle.items())
attestation=http['/v1/runtime/attestation'].get('body',{}).get('attestation',{})
build=attestation.get('build',{})
paths=http['/openapi.json'].get('body',{}).get('paths',{})
model_paths=['/v1/control-plane/model-status','/v1/control-plane/models','/v1/control-plane/model-selection']
runtime_stable=p1['process']==p2['process'] and p1['listeners']==p2['listeners']
report={
 'timestamp':datetime.now(timezone(timedelta(hours=7))).isoformat(),
 'status':'BLOCKED_PREREQUISITES', 'v1_acceptance':'HOLD', 'v2':'DEFERRED',
 'scope':'Read-only alignment/rollback prerequisites. Only new evidence files written; no source/config/env/data edits, artifact restoration, application startup, process signalling, graph queries, provider generation, new tests or deployment.',
 'repository':{'path':str(ROOT),'head':before['head']['stdout'].strip(),'candidate_and_disk_fingerprint':before['source_fingerprint'],'source_fingerprint_scope':'Existing source_build_id hashes executable app source/assets plus pyproject.toml and worker if present. Excludes frontend dist, dependencies, environment and data. Not full loaded execution closure.','historical_candidate_fingerprint':historical['source_fingerprint'],'frontend_matches_historical_recorded_bundle':bundle_match},
 'runtime':{'before':p1,'after':p2,'process_and_listener_unchanged':runtime_stable,'attestation_source_snapshot':build.get('source_build_hash'),'loaded_code_hash':build.get('loaded_code_hash'),'registered_binding':build.get('loaded_code_binding'),'full_application_build_verified':build.get('full_application_build_verified'),'identity_limitation':build.get('limitations'),'http_statuses':{k:v['status'] for k,v in http.items()},'model_routes_present_in_openapi':{k:k in paths for k in model_paths},'alignment':'NOT_ALIGNED: active route table lacks model-control paths, matching direct 404. Runtime import-source snapshot differs from final disk/candidate. Existing non-reloading process remains unchanged. No code/config correction established for this discrepancy.'},
 'rollback':{'ready':False,'finding':'Two existing staging archives have valid SHA256 sidecars and historical health-only PASS. Their existing restored source fingerprints are 31ba51f6... and 49431c39..., neither the runtime b7455... snapshot. Archive coverage omits worker, built frontend and exact dependency closure. Thus they are historical staging artifacts, not verified executable rollback for PID33160.','evidence':'ARTIFACT_INSPECTION.json','artifacts':[{k:x[k] for k in ['archive','sha256','checksum_match','existing_restored_root','existing_restored_fingerprint','current_runtime_rollback_ready']} for x in artifacts['archives']],'dependency_limit':'Current available .venv Python3.13.15 is not a frozen prior-build dependency artifact. Historical recovery environment reports Python3.12.14 and selected package versions; no complete pinned closure in inspected staging archives. pyproject minimum ranges cannot recreate exact prior dependencies.','run_method':'Historical staging script launch is documented in ARTIFACT_INSPECTION.json, but no current artifact execution performed. Fault-injected release-source must not be treated as rollback. No fragments assembled.','exact_current_runtime_rollback_command':None,'reason_no_command':'No verified old artifact/configuration/interpreter identity; do not infer from aggregate fingerprint or use current checkout as old build.'},
 'prerequisites_met':[
  {'item':'Expected HEAD and disk/candidate source fingerprint','result':before['head']['stdout'].strip()=='8f86bed38aca8e6b5a0bd365f3351ac9c0825eab' and before['source_fingerprint']==historical['source_fingerprint'],'evidence':'BASELINE.json'},
  {'item':'Recorded frontend bundle hashes still match','result':bundle_match,'evidence':'BOOTSTRAP_INSPECTION.json; historical RUNTIME_EVIDENCE.json'},
  {'item':'Existing interpreter and native-worker files available','result':all(boot['resources'][k]['exists'] for k in ['.venv/Scripts/python.exe','nusantara-models/indobert_worker.py','nusantara-models/.venv/Scripts/python.exe']),'limit':'Availability only, not runnable native readiness'},
  {'item':'Launch syntax, application entrypoint, loopback port and single worker determinable','result':True,'evidence':'ALIGNMENT_PLAN.json; current process command; app/main.py'},
  {'item':'Health helper behavior determinable','result':True,'evidence':'scripts/healthcheck.py: GET /health, timeout3s'},
  {'item':'Existing staging archive checksum integrity','result':all(x['checksum_match'] for x in artifacts['archives']),'limit':'Not proof of current-runtime rollback'},
  {'item':'No pre-existing scoped file content changed and PID33160 remains','result':audit['status']=='PASS' and runtime_stable,'evidence':'CHANGE_AUDIT.json; PROCESS_BEFORE/AFTER.json'}
 ],
 'prerequisites_open':[
  'Immutable complete runnable rollback tied to intended prior build, with verified interpreter/dependency closure, configuration provenance, run command and restoration/validation evidence.',
  'Effective inherited PID33160 environment and future operator shell configuration equivalence. Repository .env absent; existing defaults and ENV/explicit layers do not prove prior configuration. Do not invent a new config owner or silently pass rag_runtime.json.',
  'Normal native startup readiness: worker, model/tokenizer cache, provider availability and production RAG. Existing worker/interpreter file presence and fixture-candidate historical PASS are insufficient.',
  'Approved handling of native KnowledgeStore startup side effects: directory creation, SQLite WAL and CREATE TABLE/INDEX. Normal boot cannot be assumed read-only under current no-data-change boundary.',
  'Verified original-console/service owner procedure, request drain, outage window and explicit controlled process-replacement approval.',
  'Port8000 availability must be checked only after an approved old-process shutdown; it is currently correctly occupied by33160.',
  'Approval for validation that generates actual provider responses and writes conversation memory; approval for model-selection mutation and rollback drill if required.'
 ],
 'bootstrap_certainty':{'syntax':'DETERMINABLE','effective_configuration':'NOT_FULLY_DETERMINABLE_FROM_CAPTURED_FILES','native_boot_success':'NOT_VERIFIED','health_check':'DETERMINABLE_BUT_SHALLOW','candidate_command_proposed_not_executed':plan['proposed_launch_command'],'read_only_health_command':boot['health_command'],'notes':'Command is a conditional operator proposal, not authorization or proven native boot. No application imported/launched in this audit.'},
 'replacement_risks':plan['expected_impact']+['Unverified exact rollback may prevent recovery to prior behavior.','New shell may consume a different inherited environment; current .env is absent.','Startup can create/modify knowledge DB schema/WAL even before a chat request.','Current runtime source snapshot does not attest dependency/asset/global/closure identity.'],
 'post_replacement_validation_procedure':[
  {'step':1,'action':'Before any change, satisfy open rollback/config/resource/data-side-effect prerequisites and obtain explicit operator replacement approval; retain source hashes, PID/start/listener, configuration provenance without exposing credentials, and old artifact manifest. Arrange drain/outage window.','execution':'NOT_PERFORMED'},
  {'step':2,'action':'Operator rechecks PID/start/command/listener, gracefully stops the verified original console/service by its owner-approved method, then confirms port8000 free. Never act on a stale remembered PID or launch a competing server.','execution':'REQUIRES_APPROVAL'},
  {'step':3,'action':'Use the reviewed bootstrap command only after exact environment and database side-effect approval; retain stdout/stderr/traceback in a fresh evidence directory. Capture new PID/start/command/cwd/interpreter and socket owner.','execution':'REQUIRES_APPROVAL'},
  {'step':4,'action':'GET /health and /v1/runtime/attestation through real loopback port8000. Require healthy response, expected final source snapshot9916..., new matching process identity and registered-code binding. Preserve non-transitive attestation limitations; no full build/model-weight claim.','execution':'PLANNED'},
  {'step':5,'action':'GET /openapi.json: verify POST /v1/chat, GET /v1/health, GET /v1/control-plane/model-status, GET /v1/control-plane/models, POST /v1/control-plane/model-selection. Inspect /console and compiled asset HTTP separately because static routes may be absent from OpenAPI. Preserve status/body/fingerprints.','execution':'PLANNED'},
  {'step':6,'action':'Verify Console root and /console render expected compiled index/JS, New Chat client state and model-status. Unauthenticated models access must follow existing rejection contract; operator-authenticated inventory/status must succeed using legitimate existing credentials without writing them to evidence.','execution':'PLANNED'},
  {'step':7,'action':'With explicit mutation approval only, validate model-selection revision/conflict handling and chat consumption of selected installed model. Inventory has only one historically observed real model; do not claim two-real-model switching. Record final operator selection impact.','execution':'REQUIRES_APPROVAL'},
  {'step':8,'action':'With explicit provider/memory-write approval only, POST controlled greeting and substantive /v1/chat requests. Validate existing public response contract/request IDs, human answer, grounding/trust behavior, provider receipt correlated to process/source/config/model and native semantic/RAG provenance. Fixture retrieval cannot close production RAG; provider model name cannot attest loaded weights. Record errors and traceback without removing prior evidence.','execution':'REQUIRES_APPROVAL'},
  {'step':9,'action':'On failed approved replacement, operator stops only its verified new process and runs the verified previous artifact using its recorded interpreter/configuration on the free approved port. Compare health, process/build, routes and required behavior to prior baseline. No exact rollback command is available now; do not authorize replacement while this gate is open. Database restore is a separate data-change authorization, never implicit.','execution':'BLOCKED_ARTIFACT_AND_APPROVAL'},
  {'step':10,'action':'Keep V1 HOLD while CC05, CC06, native RAG, security and deployment gates remain open. Successful alignment closes only the specified runtime mismatch, not V1 acceptance.','execution':'MANDATORY'}
 ],
 'remaining_v1_gates':read(ROOT/'docs/reports/v1-functional-closure-20261009-101736/REMAINING_GATES.json')['gates']+['Durable conversation persistence and prompt-memory integration remain unimplemented requirements; no memory policy/official oracle decisions created here.'],
 'actions_requiring_explicit_approval':['Create/freeze/restore and execute any new rollback artifact or drill; current request only inspects existing artifacts.','Native candidate startup if it writes knowledge/data, or modifies configuration/resources.','Stop/restart/replace the verified user process and perform any resulting deployment operation.','POST /v1/chat provider generation/memory capture, POST model-selection, or restore/alter persistence.'],
 'new_tests':'NONE. All historical tests remain historical; current GET observations and checksum inspections are newly timestamped read-only observations.',
 'evidence_references':['EVIDENCE_REFERENCES.json','BASELINE.json','ARTIFACT_INSPECTION.json','BOOTSTRAP_INSPECTION.json','HTTP_OBSERVATIONS.json','PROCESS_BEFORE.json','PROCESS_AFTER.json','CHANGE_AUDIT.json','inspect_readonly.py'],
 'commands_executed':[
  "Get-Content -LiteralPath 'docs/reports/v1-runtime-alignment-20261009-103149/ALIGNMENT_PLAN.json'",
  "Get-Content -LiteralPath 'audit_reports/staging-drill-20261006T025037193681Z/result.json'",
  "Get-Content -LiteralPath 'audit_reports/staging-drill-20261006T025945053115Z/result.json'",
  "Get-Content -LiteralPath 'scripts/healthcheck.py'",
  "Get-Content -LiteralPath 'app/core/config.py' -TotalCount 100",
  "Get-Content -LiteralPath 'app/core/runtime_identity.py' -TotalCount 70",
  "Get-Content -LiteralPath 'app/core/nusantara_config.py' | Select-Object -Skip 330 -First 65",
  "Get-CimInstance Win32_Process -Filter 'ProcessId=33160'",
  "Get-NetTCPConnection -LocalPort 8000 -State Listen",
  "& 'C:\\Users\\dmaza\\mcp-starter\\.venv\\Scripts\\python.exe' -B 'docs/reports/v1-alignment-prerequisites-20261009-104217/inspect_readonly.py'",
  "& 'C:\\Users\\dmaza\\mcp-starter\\.venv\\Scripts\\python.exe' -B 'docs/reports/v1-alignment-prerequisites-20261009-104217/finalize_report.py'",
  'Inspector subprocess commands: git.exe --no-optional-locks rev-parse HEAD; status --short (before/after); worktree list --porcelain. Exact read/hash/HTTP operations retained in inspect_readonly.py.'
 ],
 'limitations':['Known local repository artifacts inspected, not exhaustive external backup search.','Git retains pre-existing inaccessible temporary-directory warnings; preservation proof covers successfully hashed files, not all machine filesystem.','No source/build reconstructed from aggregate hash. No archive extracted, restored or run.','No provider generation or native readiness test performed. No full process environment or live database contents captured.'],
 'next_recommended_action':'Supply or identify a verifiable complete prior-build rollback artifact and approve its bounded verification separately; resolve configuration/native startup/data-effect prerequisites before requesting controlled process replacement. Stop here.'
}
with (OUT/'PREREQUISITE_ROLLBACK_REPORT.json').open('x',encoding='utf-8') as stream:
    json.dump(report,stream,ensure_ascii=False,indent=2)
print(json.dumps({'status':report['status'],'runtime_unchanged':runtime_stable,'frontend_hash_match':bundle_match,'preservation':audit['status'],'report':str(OUT/'PREREQUISITE_ROLLBACK_REPORT.json')}))
