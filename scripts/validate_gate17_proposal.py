from __future__ import annotations

import inspect
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.research.improvement import Proposal, ProposalEngine


class Gate174Error(ValueError):
    pass


class ImprovementProposalAdapter:
    """
    Gate 17.4 adapter terhadap ProposalEngine existing.

    Tidak membuat ProposalEngine baru.
    Tidak melakukan production mutation.
    """

    def __init__(self) -> None:
        self.engine = ProposalEngine()

    def create_from_analysis(
        self,
        *,
        gap: dict,
        evidence: list[dict],
        root_cause: dict,
        proposed_change: str,
        affected_components: list[str],
        affected_files: list[str],
        risk: str,
        expected_benefit: str,
        experiment_result: str,
        test_plan: list[str],
        rollback_plan: str,
    ) -> Proposal:

        self._validate_input(
            gap=gap,
            evidence=evidence,
            root_cause=root_cause,
            proposed_change=proposed_change,
            affected_components=affected_components,
            affected_files=affected_files,
            risk=risk,
            expected_benefit=expected_benefit,
            experiment_result=experiment_result,
            test_plan=test_plan,
            rollback_plan=rollback_plan,
        )

        evidence_text = [
            self._evidence_to_text(item)
            for item in evidence
        ]

        experiment = {
            "verdict": experiment_result,
            "source": "gate17.4",
        }

        return self.engine.create(
            problem=gap["description"],
            evidence=evidence_text,
            root_cause=root_cause["selected_cause"],
            proposed_change=proposed_change,
            affected_components=affected_components,
            affected_files=affected_files,
            risk=risk,
            expected_benefit=expected_benefit,
            experiment_result=experiment,
            test_plan="; ".join(test_plan),
            rollback_plan=rollback_plan,
        )

    @staticmethod
    def _evidence_to_text(item: dict) -> str:
        if not isinstance(item, dict):
            raise Gate174Error(
                "evidence item harus dictionary"
            )

        evidence_id = item.get("evidence_id", "")
        source = item.get("source", "")
        evidence_type = item.get("evidence_type", "")
        data = item.get("data", {})

        if not evidence_id:
            raise Gate174Error(
                "evidence_id wajib"
            )

        return (
            f"{evidence_id} | "
            f"source={source} | "
            f"type={evidence_type} | "
            f"data={json.dumps(data, sort_keys=True, default=str)}"
        )

    @staticmethod
    def _validate_input(
        *,
        gap,
        evidence,
        root_cause,
        proposed_change,
        affected_components,
        affected_files,
        risk,
        expected_benefit,
        experiment_result,
        test_plan,
        rollback_plan,
    ) -> None:

        if not isinstance(gap, dict):
            raise Gate174Error("gap harus dictionary")

        if not gap.get("gap_id"):
            raise Gate174Error("gap_id wajib")

        if not gap.get("description"):
            raise Gate174Error(
                "gap description wajib"
            )

        if not evidence:
            raise Gate174Error(
                "evidence wajib"
            )

        if not root_cause:
            raise Gate174Error(
                "root_cause wajib"
            )

        if not root_cause.get("selected_cause"):
            raise Gate174Error(
                "selected_cause wajib"
            )

        if not proposed_change.strip():
            raise Gate174Error(
                "proposed_change wajib"
            )

        if not affected_components:
            raise Gate174Error(
                "affected_components wajib"
            )

        if not affected_files:
            raise Gate174Error(
                "affected_files wajib"
            )

        if not risk.strip():
            raise Gate174Error(
                "risk wajib"
            )

        if not expected_benefit.strip():
            raise Gate174Error(
                "expected_benefit wajib"
            )

        if not experiment_result.strip():
            raise Gate174Error(
                "experiment_result wajib"
            )

        if not test_plan:
            raise Gate174Error(
                "test_plan wajib"
            )

        if not rollback_plan.strip():
            raise Gate174Error(
                "rollback_plan wajib"
            )


def sample_gap() -> dict:
    return {
        "gap_id": "GAP-0001",
        "component": "KnowledgeEngine",
        "description": (
            "Relevant evidence tidak masuk top-k"
        ),
        "gap_type": "retrieval",
        "severity": "medium",
    }


def sample_evidence() -> list[dict]:
    return [
        {
            "evidence_id": "EVD-001",
            "source": "evaluation",
            "evidence_type": "retrieval",
            "data": {
                "expected": "KTP-el",
                "retrieved": False,
            },
        },
        {
            "evidence_id": "EVD-002",
            "source": "runtime",
            "evidence_type": "trace",
            "data": {
                "top_k": 5,
                "relevant_hits": 0,
            },
        },
    ]


def sample_root_cause() -> dict:
    return {
        "analysis_id": "RCA-0001",
        "selected_cause": (
            "retrieval ranking kurang tepat"
        ),
        "confidence": 0.82,
        "evidence_ids": [
            "EVD-001",
            "EVD-002",
        ],
    }


def sample_kwargs() -> dict:
    return {
        "gap": sample_gap(),
        "evidence": sample_evidence(),
        "root_cause": sample_root_cause(),
        "proposed_change": (
            "Evaluasi ulang bobot semantic dan lexical "
            "retrieval menggunakan benchmark RAG."
        ),
        "affected_components": [
            "KnowledgeEngine",
            "SemanticRetriever",
        ],
        "affected_files": [
            "app/knowledge/production_semantic_retriever.py",
        ],
        "risk": "medium",
        "expected_benefit": (
            "Meningkatkan relevansi evidence retrieval."
        ),
        "experiment_result": "NO_CHANGE",
        "test_plan": [
            "run retrieval benchmark",
            "run grounding evaluation",
            "run regression gate",
        ],
        "rollback_plan": (
            "Restore approved target files "
            "menggunakan snapshot Gate 16."
        ),
    }


passed = 0
failed = 0


def check(name: str, fn) -> None:
    global passed, failed

    try:
        fn()
        print(f"[PASS] {name}")
        passed += 1
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
        failed += 1


adapter = ImprovementProposalAdapter()


def valid_proposal():
    proposal = adapter.create_from_analysis(
        **sample_kwargs()
    )

    assert isinstance(proposal, Proposal)
    assert proposal.problem
    assert proposal.evidence
    assert proposal.root_cause
    assert proposal.proposed_change


def gap_binding():
    kwargs = sample_kwargs()

    proposal = adapter.create_from_analysis(
        **kwargs
    )

    assert proposal.problem == (
        kwargs["gap"]["description"]
    )


def evidence_required():
    kwargs = sample_kwargs()
    kwargs["evidence"] = []

    try:
        adapter.create_from_analysis(**kwargs)
    except Gate174Error:
        return

    raise AssertionError(
        "Proposal tanpa evidence diterima"
    )


def root_cause_required():
    kwargs = sample_kwargs()
    kwargs["root_cause"] = {}

    try:
        adapter.create_from_analysis(**kwargs)
    except Gate174Error:
        return

    raise AssertionError(
        "Proposal tanpa root cause diterima"
    )


def affected_components_required():
    kwargs = sample_kwargs()
    kwargs["affected_components"] = []

    try:
        adapter.create_from_analysis(**kwargs)
    except Gate174Error:
        return

    raise AssertionError(
        "Proposal tanpa affected components diterima"
    )


def affected_files_required():
    kwargs = sample_kwargs()
    kwargs["affected_files"] = []

    try:
        adapter.create_from_analysis(**kwargs)
    except Gate174Error:
        return

    raise AssertionError(
        "Proposal tanpa affected files diterima"
    )


def risk_required():
    kwargs = sample_kwargs()
    kwargs["risk"] = ""

    try:
        adapter.create_from_analysis(**kwargs)
    except Gate174Error:
        return

    raise AssertionError(
        "Proposal tanpa risk diterima"
    )


def test_plan_required():
    kwargs = sample_kwargs()
    kwargs["test_plan"] = []

    try:
        adapter.create_from_analysis(**kwargs)
    except Gate174Error:
        return

    raise AssertionError(
        "Proposal tanpa test plan diterima"
    )


def rollback_required():
    kwargs = sample_kwargs()
    kwargs["rollback_plan"] = ""

    try:
        adapter.create_from_analysis(**kwargs)
    except Gate174Error:
        return

    raise AssertionError(
        "Proposal tanpa rollback plan diterima"
    )


def regression_rejected():
    kwargs = sample_kwargs()
    kwargs["experiment_result"] = "REGRESSION"

    try:
        adapter.create_from_analysis(**kwargs)
    except Exception:
        return

    raise AssertionError(
        "Proposal REGRESSION diterima"
    )


def approval_required_enforced():
    proposal = adapter.create_from_analysis(
        **sample_kwargs()
    )

    assert proposal.approval_required is True


def deterministic_payload():
    a = adapter.create_from_analysis(
        **sample_kwargs()
    )

    b = adapter.create_from_analysis(
        **sample_kwargs()
    )

    assert a.problem == b.problem
    assert a.evidence == b.evidence
    assert a.root_cause == b.root_cause
    assert a.proposed_change == b.proposed_change


def serializable():
    proposal = adapter.create_from_analysis(
        **sample_kwargs()
    )

    payload = {
        "problem": proposal.problem,
        "evidence": proposal.evidence,
        "root_cause": proposal.root_cause,
        "proposed_change": proposal.proposed_change,
        "affected_components":
            proposal.affected_components,
        "affected_files":
            proposal.affected_files,
        "risk": proposal.risk,
        "expected_benefit":
            proposal.expected_benefit,
        "experiment_result":
            proposal.experiment_result,
        "test_plan":
            proposal.test_plan,
        "rollback_plan":
            proposal.rollback_plan,
        "approval_required":
            proposal.approval_required,
    }

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )

    assert encoded


def no_production_mutation():
    source = Path(
        __file__
    ).read_text(encoding="utf-8")

    forbidden = [
        "os.system(",
        "os.popen(",
        "os.spawn",
        "os.exec",
        "subprocess.run(",
        "subprocess.Popen(",
        "subprocess.call(",
        "subprocess.check_call(",
        "subprocess.check_output(",
    ]

    # Abaikan teks pemeriksaan itu sendiri.
    lines = []

    for line in source.splitlines():
        stripped = line.strip()

        if stripped.startswith(
            "#"
        ):
            continue

        if stripped.startswith(
            '"'
        ) or stripped.startswith(
            "'"
        ):
            continue

        lines.append(line)

    runtime_source = "\n".join(lines)

    for pattern in forbidden:
        if pattern in runtime_source:
            raise AssertionError(
                "Forbidden execution primitive: "
                + pattern
            )


print("=" * 72)
print("NUSANTARA GATE 17.4")
print("IMPROVEMENT PROPOSAL CONTRACT")
print("=" * 72)

check(
    "17.4.1 Valid proposal",
    valid_proposal,
)

check(
    "17.4.2 Gap -> proposal binding",
    gap_binding,
)

check(
    "17.4.3 Evidence required",
    evidence_required,
)

check(
    "17.4.4 Root cause required",
    root_cause_required,
)

check(
    "17.4.5 Affected components required",
    affected_components_required,
)

check(
    "17.4.6 Affected files required",
    affected_files_required,
)

check(
    "17.4.7 Risk required",
    risk_required,
)

check(
    "17.4.8 Test plan required",
    test_plan_required,
)

check(
    "17.4.9 Rollback plan required",
    rollback_required,
)

check(
    "17.4.10 REGRESSION rejected",
    regression_rejected,
)

check(
    "17.4.11 approval_required enforced",
    approval_required_enforced,
)

check(
    "17.4.12 Deterministic proposal",
    deterministic_payload,
)

check(
    "17.4.13 Payload serializable",
    serializable,
)

check(
    "17.4.14 No production mutation",
    no_production_mutation,
)

print("-" * 72)
print(f"VALIDATION CHECKS : {passed + failed}")
print(f"PASS              : {passed}")
print(f"FAIL              : {failed}")
print("-" * 72)

if failed == 0:
    print("GATE 17.4 FINAL   : PASS")
    print("PRODUCTION WRITE  : NOT ENABLED")
    print("EXECUTION         : NOT ENABLED")
    print("APPROVAL          : REQUIRED")
else:
    print("GATE 17.4 FINAL   : FAIL")
    raise SystemExit(1)

print("=" * 72)
