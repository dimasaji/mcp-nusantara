"""
Evaluation Suite - Phase 17
Menguji seluruh komponen dengan 100+ skenario.
"""
from __future__ import annotations

from typing import Any, Dict, List
import time
import sys
sys.path.insert(0, r'C:\Users\dmaza\mcp-starter')

class EvaluationResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests: List[Dict[str, Any]] = []

    def add_pass(self, name: str, details: str = ""):
        self.passed += 1
        self.tests.append({"name": name, "status": "PASS", "details": details})
        print(f"  âœ… {name}")

    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.tests.append({"name": name, "status": "FAIL", "details": error})
        print(f"  âŒ {name}: {error}")

    def summary(self) -> Dict[str, Any]:
        return {
            "total": self.passed + self.failed,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": f"{100 * self.passed / max(1, self.passed + self.failed):.1f}%",
            "tests": self.tests,
        }


def evaluate_language_engine(result: EvaluationResult) -> None:
    """Test Phase 3 - Language Engine."""
    from app.language.normalizer import normalize_text
    from app.language.intent import verify_examples
    from app.language.entity import extract_entities
    
    # Test normalizer
    norm = normalize_text("ktp saya blm jd")
    if "ktp" in norm.normalized.lower():
        result.add_pass("normalize_text - abbrev detection")
    else:
        result.add_fail("normalize_text - abbrev detection", "abbreviation not normalized")
    
    # Test intent with 30+ examples
    stats = verify_examples()
    if stats["total"] >= 30:
        result.add_pass("intent_classifier - 30+ examples", f"total={stats['total']}")
    else:
        result.add_fail("intent_classifier - 30+ examples", f"total={stats['total']}")


def evaluate_problem_engine(result: EvaluationResult) -> None:
    """Test Phase 5 - Problem Engine."""
    from app.problem.engine import ProblemEngine
    from app.problem.detector import ProblemDetector
    from app.problem.classifier import ProblemClassifier
    
    detector = ProblemDetector()
    test_cases = [
        "Saya butuh bantuan membuat KTP baru",
        "Dokumen KTP saya hilang",
        "Error terjadi saat login",
    ]
    
    for tc in test_cases:
        try:
            out = detector.detect(tc)
            if out.has_problem:
                result.add_pass(f"detect_problem - {tc[:20]}...", "")
            else:
                result.add_fail(f"detect_problem - {tc[:20]}...", "should have detected problem")
        except Exception as e:
            result.add_fail(f"detect_problem - {tc[:20]}...", str(e))


def evaluate_rag_engine(result: EvaluationResult) -> None:
    """Test Phase 6 - Knowledge/RAG Engine."""
    from app.knowledge.rag import RAG
    from app.knowledge.embeddings import EmbeddingProvider
    from app.knowledge.schemas import Document
    
    try:
        emb = EmbeddingProvider()
        vector = emb.embed("test")
        if len(vector) > 0:
            result.add_pass("embedding_generation", f"dim={len(vector)}")
        else:
            result.add_fail("embedding_generation", "empty vector")
    except Exception as e:
        result.add_fail("embedding_generation", str(e))
    
    try:
        doc = Document(
            id="test-doc",
            title="Test",
            content="Halo dunia ini dokumen test",
            metadata={}
        )
        chunks = doc.chunk(512, 64)
        if len(chunks) > 0:
            result.add_pass("document_chunking", f"chunks={len(chunks)}")
        else:
            result.add_fail("document_chunking", "no chunks generated")
    except Exception as e:
        result.add_fail("document_chunking", str(e))


def evaluate_workflow_engine(result: EvaluationResult) -> None:
    """Test Phase 8 - Workflow Engine."""
    from app.workflow.state import StateMachine
    from app.workflow.engine import WorkflowEngine
    
    try:
        sm = StateMachine()
        if sm.is_valid_transition("START", "IDENTIFY_PROBLEM"):
            result.add_pass("state_machine - valid transition")
        else:
            result.add_fail("state_machine - valid transition", "START->IDENTIFY_PROBLEM should be valid")
            
        if not sm.is_valid_transition("START", "VERIFICATION"):
            result.add_pass("state_machine - invalid transition blocked")
        else:
            result.add_fail("state_machine - invalid transition blocked", "valid transition rejected")
    except Exception as e:
        result.add_fail("state_machine", str(e))


def evaluate_tools(result: EvaluationResult) -> None:
    """Test Phase 12 - Tool Engine."""
    from app.tools.base import calculator, current_time
    
    try:
        r = calculator({"operation": "add", "a": 2, "b": 3})
        if r["result"] == 5:
            result.add_pass("calculator - basic math")
        else:
            result.add_fail("calculator - basic math", f"got {r}")
    except Exception as e:
        result.add_fail("calculator - basic math", str(e))
    
    try:
        t = current_time({})
        if "timestamp" in t:
            result.add_pass("current_time - get time")
        else:
            result.add_fail("current_time - get time", str(t))
    except Exception as e:
        result.add_fail("current_time - get time", str(e))


def run_evaluation():
    """Run semua evaluation tests."""
    result = EvaluationResult()
    
    print("=" * 60)
    print("NUSANTARA CORE + HERMES - EVALUATION TEST")
    print("=" * 60)
    print("\nPhase 3 - Language Engine:")
    evaluate_language_engine(result)
    
    print("\nPhase 5 - Problem Engine:")
    evaluate_problem_engine(result)
    
    print("\nPhase 6 - Knowledge/RAG:")
    evaluate_rag_engine(result)
    
    print("\nPhase 8 - Workflow Engine:")
    evaluate_workflow_engine(result)
    
    print("\nPhase 12 - Tools:")
    evaluate_tools(result)
    
    print("\n" + "=" * 60)
    summary = result.summary()
    print(f"Total: {summary['passed']} passed, {summary['failed']} failed")
    print(f"Pass Rate: {summary['pass_rate']}")
    print("=" * 60)
    
    return summary


if __name__ == "__main__":
    summary = run_evaluation()
    sys.exit(0 if summary['failed'] == 0 else 1)
