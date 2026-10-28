import pytest

from app.approval import ApprovalQueue, AuditTrail


def test_approval_survives_restart_and_cannot_replay(tmp_path):
    path = tmp_path / "audit.jsonl"
    queue = ApprovalQueue(AuditTrail(path))
    req = queue.submit("tool", {"value": 1}, risk="high", requested_by="requester")
    restarted = ApprovalQueue(AuditTrail(path))
    assert restarted.pending()[0].approval_id == req.approval_id
    restarted.decide(req.approval_id, reviewer="reviewer", decision="approved", reason="reviewed")
    again = ApprovalQueue(AuditTrail(path))
    assert not again.consume(req.approval_id, {"value": 2})
    assert again.consume(req.approval_id, {"value": 1})
    assert not ApprovalQueue(AuditTrail(path)).consume(req.approval_id, {"value": 1})


def test_corrupt_audit_is_not_a_source_of_permission(tmp_path):
    path = tmp_path / "audit.jsonl"
    queue = ApprovalQueue(AuditTrail(path))
    queue.submit("x", {}, risk="low", requested_by="a")
    path.write_text(path.read_text().replace('"pending"', '"approved"'))
    with pytest.raises(Exception, match="integrity"):
        ApprovalQueue(AuditTrail(path))
