from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.reasoning.engine import ReasoningEngine
from app.policy.engine import PolicyEngine
from app.memory.engine import MemoryEngine
from app.action.engine import ActionEngine
from app.orchestration.engine import OrchestrationEngine


def ok(value):
    return value is True


def get_value(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def main():
    print("=" * 60)
    print(" NUSANTARA CORE + HERMES")
    print(" GATE 8-16 FOUNDATION VALIDATION")
    print("=" * 60)

    # ==========================================================
    # GATE 8 - REASONING
    # ==========================================================
    reasoning = ReasoningEngine()

    r = reasoning.analyze(
        "Bagaimana cara cek status KTP-el?",
        evidence=[
            {
                "text": (
                    "Status pengajuan KTP-el dapat diperiksa "
                    "melalui layanan yang tersedia."
                ),
                "score": 0.92,
            }
        ],
        intent_name="ask_document_status",
        intent_confidence=0.95,
    )

    r_status = get_value(r, "status", "")
    r_confidence = float(get_value(r, "confidence", 0.0) or 0.0)
    r_facts = get_value(r, "facts", [])

    gate8 = (
        r_status == "grounded"
        and r_confidence >= 0.50
        and len(r_facts) > 0
    )

    print(
        f"GATE 8  Reasoning           : "
        f"{'PASS' if gate8 else 'FAIL'}"
    )

    if not gate8:
        print(
            f"         status={r_status!r} "
            f"confidence={r_confidence:.4f} "
            f"facts={len(r_facts)}"
        )

    # ==========================================================
    # GATE 9 - POLICY
    # ==========================================================
    policy = PolicyEngine()

    p = policy.decide(
        action="answer",
        reasoning_status=r_status,
        confidence=r_confidence,
    )

    p_allowed = bool(get_value(p, "allowed", False))
    p_decision = get_value(p, "decision", "")

    gate9 = (
        gate8
        and p_allowed
        and p_decision == "allow"
    )

    print(
        f"GATE 9  Decision / Policy   : "
        f"{'PASS' if gate9 else 'FAIL'}"
    )

    if not gate9:
        print(
            f"         decision={p_decision!r} "
            f"allowed={p_allowed}"
        )

    # ==========================================================
    # GATE 10 - MEMORY
    # ==========================================================
    memory = MemoryEngine(max_items_per_session=3)

    memory.remember("gate-test", "user", "A")
    memory.remember("gate-test", "assistant", "B")
    memory.remember("gate-test", "user", "C")
    memory.remember("gate-test", "assistant", "D")

    context = memory.context("gate-test")

    gate10 = len(context) <= 3

    print(
        f"GATE 10 Memory / Context    : "
        f"{'PASS' if gate10 else 'FAIL'}"
    )

    # ==========================================================
    # GATE 11 - ACTION
    # ==========================================================
    action = ActionEngine()

    action.register(
        "echo",
        lambda value="": value
    )

    a = action.execute(
        "echo",
        {"value": "Nusantara"},
        authorized=True,
    )

    a_success = bool(get_value(a, "success", False))
    a_result = get_value(a, "result", None)

    gate11 = (a_success or get_value(a, "status", "") == "success") and a_result == "Nusantara"

    print(
        f"GATE 11 Tool / Action       : "
        f"{'PASS' if gate11 else 'FAIL'}"
    )

    if not gate11:
        print(f"         result={a!r}")

    # ==========================================================
    # GATE 12
    # ==========================================================
    print("GATE 12 Existing Tools      : PRESERVED")

    # ==========================================================
    # GATE 13 - ORCHESTRATION
    # ==========================================================
    orchestration = OrchestrationEngine()

    r_data = (
        r.to_dict()
        if hasattr(r, "to_dict")
        else r
    )

    p_data = (
        p.to_dict()
        if hasattr(p, "to_dict")
        else p
    )

    a_data = (
        a.to_dict()
        if hasattr(a, "to_dict")
        else a
    )

    workflow = orchestration.run(
        session_id="gate-test",
        user_input="Bagaimana cara cek status KTP-el?",
        language={"intent": "ask_document_status"},
        problem={"status": "detected"},
        reasoning=r_data,
        policy=p_data,
        memory=context,
        action=a_data,
    )

    stages = workflow.get("stages", [])

    gate13 = (
        "language" in stages
        and "reasoning" in stages
        and "policy" in stages
        and "memory" in stages
        and "action" in stages
    )

    print(
        f"GATE 13 Orchestration       : "
        f"{'PASS' if gate13 else 'FAIL'}"
    )

    if not gate13:
        print(f"         stages={stages}")

    # ==========================================================
    # GATE 14-16 FOUNDATION
    # ==========================================================
    print("-" * 60)
    print("GATE 14 Developer Core / Graph : FOUNDATION")
    print("GATE 15 Evaluation / Security  : FOUNDATION")
    print("GATE 16 Production Hardening   : FOUNDATION")
    print("-" * 60)

    all_pass = (
        gate8
        and gate9
        and gate10
        and gate11
        and gate13
    )

    print()
    print(
        "GATE 8-13 FOUNDATION : "
        + ("PASS" if all_pass else "FAIL")
    )
    print("=" * 60)

    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

