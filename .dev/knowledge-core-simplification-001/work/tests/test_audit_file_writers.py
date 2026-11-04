from app.approval.audit_trail import AuditTrail


def test_two_audit_instances_append_one_chain(tmp_path):
    path = tmp_path / 'audit.jsonl'
    first = AuditTrail(path)
    second = AuditTrail(path)
    first.record('first')
    second.record('second')
    first.record('third')
    reloaded = AuditTrail(path)
    assert reloaded.verify()
    assert [e['seq'] for e in reloaded.entries()] == [1, 2, 3]


def test_explicit_recovery_preserves_fork_and_rejects_approval_history(tmp_path):
    import json
    import pytest
    from app.approval.recovery import recover_forked_telemetry
    path = tmp_path / 'audit.jsonl'
    first = AuditTrail()
    one = first.record('policy.decision')
    branch = AuditTrail().record('request.completed')
    path.write_text(json.dumps(one) + '\n' + json.dumps(branch) + '\n')
    original = path.read_bytes()
    result = recover_forked_telemetry(path)
    assert AuditTrail(path).verify()
    assert __import__('pathlib').Path(result['archive']).read_bytes() == original
    assert AuditTrail(path).entries()[0]['data']['approvals_restored'] == 0
    branch = AuditTrail().record('approval.snapshot')
    path.write_text(json.dumps(one) + '\n' + json.dumps(branch) + '\n')
    with pytest.raises(ValueError, match='APPROVAL_HISTORY'):
        recover_forked_telemetry(path)
