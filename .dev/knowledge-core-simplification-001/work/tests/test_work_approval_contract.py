from app.developer_core.controlled_write import ExecutionPaths, prepare_normal_plan, execution_context
from app.core import evidence_registry as registry
from datetime import datetime, timedelta, timezone
import pytest
import json


def test_prepared_work_explains_its_origin_and_review_flow_without_executing(tmp_path):
    paths = ExecutionPaths.for_root(tmp_path)
    context = prepare_normal_plan(paths, objective='Terbitkan panduan', expected_change='Panduan tersedia',
        documents={'docs/panduan.md': 'Isi panduan'}, risk='Perlu peninjauan',
        tests_required=['test_panduan'], rollback='Pulihkan versi sebelumnya')

    assert context['workflow']['version'] == 'nusantara.controlled-work.v1'
    assert [step['id'] for step in context['workflow']['steps']] == [
        'PREPARE', 'VERIFY', 'DECIDE', 'AUTHORIZE', 'EXECUTE', 'AUDIT']
    assert context['plan_origin'] == {'kind': 'DEVELOPER_OPERATION', 'actor_identity': 'NOT_RECORDED'}
    assert context['workflow']['approval_validity_seconds'] == 3600
    assert context['workflow']['approval_executes_work'] is False
    assert not (tmp_path / 'docs/panduan.md').exists()
    assert not (paths.data / 'control_plane/evidence_decisions.jsonl').exists()


def test_approval_expires_after_the_documented_sixty_minute_window(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, 'collect_review_package', lambda root: {
        'package_id': 'package', 'pass_allowed': True,
        'evidence': [{'path': 'plan', 'validation_status': 'VALID'}]})
    now = datetime.now(timezone.utc)
    audit = tmp_path / 'decisions.jsonl'
    decision = registry.append_decision_audit(audit, package_id='package', decision='PASS', notes='',
        reviewer_principal='test-operator', test_evidence=[], blockers=[], timestamp=now.isoformat())
    args = dict(package_id='package', decision_id=decision['decision_id'], required_sources=['plan'])
    assert registry.require_execution_approval(tmp_path, audit, now=now+timedelta(minutes=60), **args)
    with pytest.raises(registry.EvidenceRegistryError, match='APPROVAL_EXPIRED'):
        registry.require_execution_approval(tmp_path, audit, now=now+timedelta(minutes=60, seconds=1), **args)


def test_older_plan_keeps_unknown_origin_without_claiming_a_creator(tmp_path):
    paths = ExecutionPaths.for_root(tmp_path)
    prepare_normal_plan(paths, objective='Panduan', expected_change='Panduan baru',
        documents={'docs/panduan.md': 'Isi'}, risk='LOW', tests_required=['test_panduan'], rollback='Pulihkan')
    plan = json.loads(paths.change_file.read_text())
    plan.pop('origin')
    paths.change_file.write_text(json.dumps(plan))
    context = execution_context(paths)
    assert context['plan_origin'] == {'kind': 'UNKNOWN', 'actor_identity': 'NOT_RECORDED'}
    assert context['workflow']['approval_executes_work'] is False
    assert not (tmp_path / 'docs/panduan.md').exists()
