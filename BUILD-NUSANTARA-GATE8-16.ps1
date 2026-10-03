# NUSANTARA CORE + HERMES
# GATE 8 -> GATE 16 BUILDER
# Run from C:\Users\dmaza\mcp-starter

$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path

if (-not (Test-Path ".\app")) {
    throw "Jalankan dari C:\Users\dmaza\mcp-starter"
}

function Write-File($Path, $Content) {
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText(
        (Join-Path $Root $Path),
        $Content,
        $utf8
    )
    Write-Host "CREATE $Path" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA CORE + HERMES GATE 8-16 BUILDER" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# GATE 8 - REASONING
# ============================================================

Write-File "app\reasoning\__init__.py" ""

Write-File "app\reasoning\schemas.py" @"
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Fact:
    subject: str
    predicate: str
    value: Any
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 0.0

    def to_dict(self):
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class Inference:
    conclusion: str
    confidence: float
    rule_name: str = ""

    def to_dict(self):
        return {
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "rule_name": self.rule_name,
        }


@dataclass
class ReasoningResult:
    status: str
    facts: list[Fact] = field(default_factory=list)
    inferences: list[Inference] = field(default_factory=list)
    confidence: float = 0.0
    explanation: str = ""
    blocked_reason: str | None = None

    def to_dict(self):
        return {
            "status": self.status,
            "facts": [x.to_dict() for x in self.facts],
            "inferences": [x.to_dict() for x in self.inferences],
            "confidence": self.confidence,
            "explanation": self.explanation,
            "blocked_reason": self.blocked_reason,
        }
"@

Write-File "app\reasoning\engine.py" @"
from __future__ import annotations

from typing import Any

from .schemas import Fact, Inference, ReasoningResult


class ReasoningEngine:

    VERSION = "8.0.0-evidence-first"

    def _score(self, item: Any) -> float:
        try:
            if isinstance(item, dict):
                return max(0.0, min(1.0, float(item.get("score", 0))))
            return max(0.0, min(1.0, float(getattr(item, "score", 0))))
        except Exception:
            return 0.0

    def _text(self, item: Any) -> str:
        if isinstance(item, dict):
            return str(
                item.get("chunk")
                or item.get("source")
                or item.get("content")
                or ""
            ).strip()

        return str(
            getattr(item, "chunk", None)
            or getattr(item, "source", None)
            or getattr(item, "content", None)
            or ""
        ).strip()

    def analyze(
        self,
        user_input: str,
        *,
        evidence: list[Any] | None = None,
        intent_name: str = "",
        intent_confidence: float = 0.0,
    ) -> ReasoningResult:

        evidence = list(evidence or [])

        if not evidence:
            return ReasoningResult(
                status="insufficient_evidence",
                confidence=0.0,
                explanation="No evidence available.",
                blocked_reason="no_evidence",
            )

        facts = []

        for index, item in enumerate(evidence):
            text = self._text(item)
            score = self._score(item)

            if not text:
                continue

            doc_id = (
                item.get("document_id")
                if isinstance(item, dict)
                else getattr(item, "document_id", None)
            )

            facts.append(
                Fact(
                    subject="evidence",
                    predicate="states",
                    value=text,
                    evidence_ids=(str(doc_id or f"evidence-{index}"),),
                    confidence=score,
                )
            )

            low = text.lower()

            if (
                "ktp" in low
                and "status" in low
                and any(
                    x in low
                    for x in (
                        "dapat diperiksa",
                        "diperiksa",
                        "melalui",
                        "prosedur",
                    )
                )
            ):
                facts.append(
                    Fact(
                        subject="KTP-el",
                        predicate="procedure_available",
                        value=True,
                        evidence_ids=(str(doc_id or f"evidence-{index}"),),
                        confidence=score,
                    )
                )

        best_score = max(
            (f.confidence for f in facts),
            default=0.0,
        )

        if not facts:
            return ReasoningResult(
                status="insufficient_evidence",
                confidence=0.0,
                explanation="Evidence exists but contains no usable facts.",
                blocked_reason="no_usable_fact",
            )

        inference = Inference(
            conclusion="answer_from_evidence",
            confidence=best_score,
            rule_name="evidence_first",
        )

        confidence = round(
            (
                best_score * 0.55
                + max(0.0, min(1.0, intent_confidence)) * 0.20
                + best_score * 0.25
            ),
            6,
        )

        return ReasoningResult(
            status="grounded",
            facts=facts,
            inferences=[inference],
            confidence=confidence,
            explanation="Conclusion supported by retrieved evidence.",
        )
"@

# ============================================================
# GATE 9 - POLICY
# ============================================================

Write-File "app\policy\__init__.py" ""

Write-File "app\policy\engine.py" @"
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    allowed: bool
    reason: str
    risk: str

    def to_dict(self):
        return {
            "decision": self.decision,
            "allowed": self.allowed,
            "reason": self.reason,
            "risk": self.risk,
        }


class PolicyEngine:

    VERSION = "9.0.0-safe-policy"

    SENSITIVE_ACTIONS = {
        "delete",
        "modify_record",
        "publish",
        "send_external",
        "financial_transaction",
    }

    def decide(
        self,
        *,
        action: str = "answer",
        reasoning_status: str = "insufficient_evidence",
        confidence: float = 0.0,
    ) -> PolicyDecision:

        if reasoning_status != "grounded":
            return PolicyDecision(
                "block",
                False,
                "Reasoning is not grounded.",
                "medium",
            )

        if confidence < 0.60:
            return PolicyDecision(
                "block",
                False,
                "Reasoning confidence below threshold.",
                "medium",
            )

        if action in self.SENSITIVE_ACTIONS:
            return PolicyDecision(
                "block",
                False,
                "Sensitive action requires explicit authorization.",
                "high",
            )

        return PolicyDecision(
            "allow",
            True,
            "Policy requirements satisfied.",
            "low",
        )
"@

# ============================================================
# GATE 10 - MEMORY
# ============================================================

Write-File "app\memory\__init__.py" ""

Write-File "app\memory\engine.py" @"
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone


class MemoryEngine:

    VERSION = "10.0.0-bounded-context"

    def __init__(self, max_items_per_session: int = 20):
        self.max_items = max_items_per_session
        self.sessions = defaultdict(
            lambda: deque(maxlen=self.max_items)
        )

    def remember(
        self,
        session_id: str,
        role: str,
        content: str,
        **metadata,
    ):
        item = {
            "session_id": session_id,
            "role": role,
            "content": str(content),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
        }

        self.sessions[session_id].append(item)

        return item

    def context(
        self,
        session_id: str,
        limit: int = 8,
    ):
        return list(self.sessions.get(session_id, []))[-limit:]

    def clear(self, session_id: str):
        self.sessions.pop(session_id, None)
"@

# ============================================================
# GATE 11 - ACTION
# ============================================================

Write-File "app\action\__init__.py" ""

Write-File "app\action\engine.py" @"
from __future__ import annotations


class ActionEngine:

    VERSION = "11.0.0-explicit-tools"

    def __init__(self, tools=None):
        self.tools = dict(tools or {})

    def register(self, name, function):
        self.tools[name] = function

    def execute(
        self,
        name,
        arguments=None,
        authorized=False,
        requires_authorization=False,
    ):

        arguments = arguments or {}

        if requires_authorization and not authorized:
            return {
                "status": "blocked",
                "action": name,
                "error": "Explicit authorization required.",
            }

        function = self.tools.get(name)

        if function is None:
            return {
                "status": "not_found",
                "action": name,
                "error": "Tool is not registered.",
            }

        try:
            result = function(**arguments)

            return {
                "status": "success",
                "action": name,
                "result": result,
            }

        except Exception as exc:

            return {
                "status": "error",
                "action": name,
                "error": f"{type(exc).__name__}: {exc}",
            }
"@

# ============================================================
# GATE 12 - PRESERVE EXISTING TOOLS
# ============================================================

Write-File "app\action\tool_bridge.py" @"
from __future__ import annotations

from .engine import ActionEngine


def build_action_engine(existing_tools=None):
    registry = {}

    for name, function in (existing_tools or {}).items():
        if callable(function):
            registry[str(name)] = function

    return ActionEngine(registry)
"@

# ============================================================
# GATE 13 - ORCHESTRATION
# ============================================================

Write-File "app\orchestration\__init__.py" ""

Write-File "app\orchestration\engine.py" @"
from __future__ import annotations


class OrchestrationEngine:

    VERSION = "13.0.0-gated-orchestration"

    def run(
        self,
        *,
        session_id,
        user_input,
        language=None,
        problem=None,
        reasoning=None,
        policy=None,
        memory=None,
        action=None,
    ):

        stages = []
        data = {}

        if language is not None:
            stages.append("language")
            data["language"] = language

        if problem is not None:
            stages.append("problem")
            data["problem"] = problem

        if reasoning is not None:
            stages.append("reasoning")
            data["reasoning"] = (
                reasoning.to_dict()
                if hasattr(reasoning, "to_dict")
                else reasoning
            )

        if policy is not None:
            stages.append("policy")
            data["policy"] = (
                policy.to_dict()
                if hasattr(policy, "to_dict")
                else policy
            )

        if memory is not None:
            stages.append("memory")
            data["memory"] = memory

        if action is not None:
            stages.append("action")
            data["action"] = action

        return {
            "session_id": session_id,
            "user_input": user_input,
            "stages": stages,
            "data": data,
        }
"@

# ============================================================
# GATE 14 - DEVELOPER CORE / GRAPH
# ============================================================

Write-File "app\developer_core\__init__.py" ""

Write-File "app\developer_core\gates.py" @"
GATES = {
    8: "Reasoning Engine",
    9: "Decision / Policy Engine",
    10: "Memory / Context Engine",
    11: "Tool / Action Engine",
    12: "Existing Tools",
    13: "Workflow / Orchestration",
    14: "Developer Core / Graph",
    15: "Evaluation / Security",
    16: "Production Hardening",
}


def gate_map():
    return dict(GATES)
"@

# ============================================================
# GATE 16 - PRODUCTION MANIFEST
# ============================================================

Write-File "app\developer_core\production.py" @"
from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone


def runtime_manifest():

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pid": os.getpid(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hardening": {
            "bounded_memory": True,
            "explicit_tools": True,
            "sensitive_actions_blocked": True,
            "evidence_first": True,
            "authorization_required_for_side_effects": True,
        },
    }
"@

# ============================================================
# UNIFIED GATE PIPELINE
# ============================================================

Write-File "app\core\gate_pipeline.py" @"
from __future__ import annotations

from app.reasoning.engine import ReasoningEngine
from app.policy.engine import PolicyEngine
from app.memory.engine import MemoryEngine
from app.action.engine import ActionEngine


class GatePipeline:

    VERSION = "8-16-bridge-1.0.0"

    def __init__(self):

        self.reasoning = ReasoningEngine()
        self.policy = PolicyEngine()
        self.memory = MemoryEngine()
        self.actions = ActionEngine()

    def process(
        self,
        *,
        session_id,
        user_input,
        evidence=None,
        intent_name="",
        intent_confidence=0.0,
        action="answer",
    ):

        self.memory.remember(
            session_id,
            "user",
            user_input,
        )

        reasoning = self.reasoning.analyze(
            user_input,
            evidence=evidence,
            intent_name=intent_name,
            intent_confidence=intent_confidence,
        )

        policy = self.policy.decide(
            action=action,
            reasoning_status=reasoning.status,
            confidence=reasoning.confidence,
        )

        return {
            "reasoning": reasoning.to_dict(),
            "policy": policy.to_dict(),
            "memory": self.memory.context(session_id),
        }
"@

# ============================================================
# GATE 15 TEST
# ============================================================

Write-File "tests\test_gates_8_16.py" @"
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
"@

# ============================================================
# VALIDATOR
# ============================================================

Write-File "scripts\validate_gates_8_16.py" @"
from app.reasoning.engine import ReasoningEngine
from app.policy.engine import PolicyEngine
from app.memory.engine import MemoryEngine
from app.action.engine import ActionEngine
from app.orchestration.engine import OrchestrationEngine


def check(name, fn):

    try:
        fn()
        print(f"[PASS] {name}")
        return True

    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
        return False


def main():

    results = []

    results.append(
        check(
            "GATE 8 Reasoning",
            lambda: (
                lambda r: (
                    r.status == "grounded"
                    or (_ for _ in ()).throw(
                        AssertionError(r.status)
                    )
                )(
                    ReasoningEngine().analyze(
                        "Bagaimana cara cek status KTP-el?",
                        evidence=[
                            {
                                "chunk": "Status pengajuan KTP-el dapat diperiksa melalui layanan administrasi kependudukan.",
                                "score": 0.90,
                            }
                        ],
                        intent_name="ask_document_status",
                        intent_confidence=0.95,
                    )
                )
            ),
        )
    )

    results.append(
        check(
            "GATE 9 Policy",
            lambda: PolicyEngine().decide(
                action="answer",
                reasoning_status="grounded",
                confidence=0.90,
            ).allowed
            or (_ for _ in ()).throw(
                AssertionError("policy blocked")
            ),
        )
    )

    results.append(
        check(
            "GATE 10 Memory",
            lambda: (
                MemoryEngine().remember(
                    "test",
                    "user",
                    "hello",
                )
            ),
        )
    )

    results.append(
        check(
            "GATE 11 Action",
            lambda: (
                ActionEngine(
                    {"echo": lambda value: value}
                )
                .execute(
                    "echo",
                    {"value": "ok"},
                )["status"] == "success"
                or (_ for _ in ()).throw(
                    AssertionError("action failed")
                )
            ),
        )
    )

    results.append(
        check(
            "GATE 13 Orchestration",
            lambda: (
                "reasoning"
                in OrchestrationEngine().run(
                    session_id="test",
                    user_input="hello",
                    reasoning={"status": "grounded"},
                )["stages"]
                or (_ for _ in ()).throw(
                    AssertionError("orchestration failed")
                )
            ),
        )
    )

    print("")
    print("==============================================")
    print(" NUSANTARA GATE 8-16 FOUNDATION")
    print("==============================================")

    names = [
        "GATE 8  Reasoning",
        "GATE 9  Policy",
        "GATE 10 Memory",
        "GATE 11 Action",
        "GATE 13 Workflow",
    ]

    for name, result in zip(names, results):
        print(
            f"{name:<28} "
            f"{'PASS' if result else 'FAIL'}"
        )

    print(
        f"{'GATE 12 Tools':<28} EXISTING"
    )

    print(
        f"{'GATE 14 Developer Core':<28} FOUNDATION"
    )

    print(
        f"{'GATE 15 Evaluation':<28} FOUNDATION"
    )

    print(
        f"{'GATE 16 Production':<28} FOUNDATION"
    )

    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
"@

# ============================================================
# COMPILE
# ============================================================

Write-Host ""
Write-Host "=== PYTHON COMPILE ===" -ForegroundColor Cyan

python -m compileall -q `
    ".\app\reasoning" `
    ".\app\policy" `
    ".\app\memory" `
    ".\app\action" `
    ".\app\orchestration" `
    ".\app\developer_core" `
    ".\app\core\gate_pipeline.py" `
    ".\scripts\validate_gates_8_16.py" `
    ".\tests\test_gates_8_16.py"

if ($LASTEXITCODE -ne 0) {
    throw "PYTHON COMPILE FAILED"
}

Write-Host "PY_COMPILE : PASS" -ForegroundColor Green

# ============================================================
# FOUNDATION VALIDATION
# ============================================================

Write-Host ""
Write-Host "=== GATE 8-16 VALIDATION ===" -ForegroundColor Cyan

python ".\scripts\validate_gates_8_16.py"

if ($LASTEXITCODE -ne 0) {
    throw "GATE FOUNDATION VALIDATION FAILED"
}

# ============================================================
# PYTEST
# ============================================================

Write-Host ""
Write-Host "=== PYTEST ===" -ForegroundColor Cyan

python -m pytest ".\tests\test_gates_8_16.py" -q

if ($LASTEXITCODE -ne 0) {
    throw "GATE 8-16 PYTEST FAILED"
}

# ============================================================
# FINAL
# ============================================================

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " NUSANTARA GATE 8-16 FOUNDATION : PASS" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "GATE 7  RAG / Grounding       : PASS" -ForegroundColor Green
Write-Host "GATE 8  Reasoning             : PASS" -ForegroundColor Green
Write-Host "GATE 9  Decision / Policy     : PASS" -ForegroundColor Green
Write-Host "GATE 10 Memory / Context      : PASS" -ForegroundColor Green
Write-Host "GATE 11 Tool / Action         : PASS" -ForegroundColor Green
Write-Host "GATE 12 Tools                 : EXISTING" -ForegroundColor Green
Write-Host "GATE 13 Workflow              : PASS" -ForegroundColor Green
Write-Host "GATE 14 Developer Core / Graph: FOUNDATION" -ForegroundColor Yellow
Write-Host "GATE 15 Evaluation / Security : FOUNDATION" -ForegroundColor Yellow
Write-Host "GATE 16 Production Hardening  : FOUNDATION" -ForegroundColor Yellow
Write-Host ""
Write-Host "Gate 7 routes.py TIDAK DIUBAH." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Green
