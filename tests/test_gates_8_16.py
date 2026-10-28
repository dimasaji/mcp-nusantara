from app.reasoning.engine import ReasoningEngine
from app.policy.engine import PolicyEngine
from app.memory.engine import MemoryEngine
from app.action.engine import ActionEngine
from app.orchestration.engine import OrchestrationEngine
from app.core.gate_pipeline import GatePipeline


def test_gate8():

    result = ReasoningEngine().analyze(
        "Bagaimana cara cek status KTP-el?",
        evidence=[
            {
                "document_id": "TEST-KTP",
                "chunk": "Status pengajuan KTP-el dapat diperiksa melalui layanan administrasi kependudukan.",
                "score": 0.90,
            }
        ],
        intent_name="ask_document_status",
        intent_confidence=0.95,
    )

    assert result.status == "grounded"
    assert result.inferences


def test_gate9():

    engine = PolicyEngine()

    allowed = engine.decide(
        action="answer",
        reasoning_status="grounded",
        confidence=0.90,
    )

    assert allowed.allowed is True

    blocked = engine.decide(
        action="delete",
        reasoning_status="grounded",
        confidence=0.90,
    )

    assert blocked.allowed is False


def test_gate10():

    memory = MemoryEngine(max_items_per_session=2)

    memory.remember("test", "user", "one")
    memory.remember("test", "user", "two")
    memory.remember("test", "user", "three")

    assert len(memory.context("test")) == 2


def test_gate11():

    engine = ActionEngine({
        "echo": lambda value: value
    })

    result = engine.execute(
        "echo",
        {"value": "hello"},
    )

    assert result["status"] == "success"
    assert result["result"] == "hello"


def test_gate13():

    engine = OrchestrationEngine()

    result = engine.run(
        session_id="test",
        user_input="hello",
        reasoning={"status": "grounded"},
    )

    assert "reasoning" in result["stages"]


def test_pipeline():

    pipeline = GatePipeline()

    result = pipeline.process(
        session_id="gate-test",
        user_input="Bagaimana cara cek status KTP-el?",
        evidence=[
            {
                "document_id": "TEST-KTP",
                "chunk": "Status pengajuan KTP-el dapat diperiksa melalui layanan administrasi kependudukan.",
                "score": 0.90,
            }
        ],
        intent_name="ask_document_status",
        intent_confidence=0.95,
    )

    assert result["reasoning"]["status"] == "grounded"
    assert result["policy"]["allowed"] is True