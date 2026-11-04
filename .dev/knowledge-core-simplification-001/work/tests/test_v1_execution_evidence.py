"""V1 mutation boundary and current evidence approval, isolated filesystem only."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import pytest
from app.core import evidence_registry as registry
from app.developer_core import controlled_write as writer


def test_execution_requires_exact_reviewed_plan_binding(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, 'collect_review_package', lambda root: {
        'package_id': 'p', 'pass_allowed': True, 'evidence': [{'path':'plan', 'validation_status':'VALID'}]})
    path = tmp_path / 'decisions.jsonl'
    binding = {'plan_id':'NORMAL-fixture','version':'a'*64,'action':'CONTROLLED_FILE_WRITE'}
    record = registry.append_decision_audit(path, package_id='p', decision='PASS', notes='',
        reviewer_principal='fixture-reviewer', test_evidence=[], blockers=[], plan_binding=binding)
    args = dict(package_id='p',decision_id=record['decision_id'],required_sources=['plan'])
    assert registry.require_execution_approval(tmp_path,path,**args,plan_binding=binding)['plan_binding']==binding
    for field in binding:
        with pytest.raises(registry.EvidenceRegistryError,match='PLAN_APPROVAL_MISMATCH'):
            registry.require_execution_approval(tmp_path,path,**args,plan_binding={**binding,field:'changed'})


@pytest.mark.parametrize('decision', ['PASS', 'FAIL', 'HOLD'])
def test_latest_human_decision_controls_execution(tmp_path, monkeypatch, decision):
    package = {'package_id': 'package', 'pass_allowed': True, 'evidence': [
        {'path': 'plan.json', 'validation_status': 'VALID'}]}
    monkeypatch.setattr(registry, 'collect_review_package', lambda root: package)
    path = tmp_path / 'decisions.jsonl'
    now = datetime.now(timezone.utc)
    record = registry.append_decision_audit(path, package_id='package', decision=decision, notes='',
        reviewer_principal='fixture-reviewer', test_evidence=['fixture'], blockers=[], timestamp=now.isoformat())
    call = lambda **kw: registry.require_execution_approval(tmp_path, path, package_id='package',
        decision_id=record['decision_id'], required_sources=['plan.json'], **kw)
    if decision == 'PASS':
        assert call(now=now)['decision_id'] == record['decision_id']
        with pytest.raises(registry.EvidenceRegistryError, match='EXPIRED'):
            call(now=now + timedelta(hours=2))
        with pytest.raises(registry.EvidenceRegistryError, match='EXPIRED'):
            call(now=now - timedelta(seconds=1))
        package['package_id'] = 'changed'
        with pytest.raises(registry.EvidenceRegistryError, match='CHANGED'):
            call(now=now)
    else:
        with pytest.raises(registry.EvidenceRegistryError, match='CURRENT_PASS'):
            call(now=now)


def test_pass_revoked_by_hold_and_uncovered_sources_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, 'collect_review_package', lambda root: {
        'package_id': 'p', 'pass_allowed': True, 'evidence': [{'path':'plan', 'validation_status':'VALID'}]})
    path = tmp_path / 'decisions.jsonl'
    def decide(value):
        return registry.append_decision_audit(path, package_id='p', decision=value, notes='',
            reviewer_principal='fixture-reviewer', test_evidence=[], blockers=[])
    passed = decide('PASS')
    with pytest.raises(registry.EvidenceRegistryError, match='SOURCE_NOT_IN'):
        registry.require_execution_approval(tmp_path, path, package_id='p',
            decision_id=passed['decision_id'], required_sources=['unreviewed'])
    decide('HOLD')
    with pytest.raises(registry.EvidenceRegistryError, match='CURRENT_PASS'):
        registry.require_execution_approval(tmp_path, path, package_id='p',
            decision_id=passed['decision_id'], required_sources=['plan'])


@pytest.mark.parametrize('granted', [False, True])
def test_direct_writer_enforces_evidence_before_mutation(tmp_path, monkeypatch, granted):
    monkeypatch.setattr(writer, 'ROOT', tmp_path)
    monkeypatch.setattr(writer, 'AUDIT_FILE', tmp_path / 'audit' / 'execution.json')
    monkeypatch.setattr(writer, 'STAGING', tmp_path / '.developer_staging')
    plan_file = tmp_path / 'plan.json'
    monkeypatch.setattr(writer, 'CHANGE_FILE', plan_file)
    staging = writer.STAGING / 'fixture-change'
    staging.mkdir(parents=True)
    (staging / 'target.txt').write_text('new')
    target = tmp_path / 'target.txt'
    target.write_text('original')
    plan = {'change_id':'fixture-change', 'status':'APPROVED',
        'approval':{'approved':True},
        'write_scope':{'enabled':True}, 'execution':{'shell_execution':False, 'production_write':False},
        'allowed_files':['target.txt']}
    plan_file.write_text(json.dumps(plan))
    authorization = tmp_path / 'authorization.json'
    authorization.write_text(json.dumps({'package_id':'p', 'decision_id':'d'}))
    monkeypatch.setattr(writer, 'AUTHORIZATION_FILE', authorization)
    seen = []
    def authorize(root, audit_path, **kwargs):
        seen.append(kwargs)
        if not granted:
            raise registry.EvidenceRegistryError('EXECUTION_REQUIRES_CURRENT_PASS')
        return {'decision':'PASS'}
    monkeypatch.setattr(registry, 'require_execution_approval', authorize)
    if granted:
        assert writer.execute(plan, staging, [Path('target.txt')]) == ['target.txt']
        assert target.read_text() == 'new'
        with pytest.raises(RuntimeError, match='already consumed'):
            writer.execute(plan, staging, [Path('target.txt')])
    else:
        with pytest.raises(registry.EvidenceRegistryError):
            writer.execute(plan, staging, [Path('target.txt')])
        assert target.read_text() == 'original'
    history = [json.loads(line) for line in writer.AUDIT_FILE.with_suffix('.jsonl').read_text().splitlines()]
    assert history[-1]['result'] == 'BLOCKED'
    if granted:
        assert any(row['result'] == 'PASS' for row in history)
    assert set(seen[0]['required_sources']) == {'plan.json', '.developer_staging/fixture-change/target.txt', 'target.txt'}
    altered = {**plan, 'expected_change':'not reviewed'}
    with pytest.raises(RuntimeError, match='differs'):
        writer.execute(altered, staging, [Path('target.txt')])
    if granted:
        paths=writer.ExecutionPaths(tmp_path,tmp_path/'data',writer.STAGING,plan_file,writer.AUDIT_FILE,authorization)
        assert writer.execution_context(paths)['completed'] is True
        with pytest.raises(RuntimeError,match='EXECUTION_PLAN_ALREADY_COMPLETED'):
            writer.execute(plan,staging,[Path('target.txt')],paths=paths,authorization={'package_id':'p','decision_id':'new-decision'})
