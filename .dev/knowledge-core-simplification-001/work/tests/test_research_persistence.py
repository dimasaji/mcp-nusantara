from app.research.improvement import ProposalEngine


def test_proposals_survive_restart_without_reusing_ids(tmp_path):
    path = tmp_path / "proposals.json"
    values = dict(problem="observed failure", evidence=["request-1"], root_cause="identified timeout",
                  proposed_change="bounded worker", affected_components=["model bridge"],
                  test_plan="offline worker regression", rollback_plan="restore previous adapter")
    first = ProposalEngine(path).create(**values)
    restarted = ProposalEngine(path)
    assert restarted.proposals[first.proposal_id].approval_required
    assert restarted.create(**values).proposal_id != first.proposal_id
