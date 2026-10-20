"""Run, seal and publish V1 offline evidence. No decisions or provider calls."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.core.evidence_registry import collect_review_package, _safe_path, _cross_process_lock


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_once(path, value):
    with Path(path).open('xb') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode('utf-8') + b'\n')
        stream.flush()
        os.fsync(stream.fileno())


def snapshot(root, spec):
    return {name:digest(_safe_path(root,name)) for name in sorted({p for c in spec['criteria'] for p in c['sources']})}


def finalize(root, folder, before, commands, exits, isolation):
    root,folder=Path(root).resolve(),Path(folder).resolve()
    folder.relative_to(root)
    if (folder/'FINALIZED.json').exists():raise ValueError('RUN_ALREADY_FINALIZED')
    spec=json.loads((root/'control-plane/evidence-requirements.json').read_text(encoding='utf-8'))
    if before!=snapshot(root,spec):raise ValueError('SOURCE_CHANGED_DURING_TESTS')
    py=folder/'python/python-results.xml';ui=folder/'ui/vitest-results.json'
    doc=ET.parse(py).getroot()
    cases=list(doc.iter('testcase'))
    suites=[doc] if doc.tag=='testsuite' else list(doc.iter('testsuite'))
    totals={k:sum(int(s.get(k,'0')) for s in suites) for k in ('tests','failures','errors','skipped')}
    if totals['tests']!=len(cases) or not cases:raise ValueError('PYTEST_COUNTS_INVALID')
    py_status={c.get('name'):not any(e.tag in {'failure','error','skipped'} for e in c) for c in cases}
    vitest=json.loads(ui.read_text(encoding='utf-8-sig'))
    assertions=[case for suite in vitest['testResults'] for case in suite['assertionResults']]
    if not assertions or vitest.get('numTotalTests')!=len(assertions):raise ValueError('VITEST_COUNTS_INVALID')
    if any(exits) or totals['failures'] or totals['errors'] or totals['skipped'] or any(c['status']!='passed' for c in assertions):
        raise ValueError('TEST_RUN_NOT_SUCCESSFUL')
    def passed(name):
        matches=[c for c in assertions if c.get('title')==name]
        return py_status.get(name) is True or bool(matches) and all(c['status']=='passed' for c in matches)
    criteria={c['id']:{'status':'PASS' if all(passed(t) for t in c['tests']) else 'FAIL','test_ids':c['tests']} for c in spec['criteria']}
    if any(c['status']!='PASS' for c in criteria.values()):raise ValueError('REQUIRED_TEST_NOT_PASSED')
    # Only leaf results are hashed. Never include this manifest or another manifest referring to the bundle.
    artifacts=[{'path':p.relative_to(root).as_posix(),'sha256':digest(p)} for p in (py,ui,folder/'commands.json',folder/'source-before.json')]
    bundle=folder/'results-bundle.json';write_once(bundle,{'schema_version':1,'artifacts':artifacts})
    manifest={'schema_version':1,'run_id':folder.name,'timestamp':datetime.now(timezone.utc).isoformat(),
              'command':commands,'exit_code':0,'scope':'offline evidence registry, decision API, isolated runner guards and Review UI; not operational runtime approval',
              'isolation':isolation,'results_path':bundle.relative_to(root).as_posix(),'results_sha256':digest(bundle),
              'counts':{'pytest_passed':len(cases),'vitest_passed':len(assertions),'failed':0,'errors':0,'skipped':0},
              'source_sha256':before,'criteria':criteria}
    path=folder/'test-run.json';write_once(path,manifest)
    write_once(folder/'FINALIZED.json',{'manifest_sha256':digest(path),'bundle_sha256':digest(bundle),'artifacts':artifacts})
    return path


def publish(root, folder, manifest):
    root=Path(root).resolve();folder=Path(folder).resolve();manifest=Path(manifest).resolve()
    seal=json.loads((folder/'FINALIZED.json').read_text())
    if digest(manifest)!=seal['manifest_sha256']:raise ValueError('FINALIZED_MANIFEST_CHANGED')
    value=json.loads(manifest.read_text())
    if digest(_safe_path(root,value['results_path']))!=seal['bundle_sha256']:raise ValueError('FINALIZED_RESULTS_CHANGED')
    for entry in seal['artifacts']:
        if digest(_safe_path(root,entry['path']))!=entry['sha256']:raise ValueError('FINALIZED_ARTIFACT_CHANGED')
    spec=json.loads((root/'control-plane/evidence-requirements.json').read_text())
    if snapshot(root,spec)!=value['source_sha256']:raise ValueError('SOURCE_CHANGED_AFTER_TESTS')
    active=_safe_path(root,spec['test_run_manifest'])
    with _cross_process_lock(active.with_suffix(active.suffix+'.publish.lock')):
        # Preserve prior active bytes; never edit an old finalized run.
        if active.exists():
            with (folder/'previous-active-test-run.json').open('xb') as stream:stream.write(active.read_bytes())
        temp=active.with_name(active.name+'.'+uuid4().hex+'.tmp')
        with temp.open('xb') as stream:
            stream.write(manifest.read_bytes());stream.flush();os.fsync(stream.fileno())
        os.replace(temp,active)
        package=collect_review_package(root)
        current=next(e for e in package['evidence'] if e.get('id')=='current-test-run')
        if current['sha256']!=digest(manifest) or not package['pass_allowed']:
            raise ValueError('PUBLISHED_PACKAGE_NOT_VALID')
        write_once(folder/'package.json',package)
        return package



def main():
    folder=ROOT/'artifacts/evidence-runs'/('run-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid4().hex[:10])
    folder.mkdir(parents=True,exist_ok=False)
    spec=json.loads((ROOT/'control-plane/evidence-requirements.json').read_text())
    before=snapshot(ROOT,spec);write_once(folder/'source-before.json',before)
    for sub in ('python','ui'):(folder/sub).mkdir()
    import httpx
    with httpx.Client(timeout=30) as client:
        response=client.get('http://127.0.0.1:8765/v1/control-plane/snapshot');response.raise_for_status()
        write_once(folder/'ui/snapshot.json',response.json())
    commands=[];exits=[]
    command=[sys.executable,str(ROOT/'tests/run_evidence_tests_isolated.py'),str(folder/'python')]
    result=subprocess.run(command,cwd=ROOT,capture_output=True)
    (folder/'python/process.log').write_bytes(result.stdout+result.stderr);commands.append(command);exits.append(result.returncode)
    env=os.environ.copy()
    env.update(NUSANTARA_TEST_RUN_DIR=str(folder/'ui'),NUSANTARA_VITEST_CACHE_DIR=str(folder/'ui/cache'),
               CPLANE_SNAPSHOT_FILE=str(folder/'ui/snapshot.json'),TEMP=str(folder/'ui'),TMP=str(folder/'ui'),
               NODE_OPTIONS='--require '+str(ROOT/'control-plane/tests/inspection-preview-network-guard.cjs'))
    command=['node',str(ROOT/'control-plane/node_modules/vitest/vitest.mjs'),'run','tests/human.test.tsx','tests/acceptance.test.ts','tests/verification-pages.test.tsx','tests/assistant.test.tsx','tests/knowledge-operations.test.tsx',
             '--config','vitest.config.ts','--configLoader','native','--reporter=json','--outputFile='+str(folder/'ui/vitest-results.json')]
    result=subprocess.run(command,cwd=ROOT/'control-plane',env=env,capture_output=True)
    (folder/'ui/process.log').write_bytes(result.stdout+result.stderr);commands.append(command);exits.append(result.returncode)
    write_once(folder/'commands.json',{'commands':commands,'exit_codes':exits})
    print('Run:',folder.relative_to(ROOT),flush=True)
    if any(exits):raise SystemExit('Tests failed; nothing published. Inspect run process.log files.')
    isolation={k:True for k in ('network_blocked','filesystem_writes_scoped','active_data_blocked','subprocess_blocked','cache_isolated')}
    isolation['exceptions']=['Vitest exact worker and esbuild transformer; Python internal Windows socketpair only. Test process guards are installed; metadata publication runs outside those child guards.']
    manifest=finalize(ROOT,folder,before,commands,exits,isolation)
    package=publish(ROOT,folder,manifest)
    print(json.dumps({'package_id':package['package_id'],'pass_allowed':package['pass_allowed'],'counts':json.loads(manifest.read_text())['counts'],'human_decision':'NOT_CREATED'}))

if __name__=='__main__':main()
