import os
import shutil
import subprocess

import pytest

from app.approval import ApprovalQueue, AuditTrail
from app.approval.change_request import ReviewWorkflow
from app.improvement.gate import GateBlocked, create_review_branch
from app.research.improvement import ProposalEngine


def test_git_branch_requires_durable_approved_payload(tmp_path):
    git = os.getenv("NUSANTARA_TEST_GIT") or shutil.which("git")
    if not git:
        pytest.skip("Git executable required for actual branch integration")
    repo = tmp_path / "repo"
    repo.mkdir()
    def cmd(*args):
        return subprocess.run([git, "-C", str(repo), *args], check=True, capture_output=True, text=True)
    cmd("init")
    cmd("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "baseline")
    proposal = ProposalEngine().create(problem="timeout", evidence=["test-1"], root_cause="blocking worker",
               proposed_change="timeout", affected_components=["bridge"], test_plan="regression", rollback_plan="restore")
    queue = ApprovalQueue(AuditTrail(tmp_path / "audit.jsonl"))
    workflow = ReviewWorkflow(queue)
    approval = workflow.submit(proposal, "requester")
    queue.decide(approval.approval_id, reviewer="reviewer", decision="approved", reason="fixture decision")
    cr = workflow.open_change_request(approval.approval_id, proposal)
    branch = create_review_branch(repo, cr, proposal, "measured-baseline", queue, git)
    assert branch in cmd("branch", "--list").stdout
    assert cmd("branch", "--show-current").stdout.strip() != branch
    proposal.proposed_change = "changed after review"
    with pytest.raises(GateBlocked):
        create_review_branch(repo, cr, proposal, "measured-baseline", queue, git)
