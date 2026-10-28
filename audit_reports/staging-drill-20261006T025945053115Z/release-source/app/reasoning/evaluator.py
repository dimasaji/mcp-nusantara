"""
Evaluator - Evaluasi hasil eksekusi rencana.
"""
from typing import List, Optional, Dict
from app.reasoning.schemas import (
    ReasoningPlan,
    ReasoningAction,
    ReasoningEvidence,
    ReasoningGoal,
    ValidationResult,
)


class Evaluator:
    """Evaluator - memvalidasi hasil eksekusi."""

    def evaluate(
        self,
        plan: ReasoningPlan,
        actions: List[ReasoningAction],
        evidence: Optional[List[ReasoningEvidence]] = None,
        goal: Optional[ReasoningGoal] = None,
    ) -> ValidationResult:
        """
        Evaluasi hasil eksekusi.
        Return ValidationResult dengan validated, issues, confidence.
        """
        evidence = evidence or []
        goal = goal or ReasoningGoal(
            description="",
            success_criteria=[],
        )

        issues: List[str] = []

        # 1. Cek action failures
        failed_actions = [a for a in actions if a.success is False]
        for a in failed_actions:
            issues.append(f"Action '{a.action_id}' gagal: {a.error or 'Unknown error'}")

        # 2. Cek goal criteria
        met_criteria: List[str] = []
        unmet_criteria: List[str] = []

        for criterion in goal.success_criteria:
            found = False
            for action in actions:
                if criterion.lower() in action.description.lower():
                    found = True
                    break
                if action.result and criterion.lower() in str(action.result).lower():
                    found = True
                    break
            for ev in evidence:
                if criterion.lower() in ev.content.lower():
                    found = True
                    break
            if found:
                met_criteria.append(criterion)
            else:
                unmet_criteria.append(criterion)

        for c in unmet_criteria:
            issues.append(f"Goal criterion tidak terpenuhi: {c}")

        # 3. Hitung confidence
        total = len(actions)
        success_count = len([a for a in actions if a.success])
        action_rate = success_count / total if total > 0 else 0.0

        evidence_quality = (
            sum(e.confidence * e.relevance_score for e in evidence) / len(evidence)
            if evidence else 0.0
        )

        confidence = (
            action_rate * 0.5 +
            evidence_quality * 0.3 +
            (1.0 if not unmet_criteria else 0.0) * 0.2
        )

        return ValidationResult(
            validated=len(issues) == 0,
            issues=issues,
            confidence=confidence,
            details={
                "total_actions": total,
                "successful": success_count,
                "failed": len(failed_actions),
                "goal_criteria_met": met_criteria,
                "goal_criteria_unmet": unmet_criteria,
                "evidence_quality": evidence_quality,
            },
        )


def create_evaluator() -> Evaluator:
    """Factory."""
    return Evaluator()

def evaluate(*args, **kwargs):
    return create_evaluator().evaluate(*args, **kwargs)
