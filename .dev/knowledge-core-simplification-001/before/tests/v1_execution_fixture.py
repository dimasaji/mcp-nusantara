"""Build real isolated candidate evidence. Never reads or changes operational data."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]

def prepare(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    folder = root / 'data/developer_core'
    folder.mkdir(parents=True, exist_ok=True)
    staged = root / '.developer_staging/safe-action'
    staged.mkdir(parents=True, exist_ok=True)
    (root / 'safe-result.txt').write_text('before', encoding='utf-8')
    (staged / 'safe-result.txt').write_text('after', encoding='utf-8')
    plan = {'change_id':'safe-action', 'status':'APPROVED', 'expected_change':'Isolated reversible test: before -> after in safe-result.txt',
            'approval':{'approved':True}, 'write_scope':{'enabled':True},
            'execution':{'shell_execution':False,'production_write':False}, 'allowed_files':['safe-result.txt']}
    (folder / 'change_plan.json').write_text(json.dumps(plan), encoding='utf-8')
    candidate = root / 'test_safe_candidate.py'
    candidate.write_text("from pathlib import Path\ndef test_safe_candidate():\n root=Path(__file__).parent\n assert (root/'safe-result.txt').read_text()=='before'\n assert (root/'.developer_staging/safe-action/safe-result.txt').read_text()=='after'\n", encoding='utf-8')
    output = root / 'verification'
    output.mkdir(exist_ok=True)
    # Candidate must reside inside the runner write boundary; tested action sources are read-only.
    isolated_candidate = output / 'test_safe_candidate.py'
    isolated_candidate.write_text(candidate.read_text().replace('root=Path(__file__).parent','root=Path(__file__).parent.parent'), encoding='utf-8')
    command = [sys.executable, str(REPO/'tests/run_evidence_tests_isolated.py'), str(output), '--candidate', str(isolated_candidate)]
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError('ISOLATED_CANDIDATE_TEST_FAILED: ' + result.stdout[-3000:] + result.stderr[-1000:])
    import xml.etree.ElementTree as ET
    suites = ET.parse(output/'python-results.xml').getroot()
    suite = suites if suites.tag=='testsuite' else suites.find('testsuite')
    assert suite is not None and int(suite.get('tests'))==1
    assert int(suite.get('failures'))==int(suite.get('errors'))==int(suite.get('skipped'))==0
    sources = ['data/developer_core/change_plan.json','.developer_staging/safe-action/safe-result.txt','safe-result.txt','verification/test_safe_candidate.py']
    digest = lambda path: hashlib.sha256((root/path).read_bytes()).hexdigest()
    bundle = {'artifacts':[{'path':'verification/python-results.xml','sha256':digest('verification/python-results.xml')}]}
    (root/'results.json').write_text(json.dumps(bundle),encoding='utf-8')
    test_id = 'test_safe_candidate'
    criteria = [{'id':f'AC{i}','summary':f'Isolated candidate check {i}; not operational V1 readiness','sources':sources,'tests':[test_id]} for i in range(1,16)]
    run = {'schema_version':1,'run_id':'isolated-safe-action','timestamp':datetime.now(timezone.utc).isoformat(),
           'command':command,'exit_code':result.returncode,'scope':'ISOLATED_CANDIDATE_ONLY',
           'isolation':{key:True for key in ('network_blocked','filesystem_writes_scoped','active_data_blocked','subprocess_blocked','cache_isolated')},
           'results_path':'results.json','results_sha256':digest('results.json'),'counts':{'passed':1,'failed':0,'errors':0},
           'source_sha256':{path:digest(path) for path in sources},
           'criteria':{f'AC{i}':{'status':'PASS','test_ids':[test_id]} for i in range(1,16)}}
    (root/'test-run.json').write_text(json.dumps(run),encoding='utf-8')
    (root/'control-plane').mkdir(exist_ok=True)
    (root/'control-plane/evidence-requirements.json').write_text(json.dumps({'schema_version':1,'criteria':criteria,'test_run_manifest':'test-run.json'}),encoding='utf-8')
    return root


def application(root):
    from fastapi import FastAPI
    from app.api.control_plane import router
    from app.developer_core.controlled_write import ExecutionPaths
    app=FastAPI()
    app.state.runtime_profile='NORMAL'
    app.state.v1_execution_paths=ExecutionPaths.for_root(root)
    app.include_router(router)
    return app
