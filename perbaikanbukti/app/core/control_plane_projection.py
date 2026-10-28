"""Read-only engineering evidence projection. No app/worker/database imports."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
GIT = Path('C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(root: Path = ROOT) -> dict:
    evidence: list[dict] = []
    warnings: list[str] = []

    def read(key: str, path: Path, expected: str | None = None, *, pinned: bool = False):
        ref = {'id': key, 'reference': str(path), 'sha256': None, 'status': 'NOT_VERIFIED'}
        evidence.append(ref)
        try:
            if path.stat().st_size > 4_000_000:
                raise ValueError('artifact exceeds projection size limit')
            actual = digest(path)
            if pinned and not expected:
                raise ValueError('required evidence hash unavailable')
            if expected and actual != expected.lower():
                raise ValueError('artifact hash mismatch')
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            if not isinstance(data, list if key == 'parity' else dict):
                raise ValueError('unexpected artifact structure')
            ref.update(sha256=actual, status='VERIFIED_ARTIFACT')
            return data
        except (OSError, ValueError, TypeError) as exc:
            warnings.append(f'{key}: {type(exc).__name__}; evidence unavailable or invalid')
            return {}

    r1 = read('r1', root/'.dev/MDA_R1_OFFICIAL_CLOSURE_20261007_143016.json')
    r2 = read('r2', root/'.dev/MDA_R2_IMPLEMENTATION_CHECKPOINT.json')
    owner = read('r2-owner', root/'.dev/checkpoints/r2-20261007/FINAL_OWNER_ACCEPTANCE_RECORD.json', r2.get('administrative_acceptance_sha256'), pinned=True)
    sources = read('sources', root/'control-plane/evidence-sources.json')
    allowed_audit = Path(sources.get('r3_audit', '__missing__'))
    r3 = read('r3', allowed_audit/'closure-manifest.json', sources.get('r3_manifest_sha256'), pinned=True)
    # A matching manifest is insufficient if its accepted report is missing/drifted.
    try:
        if not r3.get('report_sha256') or digest(allowed_audit/'MDA_R3_IMPLEMENTATION_CLOSURE.md') != r3['report_sha256']:
            raise ValueError('R3 closure report unavailable or mismatched')
    except (OSError, ValueError):
        warnings.append('R3 closure report: NOT_VERIFIED')
        r3 = {}
    runtime = read('r2-runtime', root/'.dev/checkpoints/r2-20261007/health-gate/runtime-verification.json',
                   r2.get('evidence_sha256', {}).get('.dev/checkpoints/r2-20261007/health-gate/runtime-verification.json'), pinned=True)
    expected_hashes = sources.get('expected_hashes', {})
    profile = read('rag-profile', allowed_audit/'actual-profile.json', expected_hashes.get('actual-profile.json'), pinned=True) if r3 else {}
    integrity = read('r3-integrity', allowed_audit/'integrity-final.json', expected_hashes.get('integrity-final.json'), pinned=True) if r3 else {}
    authorization = read('cplane-owner', root/'control-plane/CPLANE_OWNER_AUTHORIZATION.json')
    contract_path = root/'docs/commands/MDA-CPLANE-UI-AUTH-001.md'
    try:
        contract = contract_path.read_text(encoding='utf-8-sig')
        evidence.append({'id':'cplane-contract','reference':str(contract_path),'sha256':digest(contract_path),'status':'VERIFIED_ARTIFACT'})
    except OSError:
        contract = ''
        warnings.append('CPLANE contract unavailable')

    def locked(phase):
        match = re.search(r'\*\*'+re.escape(phase)+r':\*\*\s*([^\r\n]+)', contract)
        return match.group(1).strip().replace(' ', '_') if match else 'UNKNOWN'

    phases = [
        {'id':'R1','name':'Configuration Intelligence','status':r1.get('status','UNKNOWN'),'evidence':['r1'],'kind':'EXISTING'},
        {'id':'R2','name':'Provider / Model Runtime Identity','status':r2.get('status','UNKNOWN') if owner.get('status') == 'APPROVED' else 'NOT_VERIFIED','evidence':['r2','r2-owner'],'kind':'EXISTING'},
        {'id':'R3','name':'Effective RAG Profile','status':r3.get('status','NOT_VERIFIED'),'evidence':['r3'],'kind':'EXISTING'},
        {'id':'R4','name':'Embedding / Index Compatibility','status':locked('R4'),'evidence':['cplane-contract'],'kind':'PROPOSED'},
        {'id':'R5','name':'Runtime Enforcement','status':locked('R5'),'evidence':['cplane-contract'],'kind':'PROPOSED'},
        {'id':'MDE10','name':'Master Developer Engine','status':locked('MDE10'),'evidence':['cplane-contract'],'kind':'PROPOSED'},
    ]
    verification = []
    for key, name in [('focused','closure-focused.xml'),('regression','closure-regression.xml')]:
        path = allowed_audit/name
        try:
            if not r3 or path.stat().st_size > 4_000_000:
                raise ValueError('unverified R3')
            if not expected_hashes.get(name) or digest(path) != expected_hashes[name]:
                raise ValueError('test evidence hash mismatch')
            doc = ElementTree.fromstring(path.read_bytes())
            suites = [doc] if doc.tag == 'testsuite' else list(doc.findall('testsuite'))
            values = {field:sum(int(s.get(field,'0')) for s in suites) for field in ('tests','failures','errors','skipped')}
            evidence.append({'id':key,'reference':str(path),'sha256':digest(path),'status':'VERIFIED_ARTIFACT'})
            verification.append({'id':key,**values,'status':'PASS' if not values['failures'] and not values['errors'] and values['tests'] else 'FAIL','evidence':[key]})
        except (OSError, ValueError, ElementTree.ParseError):
            verification.append({'id':key,'status':'NOT_VERIFIED','evidence':[]})
    parity = read('parity', allowed_audit/'query-parity.json', expected_hashes.get('query-parity.json'), pinned=True) if r3 else {}
    if isinstance(parity,list):
        verification.append({'id':'query-parity','tests':len(parity),'failures':sum(p.get('status')!='PASS' for p in parity),
                             'status':'PASS' if parity and all(p.get('status')=='PASS' for p in parity) else 'NOT_VERIFIED','evidence':['parity']})
    gates = [{'id':key,'status':value,'evidence':['r3']} for key,value in r3.get('gate_statuses',{}).items()]

    def git(*args):
        proc = subprocess.run([str(GIT),'-c','core.quotepath=false',*args],cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=5)
        if proc.returncode:
            raise ValueError('git unavailable')
        if proc.stderr:
            warnings.append('Git coverage PARTIAL: some inherited report directories are inaccessible')
        return proc.stdout.strip('\r\n')

    try:
        status = git('status','--short').splitlines()
        files = [{'path':line[3:],'state':line[:2],'ownership':'UNKNOWN'} for line in status if len(line)>3]
        worktree = {'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'tracked':sum(f['state']!='??' for f in files),
                    'untracked':sum(f['state']=='??' for f in files),'staged':sum(f['state'][0] not in (' ','?') for f in files),'files':files,'status':'PARTIAL' if any('Git coverage' in w for w in warnings) else 'READY'}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        worktree = {'status':'UNKNOWN','files':[]}
        warnings.append('Git state NOT_VERIFIED')
    protected = []
    hashes = runtime.get('database_hashes_after',{})
    for name in ('data/knowledge/nusantara_knowledge.db','data/knowledge/nusantara_knowledge.db-wal','data/knowledge/nusantara_knowledge.db-shm'):
        try:
            actual = digest(root/name)
            expected = hashes.get(name)
            protected.append({'path':name,'sha256':actual,'status':('UNCHANGED' if actual==expected else 'CHANGED') if expected else 'NOT_VERIFIED','evidence':['r2-runtime']})
        except OSError:
            protected.append({'path':name,'status':'NOT_VERIFIED','evidence':['r2-runtime']})
    identity = runtime.get('execution_identity',{})
    # Explicit projection: never expose executable, credentials or raw configuration.
    runtime_view = {key:identity.get(key) for key in ('configured_model','effective_model','selected_provider','actual_model','build_id','process_id','identity_status')}
    runtime_view.update(timestamp=runtime.get('timestamp'),scope='HISTORICAL_CONTROLLED_RUNTIME',current_status='NOT_VERIFIED',evidence=['r2-runtime'])
    warnings.extend(['R3 RAG receipt is a fixture, not production retrieval attestation.',
                     'Runtime identity is historical; current live process/model is NOT_VERIFIED.',
                     'R3 artifacts are in temporary storage; missing evidence remains NOT_VERIFIED.'])
    return {'schema_version':1,'timestamp':datetime.now(timezone.utc).isoformat(),'status':'PARTIAL' if warnings else 'READY',
            'system':'NUSANTARA CORE + HERMES','phases':phases,'current_phase':r3.get('status','UNKNOWN').split('_')[0],'contract':{'id':authorization.get('contract','UNKNOWN'),'status':authorization.get('status','NOT_AUTHORIZED'),'evidence':['cplane-owner','cplane-contract']},
            'gates':gates,'evidence':evidence,'verification':verification,'runtime':runtime_view,
            'rag':{'status':'FIXTURE_EVIDENCE' if profile else 'NOT_VERIFIED','profile':profile or None,'evidence':['rag-profile'] if profile else []},
            'worktree':worktree,'protected_assets':protected,'warnings':list(dict.fromkeys(warnings)),
            'blockers':[p['id']+': '+p['status'] for p in phases if p['status'] in ('LOCKED','NOT_AUTHORIZED')],
            'governance':{'read_only':True,'commit':authorization.get('commit','NOT_AUTHORIZED'),'push':authorization.get('push','NOT_AUTHORIZED'),
                          'acceptance':{'R2':owner.get('status','NOT_VERIFIED'),'R3':'NOT_VERIFIED'},
                          'scope':authorization.get('scope','UNKNOWN'),'rollback':'Isolated CPLANE-owned changes only; no global reset/restore',
                          'r3_integrity':{'outside_scope':integrity.get('outside_scope'),'protected_mismatch':integrity.get('protected_mismatch'),'static_syntax':integrity.get('static_syntax')},'evidence':['cplane-owner','r2-owner','r3-integrity']}}
