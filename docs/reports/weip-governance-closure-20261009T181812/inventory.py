import hashlib, json, re, subprocess
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
GIT=r'C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def git(*args):
    p=subprocess.run([GIT,*args],cwd=ROOT,text=True,capture_output=True)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest_path=ROOT/'data/knowledge/official_sources/ktp_el/manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
records=[]
for d in manifest['documents']:
    p=manifest_path.parent/(d['id'].lower()+'.md')
    b=p.read_bytes(); text=b.decode('utf-8-sig'); lf=text.replace('\r\n','\n')
    meta=dict(re.findall(r'^([A-Z_]+): (.*)$',lf.split('---',2)[1],re.M))
    body=lf.split('## Isi Sumber\n\n',1)[1]
    candidates={'full_file':sha(b),'lf_file':sha(lf.encode()),'extracted_body':sha(body.encode()),
                'extracted_body_stripped':sha(body.strip().encode()),'extracted_body_rstripped':sha(body.rstrip().encode())}
    records.append({'document_id':d['id'],'path':str(p),'exists':True,'bytes':len(b),
      'mtime_utc':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),
      'sha256':sha(b),'expected_sha256':d['sha256'],'expected_source':str(manifest_path),
      'expected_authority':'DECLARED_MANIFEST_NOT_INDEPENDENTLY_AUTHENTICATED',
      'integrity':'INTEGRITY_PASS' if sha(b)==d['sha256'] else 'INTEGRITY_FAIL',
      'digest_candidates':candidates,'matching_representations':[k for k,v in candidates.items() if v==d['sha256']],
      'body_chars':len(body),'manifest_content_length':d.get('content_length'),
      'metadata_consistency':{'id':meta.get('DOCUMENT_ID')==d['id'],'title':meta.get('TITLE')==d['title'],
        'url':meta.get('SOURCE_URL')==d['url'],'embedded_hash':meta.get('SOURCE_HASH')==d['sha256']},
      'claimed_url':d['url'],'claimed_published_at':d.get('published_at'),'claimed_retrieved_at':d.get('retrieved_at'),
      'approval_reference':d.get('approval_reference'),'approval_state':'NEEDS_OWNER_INPUT',
      'provenance':'REVIEW_REQUIRED','status':'REVIEW_REQUIRED',
      'tracking':git('ls-files','--error-unmatch','--',str(p.relative_to(ROOT)))})
paths=[manifest_path]+[Path(r['path']) for r in records]+[
 ROOT/'docs/commands/NUS-V1-WEIP-20261009.MD',
 ROOT/'docs/reports/post-weip-console-20261009T175526/REPORT.md',
 ROOT/'docs/reports/weip-completion-20261009T104250Z/CHANGE_AUDIT.json',
 ROOT/'docs/reports/v1-rollback-investigation-20261009-105200/LEGACY_ZIP_INSPECTION.json']
inventory={'timestamp':datetime.now(timezone.utc).isoformat(),'head':git('rev-parse','HEAD'),
 'branch':git('branch','--show-current'),'status':git('status','--short','--untracked-files=all'),
 'files':[{'path':str(p),'exists':p.exists(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),
 'mtime_utc':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()} for p in paths],
 'baseline_hashes':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for folder in ['app','tests','control-plane/src','control-plane/tests']
   for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.py','.tsx','.ts','.css'}}}
zip_record=json.loads(paths[-1].read_text())
inventory['historical_archive_limit']={'checksum_status':zip_record.get('checksum_status'),
 'matching_members':[m for m in zip_record.get('member_manifest',[]) if 'official_sources/ktp_el/' in m['name']],
 'limitation':'Member names/sizes are not per-document authenticated hashes; archive not opened/extracted here.'}
(OUT/'EVIDENCE_INVENTORY.json').write_text(json.dumps(inventory,indent=2))
(OUT/'FIXTURE_VERIFICATION.json').write_text(json.dumps({'documents':records,'live_acquisition':'NOT_RUN',
 'document_use_approval':'NEEDS_OWNER_INPUT','source_authentication':'NOT_VERIFIED'},indent=2))
print(json.dumps([{'id':r['document_id'],'actual':r['sha256'],'matches':r['matching_representations']} for r in records],indent=2))
