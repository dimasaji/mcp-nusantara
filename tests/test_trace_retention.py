import pytest

from app.approval import AuditTrail
from app.experience import EventRecorder
from app.v2.orchestrator import V2Orchestrator


@pytest.mark.asyncio
async def test_trust_receives_generated_claim_and_all_stages_trace(tmp_path):
    claims = []
    recorder = EventRecorder(tmp_path / "events.jsonl")
    def trust(evidence, claim):
        claims.append(claim)
        return {"verification": "unverified"}
    orch = V2Orchestrator(generate=lambda prompt: "generated answer", retrieve=lambda query: [],
                          policy_check=lambda ctx: {"decision": "ALLOW"}, trust_check=trust,
                          recorder=recorder, audit=AuditTrail())
    result = await orch.handle("original question", "session")
    assert claims == ["generated answer"]
    stages = {e.component for e in recorder.events()}
    assert {"policy", "retrieve", "generate", "trust"} <= stages
    assert all(e.request_id == result.request_id for e in recorder.events())


def test_telemetry_retention_does_not_touch_audit(tmp_path):
    audit = tmp_path / "audit.jsonl"
    audit.write_text("preserve audit")
    recorder = EventRecorder(tmp_path / "events.jsonl", max_file_bytes=500, backup_count=2)
    for i in range(20):
        recorder.emit("stage_completed", "retrieve", metadata={"count": i})
    assert len(list(tmp_path.glob("events.jsonl*"))) == 3
    assert audit.read_text() == "preserve audit"
    assert recorder.dropped == 0
