"""Evidence-only reads; never imports application, extracts archives or opens SQLite."""
import ast
import hashlib
import importlib.util
import json
import os
import re
import sys
import tarfile
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
PRIOR=ROOT/'docs/reports/v1-alignment-prerequisites-20261009-104217'
EXPECTED='sha256:9916a16a8411c1d892157fad11e3bfdf4200efe4e20a259ec23dd9de74b90fcd'
OLD_ID='sha256:b7455ef0823df00d73a576147c6331ed69f9b74c145de39281819c3cad78d27f'
errors=[]
def now():return datetime.now(timezone(timedelta(hours=7))).isoformat()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def write(name,data):
    with (OUT/name).open('x',encoding='utf-8') as stream:json.dump(data,stream,indent=2,ensure_ascii=False)
def secret_file(p):
    name=p.name.lower()
    return name=='.env' or name.startswith('.env.') and name!='.env.example' or any(s in name for s in ['secret','credential','cookie','token','password']) or p.suffix.lower() in ['.pem','.key']
def files(base):
    if not base.exists():return []
    result=[]
    for directory,dirs,names in os.walk(base,followlinks=False,onerror=lambda e:errors.append({'path':e.filename,'error':type(e).__name__})):
        dirs[:]=[d for d in dirs if d not in ['.git','.venv','node_modules','__pycache__','.pytest_cache'] and not (Path(directory)/d).is_symlink()]
        for name in names:
            p=Path(directory)/name
            if not p.is_symlink():result.append(p)
    return result
def meta(p,hash_content=True):
    try:
        s=p.stat()
        return {'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(p) if hash_content and not secret_file(p) else None,'content_recorded':False}
    except OSError as exc:
        errors.append({'path':str(p),'error':type(exc).__name__});return {'path':str(p),'unavailable':True}
# Preserve existing audited source/report/cache files; no application import.
spec=importlib.util.spec_from_file_location('baseline',ROOT/'docs/reports/v1-functional-closure-20261009-101736/prepare_baseline.py')
baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline);baseline.OUT=OUT
tree=ast.parse((ROOT/'app/core/runtime_identity.py').read_text(encoding='utf-8'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='source_build_id')
ns={'ROOT':ROOT,'Path':Path,'hashlib':hashlib}
exec(compile(ast.Module(body=[fn],type_ignores=[]),'<existing-pure-fingerprint-function>','exec'),ns)
fp=ns['source_build_id']
local_roots=['backup','archive','app_backup_before_openrouter','backup_indobert_20261001_091633','legacy_v1_artifacts','.developer_staging','.dev','audit_reports','service','config','control-plane/dist']
def preservation():
    state=baseline.snapshot()
    for rel in local_roots:
        for p in files(ROOT/rel):
            if secret_file(p) or p.suffix.lower() in ['.db','.sqlite','.sqlite3'] or p.name.endswith(('-wal','-shm')):continue
            try:state['sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
            except OSError as exc:state['errors'].append({'path':str(p),'error':type(exc).__name__})
    return state
before={'timestamp':now(),'head':baseline.git('rev-parse','HEAD'),'git_status':baseline.git('status','--short'),'fingerprint':fp(),'preservation':preservation()}
write('BASELINE.json',before)
if before['fingerprint']!=EXPECTED or before['head']['stdout'].strip()!='8f86bed38aca8e6b5a0bd365f3351ac9c0825eab':
    write('INVESTIGATION_REPORT.json',{'timestamp':now(),'status':'BLOCKED_BASELINE_CHANGED','v1_acceptance':'HOLD','v2':'DEFERRED','baseline':before['fingerprint'],'stop':True});sys.exit(0)
inventory=[]
for rel in local_roots:
    inventory.extend(meta(p) for p in files(ROOT/rel) if p.suffix.lower() not in ['.db','.sqlite','.sqlite3'] and not p.name.endswith(('-wal','-shm')))
external=Path('E:/AI/mcp-starter')
external_files=files(external)
external_record={'root':str(external),'exists':external.exists(),'fingerprint':fp(external) if (external/'app').is_dir() else None,'matches_old_runtime':False,'files':[meta(p) for p in external_files if not p.is_relative_to(external/'data')],'runtime_claim':'Existing relocated source and mutable .venv; no build provenance ties this location to PID33160. Not executed.'}
external_record['matches_old_runtime']=external_record['fingerprint']==OLD_ID
write('LOCAL_BACKUP_INVENTORY.json',{'timestamp':now(),'files':inventory,'external_project':external_record,'search_limits':'Repository backup/archive/staging/audit/checkpoint locations and E:/AI/mcp-starter; top-level Nusantara names checked in Desktop/Documents/Downloads/OneDrive. No whole-disk/private-folder crawl.','errors':errors})
archive_paths=[]
for p in files(ROOT):
    if p.is_relative_to(OUT) or p.is_relative_to(ROOT/'data') or p.is_relative_to(ROOT/'nusantara-models'):continue
    if p.name.lower().endswith(('.tar.gz','.tgz','.zip','.whl')):archive_paths.append(p)
for p in external_files:
    if p.name.lower().endswith(('.tar.gz','.tgz','.zip','.whl')):archive_paths.append(p)
# Only explicitly relevant top-level archives outside the project.
for name in ['Downloads','Desktop','Documents','OneDrive']:
    base=ROOT.parent/name
    try:
        for p in base.iterdir():
            if p.is_file() and re.search(r'nusantara|mcp-starter',p.name,re.I) and p.name.lower().endswith(('.tar.gz','.tgz','.zip')):archive_paths.append(p)
    except OSError as exc:errors.append({'path':str(base),'error':type(exc).__name__})
archives=[]
for p in sorted(set(archive_paths)):
    item=meta(p);side=p.with_name(p.name+'.sha256')
    item['sidecar']=meta(side) if side.is_file() else None
    expected=None
    if side.is_file():
        match=re.match(r'^([0-9a-fA-F]{64})(?:\s|$)',side.read_text(encoding='ascii',errors='replace').strip())
        expected=match.group(1).lower() if match else None
    item['checksum_status']='VALID' if expected==item.get('sha256') else ('MISMATCH_OR_INVALID_SIDECAR' if side.is_file() else 'NO_INDEPENDENT_SIDECAR')
    try:
        if zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z:members=[{'name':m.filename,'bytes':m.file_size} for m in z.infolist()]
        else:
            with tarfile.open(p,'r:*') as t:members=[{'name':m.name,'bytes':m.size,'type':m.type.decode('ascii',errors='replace')} for m in t.getmembers()]
        item['members']=members
        names=[m['name'] for m in members]
        item['coverage']={'worker':any(n.endswith('/indobert_worker.py') for n in names),'frontend_dist':any('/control-plane/dist/' in n for n in names),'interpreter':any(n.endswith('/python.exe') for n in names),'lock_or_freeze':[n for n in names if re.search(r'(uv\.lock|poetry\.lock|Pipfile\.lock|requirements[^/]*|freeze|manifest)',n,re.I)],'data_members':[m for m in members if re.search(r'(/data/|\.db$|\.db-wal$|\.db-shm$)',m['name'])]}
        item['dependency_complete']='NOT_ESTABLISHED';item['current_runtime_rollback']='NOT_VERIFIED';item['extracted_or_executed']=False
    except (OSError,tarfile.TarError,zipfile.BadZipFile) as exc:item['inspection_error']=type(exc).__name__
    archives.append(item)
write('ARCHIVE_CLASSIFICATION.json',{'timestamp':now(),'archives':archives,'historical_recovery':read(PRIOR/'ARTIFACT_INSPECTION.json'),'categories':'Computed hash is not independent expected checksum; valid checksum is not recovered-source proof; historical health is not full build closure; source identity alone is not rollback proof.','errors':errors})
deps=[]
for root in [ROOT,external,ROOT/'nusantara-models']:
    venv=root/'.venv';cfg=venv/'pyvenv.cfg'
    interpreter=venv/'Scripts/python.exe'
    packages=[]
    site=venv/'Lib/site-packages'
    for info in site.glob('*.dist-info'):
        metadata=info/'METADATA'
        if not metadata.is_file():continue
        text=metadata.read_text(encoding='utf-8',errors='replace')
        name=re.search(r'^Name: ([-\w.]+)$',text,re.M);version=re.search(r'^Version: ([^\r\n]+)$',text,re.M)
        packages.append({'name':name.group(1) if name else 'UNKNOWN','version':version.group(1) if version else 'UNKNOWN','metadata_sha256':sha(metadata),'record_exists':(info/'RECORD').is_file(),'record_sha256':sha(info/'RECORD') if (info/'RECORD').is_file() else None})
    deps.append({'root':str(root),'venv_configuration':meta(cfg) if cfg.is_file() else None,'interpreter':meta(interpreter) if interpreter.is_file() else None,'installed_metadata':packages,'complete_old_build_closure':False,'limit':'Read dist-info Name/Version and hashes only, no package imports/installation. Mutable installed metadata is not a frozen dependency artifact, interpreter/stdlib inventory or prior-process load witness.'})
locks=[]
for p in files(ROOT)+external_files:
    if p.is_relative_to(OUT):continue
    if re.search(r'^(uv\.lock|poetry\.lock|Pipfile\.lock|requirements[^/]*\.(txt|lock|json)|package-lock\.json|test-requirements\.json)$',p.name,re.I):locks.append(meta(p))
write('DEPENDENCY_EVIDENCE.json',{'timestamp':now(),'environments':deps,'lock_records':locks,'frontend_lock_limit':'package-lock.json covers frontend declared dependency resolution; not prior Python/native/runtime/model closure. test-requirements.json is not a production dependency lock.','historical_environment_records':[meta(ROOT/'reports'/n) for n in ['V1_RECOVERY_ENVIRONMENT.json','V1_CLOSURE_ENVIRONMENT.json','CONFIGURATION_BASELINE_20261006.json'] if (ROOT/'reports'/n).is_file()]})
refs=[]
for rel in ['ROLLBACK_PLAN.md','app/improvement/release.py','scripts/staging_drill.py','tests/test_backup_restore.py','app/core/config.py','app/core/nusantara_config.py','app/knowledge/store.py','service/nusantara-service.ps1','service/nusantara-supervisor.ps1','service/install-nusantara-task.ps1','docs/reports/r2-a14-build-provenance-20261008-61f072ac/APPLICATION_BUILD_BOUNDARY.json','docs/reports/v1-alignment-prerequisites-20261009-104217/PREREQUISITE_ROLLBACK_REPORT.json']:
    refs.append(meta(ROOT/rel))
dotenv_locations=[ROOT/'.env',external/'.env',ROOT.parent/'.env']
config={'timestamp':now(),'process_environment':'UNKNOWN: not captured or reconstructed','previous_import_configuration_bytes':'UNKNOWN: current source defaults are not prior loaded configuration proof','dotenv_presence':[{'path':str(p),'exists':p.is_file(),'content_copied':False} for p in dotenv_locations],'known_process_launch':'Historical confirmed .venv/Scripts/python.exe -m uvicorn app.main:app --host127.0.0.1 --port8000 --workers1; cwd current repository from prior attestation; no reload. Current process safe flags recorded separately.','static_configuration_owner':'Settings compose once: default, optional explicit config_file, dotenv, inherited environment, explicit overrides. No evidence that rag_runtime.json was supplied as config_file to PID33160.','secret_handling':'No environment values, tokens, cookie/password contents, raw shell parent command line or auth values captured. Secret-named files content skipped.','launch_scripts':'service/nusantara-service.ps1 has matching start syntax, but its start path performs hard stop of existing app/port owners and may launch Ollama. Supervisor may auto-start processes. Neither script run; matching text does not prove prior effective environment.','safe_launch_not_yet_verified':'Exact bootstrap syntax known; prior effective configuration, dependencies and resources remain UNKNOWN/NOT_VERIFIED. No guessed rollback command.','references':refs}
write('CONFIGURATION_ORIGINS.json',config)
data=[]
for base in [ROOT/'data',external/'data',ROOT/'reports/v1-recovery-candidate']:
    for p in files(base):
        if p.suffix.lower() in ['.db','.sqlite','.sqlite3'] or p.name.endswith(('-wal','-shm')) or re.search(r'backup|snapshot|manifest|schema|migrat',p.name,re.I):data.append(meta(p,False))
write('DATA_RECOVERY_EVIDENCE.json',{'timestamp':now(),'existing_data_metadata_only':data,'archive_data_members_reference':'ARCHIVE_CLASSIFICATION.json','live_database_opened':False,'sqlite_integrity_or_schema_test':'NOT_RUN','production_restore_proven':False,'missing':['Consistent quiesced current production DB/data snapshot linked to prior build and schema','Independent checksum/manifest for database, index, approved knowledge and WAL handling at common recovery point','Documented backward schema compatibility/approved restore sequence and ownership','Historical production recovery test covering integrity, knowledge retrieval, memory and business behavior; existing staging drill only health'],'startup_risk':'KnowledgeStore mkdir -> SQLite connect -> WAL -> CREATE TABLE/INDEX IF NOT EXISTS can affect data even without chat. Full migration compatibility not demonstrated. Existing synthetic restore tests validate safety/checksum, not production data recoverability.','current_db_limit':'Metadata not content proof; active DB may change independently while running. No snapshot created or restored.'})
after={'timestamp':now(),'head':baseline.git('rev-parse','HEAD'),'git_status':baseline.git('status','--short'),'fingerprint':fp(),'preservation':preservation()}
b=before['preservation']['sha256'];a=after['preservation']['sha256']
changes={'modified':sorted(p for p in a.keys()&b.keys() if a[p]!=b[p]),'removed':sorted(b.keys()-a.keys()),'added':sorted(a.keys()-b.keys())}
write('CHANGE_AUDIT.json',{'timestamp':now(),'status':'PASS_SCOPED' if not any(changes.values()) and before['fingerprint']==after['fingerprint'] and before['head']==after['head'] else 'REVIEW_REQUIRED','changes':changes,'before':before,'after':after,'scope':'New report directory excluded. Existing source, tests, reports, backup/checkpoint/config/bundle/cache content hashed; secrets and live data not copied. Read errors retained; no whole-disk/full live DB immutability claim.','new_tests':0,'application_startups':0,'provider_invocations':0,'runtime_signals':0})
write('SEARCH_LIMITATIONS.json',{'timestamp':now(),'errors':errors,'limitations':['Initial non-escalated directory reads denied; repeated read-only inventory with approved metadata access.','No secret values exposed or raw backup configuration text copied.','No archive extracted/modified; no environment or artifact created.','No application import; only AST-isolated existing pure source fingerprint function used.','No graph query/update: persistent cache mutation forbidden.','Full model-weight/stdlib/native closure not hashed or loaded; installed metadata is discovery evidence only.']})
print(json.dumps({'source':after['fingerprint'],'external_source':external_record['fingerprint'],'archives':len(archives),'archive_checksums':{p['path']:p['checksum_status'] for p in archives},'dependency_environments':[(d['root'],len(d['installed_metadata'])) for d in deps],'changes':changes,'read_errors':len(errors)},indent=2))
