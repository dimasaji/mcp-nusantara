from app.core.gate_integration import GateIntegration


def test_grounded_gate_8_13():
    engine = GateIntegration()

    result = engine.process(
        session_id="test-grounded",
        user_input="Bagaimana cara cek status KTP-el?",
        evidence=[
            {
                "text": "Status pengajuan KTP-el dapat diperiksa melalui layanan yang tersedia.",
                "score": 0.92,
            }
        ],
        intent_name="ask_document_status",
        intent_confidence=0.95,
        problem=None,
    )

    assert result["reasoning"]["status"] == "grounded"
    assert result["reasoning"]["confidence"] >= 0.50
    assert result["policy"]["allowed"] is True
    assert result["policy"]["decision"] == "allow"
    assert "language" in result["orchestration"]["stages"]
    assert "reasoning" in result["orchestration"]["stages"]
    assert "policy" in result["orchestration"]["stages"]
    assert "memory" in result["orchestration"]["stages"]


def test_no_evidence_is_blocked():
    engine = GateIntegration()

    result = engine.process(
        session_id="test-blocked",
        user_input="Berapa status KTP saya?",
        evidence=[],
        intent_name="ask_document_status",
        intent_confidence=0.90,
        problem=None,
    )

    assert result["reasoning"]["status"] == "insufficient_evidence"
    assert result["policy"]["allowed"] is False
    assert result["policy"]["decision"] == "block"


def test_memory_keeps_conversation():
    engine = GateIntegration()

    engine.process(
        session_id="memory-test",
        user_input="Halo Nusantara",
        evidence=[],
        intent_name="unknown",
        intent_confidence=0.0,
        problem=None,
    )

    memory = engine.memory.context("memory-test")

    assert len(memory) >= 1
    assert any(
        item.get("role") == "user"
        for item in memory
        if isinstance(item, dict)
    )
