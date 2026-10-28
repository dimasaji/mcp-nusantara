"""Test-only server: real validator/executor on isolated roots, no model/provider."""
import argparse
from pathlib import Path
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v1_execution_fixture import prepare, application
from app.developer_core.controlled_write import ExecutionPaths
from app.core.evidence_registry import append_decision_audit, read_decision_audit
from pydantic import BaseModel
from fastapi import HTTPException, Request

os.environ['NUSANTARA_ADMIN_TOKEN']='fixture-only-review'
os.environ.pop('NUSANTARA_CONTROL_PLANE_READ_ONLY',None)
folder=ROOT/'artifacts/v1-review-e2e'
folder.mkdir(parents=True,exist_ok=True)
app=application(prepare(folder/uuid4().hex))

@app.post('/__fixture/reset')
def reset(request:Request):
    if request.client.host!='127.0.0.1':raise HTTPException(403)
    app.state.v1_execution_paths=ExecutionPaths.for_root(prepare(folder/uuid4().hex))
    return {'scope':'ISOLATED_TEST_ONLY'}

class Scenario(BaseModel):
    operation:str

@app.post('/__fixture/scenario')
def scenario(body:Scenario,request:Request):
    if request.client.host!='127.0.0.1':raise HTTPException(403)
    paths=app.state.v1_execution_paths
    if body.operation=='change_source':
        (paths.staging/'safe-action/safe-result.txt').write_text('unreviewed')
    elif body.operation=='expire':
        audit=paths.data/'control_plane/evidence_decisions.jsonl'
        record=read_decision_audit(audit)[-1]
        append_decision_audit(audit,package_id=record['package_id'],decision='PASS',notes='isolated expiry scenario',reviewer_principal='fixture-reviewer',test_evidence=record['test_evidence'],blockers=[],timestamp=(datetime.now(timezone.utc)-timedelta(hours=2)).isoformat(),plan_binding=record.get('plan_binding'))
    else:raise HTTPException(422)
    return {'scope':'ISOLATED_TEST_ONLY'}

@app.get('/__fixture/result')
def result():
    return {'value':(app.state.v1_execution_paths.root/'safe-result.txt').read_text()}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=9876);args=parser.parse_args()
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=args.port,log_level='warning')
