"""Inspect existing legacy ZIP in memory, without extraction or code execution."""
import hashlib
import json
import os
import re
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
archive=ROOT.parent/'mcp-starter.zip'
def sha_file(p):
    digest=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()
def write(name,data):
    with (OUT/name).open('x',encoding='utf-8') as stream:json.dump(data,stream,ensure_ascii=False,indent=2)
result={'timestamp':datetime.now(timezone(timedelta(hours=7))).isoformat(),'archive':str(archive),'exists':archive.is_file(),'extracted':False,'executed':False}
if archive.is_file():
    stat=archive.stat();result.update(bytes=stat.st_size,mtime_ns=stat.st_mtime_ns,sha256=sha_file(archive))
    side=archive.with_name(archive.name+'.sha256');result['sidecar_exists']=side.is_file()
    result['checksum_status']='NO_INDEPENDENT_SIDECAR'
    if side.is_file():
        text=side.read_text(encoding='ascii',errors='replace').strip()
        match=re.match(r'^([a-fA-F0-9]{64})(?:\s|$)',text)
        result['checksum_status']='VALID' if match and match.group(1).lower()==result['sha256'] else 'MISMATCH_OR_INVALID_SIDECAR'
    with zipfile.ZipFile(archive) as source:
        members=source.infolist();names=[m.filename for m in members]
        result['member_manifest']=[{'name':m.filename,'bytes':m.file_size,'compressed_bytes':m.compress_size} for m in members]
        roots=sorted({n[:-len('app/main.py')] for n in names if n.endswith('app/main.py') and '/site-packages/' not in n})
        builds=[]
        for prefix in roots:
            entries=[]
            for m in members:
                if not m.filename.startswith(prefix) or m.is_dir():continue
                rel=m.filename[len(prefix):]
                if rel.startswith('app/') and Path(rel).suffix in {'.py','.json','.html','.css','.js'} or rel in {'pyproject.toml','nusantara-models/indobert_worker.py'}:
                    entries.append((rel,m))
            digest=hashlib.sha256();limited=[]
            for rel,m in sorted(entries):
                if m.file_size>10*1024*1024:limited.append(rel);continue
                content=source.read(m);name=rel.encode('utf-8')
                digest.update(len(name).to_bytes(8,'big'));digest.update(name)
                digest.update(len(content).to_bytes(8,'big'));digest.update(content)
            fingerprint='sha256:'+digest.hexdigest() if not limited else None
            builds.append({'root_prefix':prefix,'source_fingerprint_same_current_algorithm':fingerprint,'source_files_hashed':len(entries)-len(limited),'skipped_large_members':limited,'matches_runtime_import_snapshot':fingerprint=='sha256:b7455ef0823df00d73a576147c6331ed69f9b74c145de39281819c3cad78d27f','worker_present':prefix+'nusantara-models/indobert_worker.py' in names,'frontend_dist_members':[n for n in names if n.startswith(prefix+'control-plane/dist/')],'dependency_lock_members':[n for n in names if n.startswith(prefix) and re.search(r'(uv\.lock|poetry\.lock|Pipfile\.lock|requirements[^/]*\.txt|package-lock\.json)$',n,re.I)]})
        result['source_builds']=builds
        metadata=[]
        for m in members:
            if m.filename.endswith('.dist-info/METADATA') and m.file_size<1024*1024:
                raw=source.read(m);text=raw.decode('utf-8',errors='replace')
                name=re.search(r'^Name: ([-\w.]+)$',text,re.M);version=re.search(r'^Version: ([^\r\n]+)$',text,re.M)
                metadata.append({'member':m.filename,'name':name.group(1) if name else 'UNKNOWN','version':version.group(1) if version else 'UNKNOWN','sha256':hashlib.sha256(raw).hexdigest()})
        result['installed_dependency_metadata']=metadata
        result['interpreter_members']=[{'member':m.filename,'sha256':hashlib.sha256(source.read(m)).hexdigest()} for m in members if m.filename.endswith('/Scripts/python.exe') and m.file_size<10*1024*1024]
        result['venv_configuration_members']=[m.filename for m in members if m.filename.endswith('/pyvenv.cfg')]
        result['data_members']=[{'name':m.filename,'bytes':m.file_size} for m in members if re.search(r'(/data/|\.db$|\.db-wal$|\.db-shm$)',m.filename)]
        result['secret_content_handling']='No environment/credential/token/cookie/password/data file contents read or recorded; only executable source fingerprint, package Name/Version and launcher byte hashes inspected in memory.'
    result['before_after_stat_equal']=stat.st_size==archive.stat().st_size and stat.st_mtime_ns==archive.stat().st_mtime_ns
    result['dependency_complete']='NOT_ESTABLISHED: bundled .venv/metadata is not interpreter/stdlib/native/model transitive closure or load witness; scripts launcher depends on base interpreter outside archive'
    result['historical_restore_execution_evidence']='NOT_FOUND_LINKED_TO_THIS_ARCHIVE'
    result['verified_old_runtime_rollback']=False
write('LEGACY_ZIP_INSPECTION.json',result)
# Search data areas only for recovery artifact names; do not open live databases.
recovery=[]
for base in [ROOT/'data',Path('E:/AI/mcp-starter/data')]:
    for directory,dirs,names in os.walk(base,followlinks=False):
        dirs[:]=[d for d in dirs if not (Path(directory)/d).is_symlink()]
        for name in names:
            if re.search(r'backup|snapshot|manifest|migrat|schema|\.zip$|\.tar\.gz$',name,re.I):
                p=Path(directory)/name;s=p.stat()
                recovery.append({'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'content_opened':False})
write('DATA_BACKUP_SEARCH.json',{'timestamp':datetime.now(timezone(timedelta(hours=7))).isoformat(),'searched_roots':[str(ROOT/'data'),'E:/AI/mcp-starter/data'],'matching_artifact_names':recovery,'production_consistency_and_restore_proof':'NOT_ESTABLISHED'})
print(json.dumps({'archive':str(archive),'sha256':result.get('sha256'),'builds':result.get('source_builds'),'package_metadata_count':len(result.get('installed_dependency_metadata',[])),'interpreter_members':result.get('interpreter_members'),'data_recovery_artifacts':len(recovery)},indent=2))
