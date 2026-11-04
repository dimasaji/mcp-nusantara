import json
import pytest
from app.developer_core.controlled_write import ExecutionPaths, prepare_normal_plan, execution_context, validate_plan


def test_normal_plan_prepares_without_human_approval(tmp_path):
    paths = ExecutionPaths.for_root(tmp_path)
    paths.change_file.parent.mkdir(parents=True)
    original = b'{"status":"APPROVAL_REQUIRED"}'
    paths.change_file.write_bytes(original)
    context = prepare_normal_plan(paths, objective='Publier le guide', expected_change='Un nouveau document',
        documents={'docs/guide.md': 'Guide'}, risk='LOW', tests_required=['test_normal_plan_prepares_without_human_approval'],
        rollback='Archiver le nouveau document')
    plan = json.loads(paths.change_file.read_text())
    assert plan['status'] == 'PREPARED' and plan['approval'] == {'required': True, 'approved': False}
    assert not (tmp_path/'docs/guide.md').exists()
    assert any(p.read_bytes() == original for p in (paths.change_file.parent/'plans').glob('*.json'))
    assert not (paths.data/'control_plane/evidence_decisions.jsonl').exists()
    before = context['plan_binding']
    plan['rollback'] = 'Different recovery scope'
    paths.change_file.write_text(json.dumps(plan))
    assert execution_context(paths)['plan_binding'] != before
    (paths.staging/plan['change_id']/'docs/guide.md').write_text('Changed content')
    assert execution_context(paths)['plan_binding'] != before


def test_normal_plan_requires_complete_context_and_safe_targets(tmp_path):
    paths = ExecutionPaths.for_root(tmp_path)
    args = dict(objective='Guide', expected_change='Publish guide', documents={'../escape.txt':'bad'},
                risk='LOW', tests_required=['test'], rollback='Archive')
    with pytest.raises(RuntimeError): prepare_normal_plan(paths, **args)
    args['documents'] = {'docs/guide.md': 'Guide'}
    args['rollback'] = ''
    with pytest.raises(RuntimeError, match='PLAN_INCOMPLETE'): prepare_normal_plan(paths, **args)
    assert not paths.change_file.exists()

