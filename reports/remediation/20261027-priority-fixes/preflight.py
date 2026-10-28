"""Capture existing source and consistent SQLite backups before remediation."""
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent
GIT = 'C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
os.chdir(ROOT)
import sys
sys.path.insert(0,str(ROOT))
from dotenv import dotenv_values
from app.core.nusantara_config import load_nusantara_config

baseline_path=RUN/'baseline.json'
if baseline_path.exists():
    raise SystemExit('Baseline already exists; do not overwrite source/DB backup evidence.')
configuration=load_nusantara_config(dotenv_environment=dotenv_values(ROOT/'.env',interpolate=False),
                                   environment=os.environ,project_root=ROOT)
files=[p for area in ['app','tests','control-plane/src','control-plane/tests']
       for p in (ROOT/area).rglob('*') if p.is_file() and p.suffix in {'.py','.ts','.tsx','.html'}
       and '__pycache__' not in p.parts]
manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
targets=['app/knowledge/sop_review.py','app/security/v1_knowledge.py','app/knowledge/document_tools.py',
         'app/api/knowledge_pipeline.py','app/knowledge/engine.py','app/knowledge/production_kb.py',
         'app/knowledge/production_embedding_bridge.py','app/knowledge/official_knowledge_ingestion.py',
         'app/api/routes.py','app/hermes/agent.py','tests/test_sop_review.py','tests/test_document_tools.py']
for name in targets:
    dest=RUN/'source-before'/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/name,dest)

def git(*args):
    result=subprocess.run([GIT,'-c','core.fsmonitor=false','--no-optional-locks',*args],cwd=ROOT,
                          capture_output=True,text=True,encoding='utf-8',errors='replace')
    return {'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}

backups=[]
candidates={Path(configuration.knowledge.database).resolve(),
            ROOT/'data/knowledge/production_knowledge.db',ROOT/'data/knowledge/nusantara_knowledge.db'}
for index,path in enumerate(sorted(candidates)):
    if not path.is_file():
        backups.append({'source':str(path),'status':'ABSENT'});continue
    folder=RUN/'database-before'/str(index)
    folder.mkdir(parents=True,exist_ok=True)
    target=folder/path.name
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=15) as source:
        source.execute('PRAGMA query_only=ON')
        with sqlite3.connect(target) as destination:
            source.backup(destination,pages=512,sleep=.05)
    with sqlite3.connect(target) as restored:
        integrity=restored.execute('PRAGMA integrity_check').fetchone()[0]
        tables=[r[0] for r in restored.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        counts={name:restored.execute('SELECT COUNT(*) FROM "'+name.replace('"','""')+'"').fetchone()[0]
                for name in tables if name in {'documents','chunks','knowledge_pipeline_runs',
                    'sop_review_events','sop_review_trials','sop_review_sessions','sop_review_pilots','document_extractions'}}
    originals=path.parent/'source-documents'
    if originals.is_dir():
        shutil.copytree(originals,folder/'source-documents',dirs_exist_ok=False)
    extractions=path.parent/'docling'
    if extractions.is_dir():
        shutil.copytree(extractions,folder/'docling',dirs_exist_ok=False)
    backups.append({'source':str(path),'backup':str(target),'status':'PASS' if integrity=='ok' else 'FAIL',
                    'integrity_check':integrity,'tables':tables,'counts':counts,
                    'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
baseline={'created_at_utc':datetime.now(timezone.utc).isoformat(),'head':git('rev-parse','HEAD'),
          'tracked_status':git('status','--short','--untracked-files=no'),
          'effective_knowledge_database':str(configuration.knowledge.database),'source_hashes':manifest,
          'database_backups':backups,'scope':'four operator-approved remediation priorities; no commit/push'}
baseline_path.write_text(json.dumps(baseline,indent=2),encoding='utf-8')
print(json.dumps({'head':baseline['head']['stdout'].strip(),'sources':len(manifest),
                  'backups':backups},indent=2))
