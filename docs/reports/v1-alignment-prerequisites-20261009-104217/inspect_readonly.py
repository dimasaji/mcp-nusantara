"""Read-only prerequisite inspection. Exclusive writes restricted to this report directory."""
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import tarfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OLD = ROOT/'docs/reports/v1-runtime-alignment-20261009-103149'
PREV = ROOT/'docs/reports/v1-functional-closure-20261009-101736'
def now(): return datetime.now(timezone(timedelta(hours=7))).isoformat()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, value):
    with (OUT/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
spec = importlib.util.spec_from_file_location('preservation', PREV/'prepare_baseline.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
baseline.OUT = OUT
def snapshot():
    value = baseline.snapshot()
    for rel in ['audit_reports', 'control-plane/dist', 'control-plane/tests', '.dockerignore', '.env.example', 'ROLLBACK_PLAN.md', 'RELEASE_READINESS_REPORT.md', 'config']:
        base = ROOT/rel
        for p in [base] if base.is_file() else base.rglob('*'):
            if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:
                try: value['sha256'][p.relative_to(ROOT).as_posix()] = digest(p)
                except OSError as exc: value['errors'].append({'path':str(p),'error':type(exc).__name__})
    return value
# Execute only the existing pure fingerprint function, without application imports.
tree = ast.parse((ROOT/'app/core/runtime_identity.py').read_text(encoding='utf-8'))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'source_build_id')
ns = {'Path':Path, 'ROOT':ROOT, 'hashlib':hashlib}
exec(compile(ast.Module(body=[fn], type_ignores=[]), '<existing-source-build-id-function>', 'exec'), ns)
fingerprint = ns['source_build_id']
before = {'timestamp':now(), 'head':baseline.git('rev-parse','HEAD'), 'git':baseline.git('status','--short'), 'source_fingerprint':fingerprint(), 'snapshot':snapshot()}
write('BASELINE.json', before)
refs = {}
for base, names in [(OLD,['ALIGNMENT_PLAN.json','CHANGE_AUDIT.json','RUNTIME_ALIGNMENT_REPORT.json','HTTP_OBSERVATIONS.json','UNRESOLVED_REQUIREMENTS.json']), (PREV,['BASELINE.json','CAPABILITY_MATRIX.json','IMPLEMENTATION_REPORT.json','REGRESSION.json','RUNTIME_EVIDENCE.json','CHANGE_AUDIT.json','REMAINING_GATES.json'])]:
    for name in names:
        p = base/name
        refs[p.relative_to(ROOT).as_posix()] = {'exists':p.is_file(), 'sha256':digest(p) if p.is_file() else None}
write('EVIDENCE_REFERENCES.json', refs)
artifacts = []
for dirname in ['staging-drill-20261006T025037193681Z','staging-drill-20261006T025945053115Z']:
    directory = ROOT/'audit_reports'/dirname
    for archive in (directory/'backups').glob('*.tar.gz'):
        checksum = archive.with_name(archive.name+'.sha256')
        expected = checksum.read_text().strip().split()[0] if checksum.is_file() else None
        with tarfile.open(archive, 'r:gz') as tf:
            members = [{'name':m.name,'size':m.size,'type':m.type.decode('ascii',errors='replace')} for m in tf.getmembers()]
        restored = directory/'restored/release-source'
        artifacts.append({'archive':str(archive),'sha256':digest(archive),'sidecar_sha256':expected,'checksum_match':digest(archive)==expected,'members':members,'existing_restored_root':str(restored),'existing_restored_fingerprint':fingerprint(restored) if restored.is_dir() else None,'historical_result':read(directory/'result.json'),'source_provenance':'scripts/staging_drill.py: copied app, pyproject.toml and config; isolated quiesced staging data; then fault injection in release-source. Existing restored copy predates the fault.', 'dependency_snapshot':'No interpreter, full pinned dependency closure or wheel set in this archive member list','bootstrap':'Historical script used its sys.executable -m uvicorn app.main:app --host 127.0.0.1 --port <ephemeral> --no-access-log; cwd restored/release-source; inherited environment plus isolated data paths, admin token removed','current_runtime_rollback_ready':False,'reason':'Historical staging health-only result; not tied to b7455 prior runtime fingerprint; omitted worker and frontend bundle/dependencies. No startup/restore executed now.'})
partials = {}
for rel in ['reports/developer-core-backup-20261006-175153','reports/v1-cc01-option-c-backup-20261006','reports/v1-closure-backup-20261006','reports/v1-recovery-backup-20261006','reports/v1-recovery-candidate']:
    directory=ROOT/rel
    partials[rel]={'exists':directory.is_dir(),'files':[p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()],'classification':'Historical partial source/data backup; no verified complete runnable prior runtime build. Fragments not assembled or altered.'}
write('ARTIFACT_INSPECTION.json', {'timestamp':now(),'archives':artifacts,'partial_backups':partials,'worktrees':baseline.git('worktree','list','--porcelain'),'archive_extraction':False,'artifact_execution':False,'scope':'Known repository-local artifacts; not an exhaustive machine-wide backup search'})
observations = {}
for path in ['/health','/openapi.json','/console','/v1/control-plane/model-status','/v1/control-plane/models','/v1/runtime/attestation']:
    item={'timestamp':now(),'method':'GET','url':'http://127.0.0.1:8000'+path}
    try:
        try: response=urlopen(item['url'],timeout=8)
        except HTTPError as exc: response=exc
        with response:
            raw=response.read(1024*1024)
            item.update(status=response.status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            if 'json' in response.headers.get('Content-Type',''): item['body']=json.loads(raw)
    except Exception as exc: item.update(status='NOT_VERIFIED',error=repr(exc))
    observations[path]=item
write('HTTP_OBSERVATIONS.json', observations)
resources={}
for rel in ['.env','.venv/Scripts/python.exe','.venv/pyvenv.cfg','nusantara-models/.venv/Scripts/python.exe','nusantara-models/indobert_worker.py','config/rag_runtime.json','control-plane/dist/index.html','pyproject.toml','control-plane/package-lock.json']:
    p=ROOT/rel
    resources[rel]={'exists':p.is_file(),'size':p.stat().st_size if p.is_file() else None,'sha256':digest(p) if p.is_file() and rel!='.env' else None}
dist={p.relative_to(ROOT).as_posix():digest(p) for p in (ROOT/'control-plane/dist').rglob('*') if p.is_file()}
write('BOOTSTRAP_INSPECTION.json', {'timestamp':now(),'resources':resources,'frontend_hashes':dist,'python_version':sys.version,'python_executable':sys.executable,'configuration_owner':'app/core/config.py Settings.compose_configuration -> app/core/nusantara_config.py: default -> optional explicitly supplied config_file -> DOTENV -> ENV -> EXPLICIT; composed once. Default paths resolved from working directory. config/rag_runtime.json existence does not prove it is passed as bootstrap config_file.','exact_effective_current_runtime_environment':'NOT_VERIFIED: inherited environment of PID33160 not captured; .env secret values neither printed nor copied','launch_syntax':read(OLD/'ALIGNMENT_PLAN.json')['proposed_launch_command'],'launch_executed':False,'health_command':"& 'C:\\Users\\dmaza\\mcp-starter\\.venv\\Scripts\\python.exe' -B scripts/healthcheck.py",'health_semantics':'scripts/healthcheck.py only GET /health with 3s timeout; HTTP success alone does not prove native RAG/semantic worker or provider generation.','startup_side_effects':'app/api/routes.py module-level KnowledgeEngine; app/knowledge/store.py constructor creates directory, opens SQLite, PRAGMA journal_mode=WAL and CREATE TABLE/INDEX IF NOT EXISTS. Normal candidate startup not executed because DB/data changes are outside this request.','native_readiness':'File existence is not proof of worker/embedding model readiness. Historical native_candidate.py used semantic and retrieval fixtures with child-only overrides; not a normal boot recipe.'})
after={'timestamp':now(),'head':baseline.git('rev-parse','HEAD'),'git':baseline.git('status','--short'),'source_fingerprint':fingerprint(),'snapshot':snapshot()}
b=before['snapshot']['sha256']; a=after['snapshot']['sha256']
changes={'modified':[p for p in b.keys()&a.keys() if b[p]!=a[p]],'removed':sorted(b.keys()-a.keys()),'added':sorted(a.keys()-b.keys())}
write('CHANGE_AUDIT.json', {'timestamp':now(),'before':before,'after':after,'changes':changes,'status':'PASS' if not any(changes.values()) and before['head']==after['head'] else 'REVIEW_REQUIRED','limitations':'Only new evidence directory excluded; scoped content hashes, not all machine filesystem. Existing Git inaccessible temporary-directory warnings retained. No .env values or live DB inspected. Read-only HTTP may increment runtime observability counters.'})
print(json.dumps({'source':after['source_fingerprint'],'archives':[{ 'checksum_match':x['checksum_match'],'fingerprint':x['existing_restored_fingerprint']} for x in artifacts],'changes':changes,'resources':resources},indent=2))
