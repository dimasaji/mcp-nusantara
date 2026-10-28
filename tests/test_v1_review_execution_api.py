"""Real HTTP API, real isolated evidence validator, real executor and persistent history."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.core.evidence_registry import append_decision_audit
from v1_execution_fixture import prepare, application

@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN','isolated-test-credential')
    monkeypatch.delenv('NUSANTARA_CONTROL_PLANE_READ_ONLY',raising=False)
    root=prepare(tmp_path)
    with TestClient(application(root),base_url='http://127.0.0.1:8765',client=('127.0.0.1',1234)) as client:
        client.headers.update({'X-Admin-Token':'isolated-test-credential'})
        yield root,client

@pytest.mark.parametrize('case',['PASS','FAIL','HOLD','none','expired','different_evidence','changed_source'])
def test_review_governance_executor_history(environment,case):
    root,c=environment
    package=c.get('/v1/control-plane/evidence-package').json()
    assert package['pass_allowed'] is True
    context=c.get('/v1/control-plane/execution-context').json()
    assert context['target_files']==['safe-result.txt']
    decision_id='dec_'+'0'*32
    if case!='none':
        decision=case if case in {'PASS','FAIL','HOLD'} else 'PASS'
        if case=='expired':
            record=append_decision_audit(root/'data/control_plane/evidence_decisions.jsonl',package_id=package['package_id'],decision='PASS',notes='',reviewer_principal='isolated-reviewer',test_evidence=['test_safe_candidate'],blockers=[],timestamp=(datetime.now(timezone.utc)-timedelta(hours=2)).isoformat(),plan_binding=context['plan_binding'])
        else:
            response=c.post('/v1/control-plane/decisions',json={'package_id':package['package_id'],'decision':decision,'notes':'','plan_binding':context['plan_binding']})
            assert response.status_code==200,response.text
            record=response.json()
        decision_id=record['decision_id']
    if case=='changed_source':
        (root/'.developer_staging/safe-action/safe-result.txt').write_text('unreviewed')
    sent_package='evp_sha256_'+'0'*64 if case=='different_evidence' else package['package_id']
    response=c.post('/v1/control-plane/execute-reviewed',json={'package_id':sent_package,'decision_id':decision_id})
    assert response.status_code==(200 if case=='PASS' else 409),response.text
    assert (root/'safe-result.txt').read_text()==('after' if case=='PASS' else 'before')
    history=c.get('/v1/control-plane/history')
    assert history.status_code==200
    body=history.json()
    assert body['decision_audit']=='VALIDATED_HASH_CHAIN'
    assert len(body['decisions'])==(0 if case=='none' else 1)
    assert body['executions'][-1]['result']==('PASS' if case=='PASS' else 'BLOCKED')
    assert body['executions'][-1]['decision_id']==decision_id
    assert body['executions'][-1]['package_id']==sent_package
    if case=='expired':assert body['executions'][-1]['reason']=='EXECUTION_APPROVAL_EXPIRED'
    if case in {'changed_source','different_evidence'}:assert body['executions'][-1]['reason']=='EXECUTION_EVIDENCE_INVALID_OR_CHANGED'
    # Reloaded app reads the same durable decisions and execution history.
    with TestClient(application(root),base_url='http://127.0.0.1:8765',client=('127.0.0.1',1234)) as reloaded:
        assert reloaded.get('/v1/control-plane/history',headers={'X-Admin-Token':'isolated-test-credential'}).json()==body
    if case=='changed_source':
        current=c.get('/v1/control-plane/evidence-package').json()
        assert current['pass_allowed'] is False and current['package_id']!=package['package_id']
        assert any(item['reason']=='TEST_SOURCE_CHANGED_AFTER_RUN' for item in current['blockers'])


def test_unauthorized_execution_does_not_write(environment):
    root,c=environment
    response=c.post('/v1/control-plane/execute-reviewed',headers={'X-Admin-Token':'wrong'},json={'package_id':'evp_sha256_'+'0'*64,'decision_id':'dec_'+'0'*32})
    assert response.status_code==403 and (root/'safe-result.txt').read_text()=='before'


def test_operation_summary_stops_requesting_review_after_completion(environment):
    root,c=environment
    path='/v1/control-plane/operations-summary'
    assert c.get(path,headers={'X-Admin-Token':'wrong'}).status_code==403
    before=c.get(path)
    assert before.status_code==200
    assert before.json()['pending_work']==1
    context=c.get('/v1/control-plane/execution-context').json()
    package=c.get('/v1/control-plane/evidence-package').json()
    append_decision_audit(root/'data/control_plane/evidence_decisions.jsonl',package_id=package['package_id'],decision='PASS',notes='isolated expired review',reviewer_principal='isolated-reviewer',test_evidence=['test_safe_candidate'],blockers=[],timestamp=(datetime.now(timezone.utc)-timedelta(hours=2)).isoformat(),plan_binding=context['plan_binding'])
    assert c.get(path).json()['pending_review']==1
    record=c.post('/v1/control-plane/decisions',json={'package_id':package['package_id'],'decision':'PASS','plan_binding':context['plan_binding']}).json()
    assert c.post('/v1/control-plane/execute-reviewed',json={'package_id':package['package_id'],'decision_id':record['decision_id']}).status_code==200
    after=c.get(path).json()
    assert after['pending_work']==0
    assert after['pending_review']==0
    assert after['tasks'][0]['status']=='SUCCEEDED'


def test_unbound_pass_does_not_authorize_action(environment):
    root,c=environment
    package=c.get('/v1/control-plane/evidence-package').json()
    record=c.post('/v1/control-plane/decisions',json={'package_id':package['package_id'],'decision':'PASS'}).json()
    response=c.post('/v1/control-plane/execute-reviewed',json={'package_id':package['package_id'],'decision_id':record['decision_id']})
    assert response.status_code==409
    assert (root/'safe-result.txt').read_text()=='before'
    assert c.get('/v1/control-plane/history').json()['executions'][-1]['reason']=='EXECUTION_PLAN_APPROVAL_MISMATCH'


def test_changed_plan_cannot_receive_stale_ui_approval(environment):
    root,c=environment
    package=c.get('/v1/control-plane/evidence-package').json()
    binding=c.get('/v1/control-plane/execution-context').json()['plan_binding']
    binding['version']='0'*64
    response=c.post('/v1/control-plane/decisions',json={'package_id':package['package_id'],'decision':'PASS','plan_binding':binding})
    assert response.status_code==409
    assert c.get('/v1/control-plane/history').json()['decisions']==[]


def test_plan_changed_after_approval_is_rejected_and_recorded(environment):
    import json
    root,c=environment
    package=c.get('/v1/control-plane/evidence-package').json()
    binding=c.get('/v1/control-plane/execution-context').json()['plan_binding']
    record=c.post('/v1/control-plane/decisions',json={'package_id':package['package_id'],'decision':'PASS','plan_binding':binding}).json()
    path=root/'data/developer_core/change_plan.json'
    plan=json.loads(path.read_text());plan['expected_change']='Unreviewed action scope';path.write_text(json.dumps(plan))
    response=c.post('/v1/control-plane/execute-reviewed',json={'package_id':package['package_id'],'decision_id':record['decision_id']})
    assert response.status_code==409
    assert (root/'safe-result.txt').read_text()=='before'
    assert c.get('/v1/control-plane/history').json()['executions'][-1]['reason']=='EXECUTION_EVIDENCE_INVALID_OR_CHANGED'


def test_copy_failure_is_persisted_and_cannot_reuse_approval(environment,monkeypatch):
    from app.developer_core import controlled_write
    root,c=environment
    package=c.get('/v1/control-plane/evidence-package').json()
    binding=c.get('/v1/control-plane/execution-context').json()['plan_binding']
    record=c.post('/v1/control-plane/decisions',json={'package_id':package['package_id'],'decision':'PASS','plan_binding':binding}).json()
    def fail_copy(*args,**kwargs):raise OSError('isolated copy failure')
    monkeypatch.setattr(controlled_write.shutil,'copy2',fail_copy)
    body={'package_id':package['package_id'],'decision_id':record['decision_id']}
    assert c.post('/v1/control-plane/execute-reviewed',json=body).status_code==409
    events=c.get('/v1/control-plane/history').json()['executions']
    assert [e['result'] for e in events]==['AUTHORIZED_ATTEMPT','BLOCKED']
    assert events[-1]['reason']=='OSError'
    assert c.post('/v1/control-plane/execute-reviewed',json=body).status_code==409
    assert c.get('/v1/control-plane/history').json()['executions'][-1]['reason']=='EXECUTION_DECISION_ALREADY_CONSUMED'
    assert (root/'safe-result.txt').read_text()=='before'


def test_latest_hold_revokes_pass_without_erasing_history(environment):
    root,c=environment
    package=c.get('/v1/control-plane/evidence-package').json()
    binding=c.get('/v1/control-plane/execution-context').json()['plan_binding']
    records=[]
    for decision in ('PASS','HOLD'):
        response=c.post('/v1/control-plane/decisions',json={'package_id':package['package_id'],'decision':decision,'plan_binding':binding})
        assert response.status_code==200
        records.append(response.json())
    body={'package_id':package['package_id'],'decision_id':records[0]['decision_id']}
    assert c.post('/v1/control-plane/execute-reviewed',json=body).status_code==409
    history=c.get('/v1/control-plane/history').json()
    assert [r['decision'] for r in history['decisions']]==['PASS','HOLD']
    assert history['executions'][-1]['reason']=='EXECUTION_REQUIRES_CURRENT_PASS'
    assert (root/'safe-result.txt').read_text()=='before'


@pytest.mark.parametrize('profile',['ATTESTATION','EVIDENCE_ONLY'])
def test_other_runtime_profiles_cannot_reach_v1_mutation(environment,monkeypatch,profile):
    root,c=environment
    if profile=='ATTESTATION':c.app.state.runtime_profile=profile
    else:monkeypatch.setenv('NUSANTARA_CONTROL_PLANE_READ_ONLY','1')
    response=c.post('/v1/control-plane/execute-reviewed',json={'package_id':'evp_sha256_'+'0'*64,'decision_id':'dec_'+'0'*32})
    assert response.status_code==403
    assert (root/'safe-result.txt').read_text()=='before'
