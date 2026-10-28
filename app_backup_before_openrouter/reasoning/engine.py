"""
Reasoning Engine — Problem + Context + Knowledge → Plan → Execution → Evaluation.
Artefak terstruktur: goal, assumptions, plan, evidence, actions, validation result.
Tidak ada hidden chain-of-thought.
"""
import uuid
import logging
from typing import Any, Dict, List, Optional
from app.reasoning.schemas import (
    ReasoningGoal,
    ReasoningAssumption,
    ReasoningPlan,
    PlanStep,
    ReasoningEvidence,
    ReasoningAction,
    ValidationResult,
    ReasoningArtifact,
    ReasoningRequest,
    ReasoningResponse,
)

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Orchestrator utama reasoning.
    Input: Problem, Context, Knowledge (evidence).
    Output: Plan + Artefak terstruktur + Evaluation.
    """

    def __init__(self):
        self._artifacts: Dict[str, ReasoningArtifact] = {}

    def process(self, request: ReasoningRequest) -> ReasoningResponse:
        """
        Jalankan siklus reasoning lengkap.
        Return response dengan plan, assumptions, dan status.
        """
        goal = request.goal or self._infer_goal(request)
        assumptions = self._extract_assumptions(request)
        plan = self._create_plan(request, goal, assumptions)
        evidence_summary = self._summarize_evidence(request.evidence)
        missing_info = self._identify_missing(plan, goal, request.context)

        needs_clarification = len(missing_info) > 0
        requires_human = self._check_high_risk(goal, request.context)

        artifact = self._create_artifact(
            request=request,
            goal=goal,
            assumptions=assumptions,
            plan=plan,
            evidence=request.evidence or [],
        )

        return ReasoningResponse(
            request_id=artifact.artifact_id,
            artifact_id=artifact.artifact_id,
            goal=goal,
            assumptions=assumptions,
            plan=plan,
            evidence_summary=evidence_summary,
            missing_information=missing_info,
            needs_clarification=needs_clarification,
            requires_human_approval=requires_human,
            clarification_questions=self._build_clarification_questions(missing_info),
            status="needs_clarification" if needs_clarification else "in_progress",
        )

    def execute(
        self,
        artifact_id: str,
        actions: List[ReasoningAction],
    ) -> Optional[ReasoningArtifact]:
        """Eksekusi rencana dengan actions yang diberikan."""
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            logger.error(f"Artifact {artifact_id} tidak ditemukan")
            return None

        artifact.actions = actions
        artifact.status = "executing"
        return artifact

    def evaluate(self, artifact_id: str) -> Optional[ValidationResult]:
        """Evaluasi hasil eksekusi."""
        artifact = self._artifacts.get(artifact_id)
        if not artifact or not artifact.actions:
            return None

        result = self._run_evaluation(
            plan=artifact.plan,
            actions=artifact.actions,
            evidence=artifact.evidence,
            goal=artifact.goal,
        )

        artifact.validation = result
        artifact.status = "completed" if result.validated else "failed"
        return result

    def get_artifact(self, artifact_id: str) -> Optional[ReasoningArtifact]:
        return self._artifacts.get(artifact_id)

    def list_artifacts(self) -> List[ReasoningArtifact]:
        return list(self._artifacts.values())

    def _infer_goal(self, request: ReasoningRequest) -> ReasoningGoal:
        """Infer goal dari request jika tidak disediakan."""
        return ReasoningGoal(
            description=request.problem_description,
            success_criteria=["Masalah dipahami dan ditangani"],
            constraints=request.constraints or [],
            priority="normal",
        )

    def _extract_assumptions(
        self, request: ReasoningRequest
    ) -> List[ReasoningAssumption]:
        """Ekstrak asumsi dari problem dan context."""
        assumptions: List[ReasoningAssumption] = []

        assumptions.append(ReasoningAssumption(
            assumption="Descripsi masalah adalah akurat",
            confidence=0.7,
            source="inferred",
        ))

        if request.context:
            for key, value in request.context.items():
                assumptions.append(ReasoningAssumption(
                    assumption=f"Context '{key}' = {value}",
                    confidence=0.8,
                    source="provided",
                ))

        if request.evidence:
            assumptions.append(ReasoningAssumption(
                assumption=f"Terdapat {len(request.evidence)} evidence",
                confidence=0.6,
                source="observed",
            ))

        return assumptions

    def _create_plan(
        self,
        request: ReasoningRequest,
        goal: ReasoningGoal,
        assumptions: List[ReasoningAssumption],
    ) -> ReasoningPlan:
        """Buat plan dari goal dan assumptions."""
        steps: List[PlanStep] = []
        step_num = 0

        # Step 1: Pahami problem
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description=f"Analisis: {request.problem_description[:80]}",
            action_type="action",
            expected_output="Problem dipahami",
            dependencies=[],
            success_criteria=["Problem teridentifikasi"],
        ))

        # Step 2: Kumpulkan evidence
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Kumpulkan dan review evidence",
            action_type="retrieve",
            expected_output="Evidence terkumpul",
            dependencies=["s01"],
            success_criteria=["Evidence tervalidasi"],
        ))

        # Step 3: Identifikasi gap
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Identifikasi informasi yang kurang",
            action_type="action",
            expected_output="Daftar missing info",
            dependencies=["s02"],
            success_criteria=["Semua gap teridentifikasi"],
        ))

        # Step 4: Buat alternatif solusi
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Buat 2-3 alternatif solusi",
            action_type="action",
            expected_output="List alternatif",
            dependencies=["s03"],
            success_criteria=["Minimal 2 alternatif"],
        ))

        # Step 5: Pilih solusi terbaik
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Evaluasi dan pilih solusi terbaik",
            action_type="action",
            expected_output="Solusi terpilih",
            dependencies=["s04"],
            success_criteria=["Solusi terpilih dengan alasan jelas"],
        ))

        # Step 6: Eksekusi
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Eksekusi solusi",
            action_type="action",
            expected_output="Solusi tereksekusi",
            dependencies=["s05"],
            success_criteria=["Eksekusi sukses"],
        ))

        # Step 7: Verifikasi hasil
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Verifikasi hasil eksekusi",
            action_type="verify",
            expected_output="Hasil sesuai expectation",
            dependencies=["s06"],
            success_criteria=["Hasil sesuai success criteria"],
        ))

        # Step 8: Dokumentasi
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Dokumentasi hasil dan pelajaran",
            action_type="action",
            expected_output="Dokumentasi lengkap",
            dependencies=["s07"],
            success_criteria=["Dokumentasi selesai"],
        ))

        if len(steps) > request.max_steps:
            steps = steps[:request.max_steps]

        return ReasoningPlan(
            plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
            description=f"Plan untuk: {request.problem_description[:60]}",
            steps=steps,
            total_steps=len(steps),
            estimated_effort="medium" if len(steps) > 5 else "low",
            prerequisites=[],
        )

    def _run_evaluation(
        self,
        plan: ReasoningPlan,
        actions: List[ReasoningAction],
        evidence: List[ReasoningEvidence],
        goal: ReasoningGoal,
    ) -> ValidationResult:
        """Jalankan evaluasi atas hasil eksekusi."""
        issues: List[str] = []

        # 1. Cek action success
        failed = [a for a in actions if a.success is False]
        for a in failed:
            issues.append(f"Aksi '{a.action_id}' gagal: {a.error or 'no error msg'}")

        # 2. Cek goal criteria
        met_criteria = []
        unmet_criteria = []
        for criterion in goal.success_criteria:
            found = False
            for a in actions:
                if criterion.lower() in a.description.lower():
                    found = True
                    break
                if a.result and criterion.lower() in str(a.result).lower():
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

        # 3. Confidence
        total = len(actions)
        success_count = len([a for a in actions if a.success])
        action_rate = success_count / total if total > 0 else 0.0

        evidence_quality = (
            sum(e.confidence * e.relevance_score for e in evidence) / len(evidence)
            if evidence else 0.0
        )

        confidence = (
            action_rate * 0.4 +
            evidence_quality * 0.3 +
            (1.0 if not unmet_criteria else 0.0) * 0.3
        )

        return ValidationResult(
            validated=len(issues) == 0,
            issues=issues,
            confidence=confidence,
            details={
                "total_actions": total,
                "successful": success_count,
                "failed": len(failed),
                "goal_met": met_criteria,
                "goal_unmet": unmet_criteria,
                "evidence_quality": evidence_quality,
            },
        )

    def _identify_missing(
        self,
        plan: ReasoningPlan,
        goal: ReasoningGoal,
        context: Optional[Dict],
    ) -> List[str]:
        """Identifikasi informasi yang masih kurang."""
        missing: List[str] = []

        if context:
            for key in ["user_id", "location", "time", "budget"]:
                if key not in context:
                    missing.append(f"context: {key}")

        for step in plan.steps:
            if step.action_type == "retrieve" and not step.expected_output:
                missing.append(f"step {step.step_number}: expected_output tidak diisi")

        return missing

    def _check_high_risk(
        self, goal: ReasoningGoal, context: Optional[Dict]
    ) -> bool:
        """Cek apakah butuh human approval."""
        if "high" in goal.priority.lower() or "critical" in goal.priority.lower():
            return True
        if context and context.get("risk_level") in ("high", "critical"):
            return True
        return False

    def _build_clarification_questions(
        self, missing: List[str]
    ) -> List[str]:
        """Buat pertanyaan klarifikasi dari missing info."""
        questions = []
        for m in missing:
            questions.append(f"Apakah {m} tersedia?")
        return questions

    def _summarize_evidence(
        self, evidence: Optional[List[ReasoningEvidence]]
    ) -> str:
        """Ringkas evidence."""
        if not evidence:
            return "Tidak ada evidence yang diberikan"

        lines = [f"{len(evidence)} evidence tersedia:"]
        for i, ev in enumerate(evidence, 1):
            lines.append(f"  {i}. [{ev.source}] {ev.content[:100]}")
        return "\n".join(lines)

    def _create_artifact(
        self,
        request: ReasoningRequest,
        goal: ReasoningGoal,
        assumptions: List[ReasoningAssumption],
        plan: ReasoningPlan,
        evidence: List[ReasoningEvidence],
    ) -> ReasoningArtifact:
        """Buat artifact dan simpan."""
        artifact = ReasoningArtifact(
            artifact_id=f"ART-{uuid.uuid4().hex[:8].upper()}",
            goal=goal,
            assumptions=assumptions,
            plan=plan,
            evidence=evidence,
            actions=[],
            status="in_progress",
        )
        self._artifacts[artifact.artifact_id] = artifact
        return artifact


def create_reasoning_engine() -> ReasoningEngine:
    """Factory."""
    return ReasoningEngine()

_original_reasoning_process = ReasoningEngine.process
def _compat_reasoning_process(self, request=None, context=None, knowledge_evidence=None, problem_description=None, **kwargs):
    from app.reasoning.schemas import ReasoningRequest
    if problem_description is not None: request = problem_description
    if isinstance(request, str):
        req=ReasoningRequest(problem_description=request, context=context or {}, evidence=knowledge_evidence or [])
        return _original_reasoning_process(self, req)
    return _original_reasoning_process(self, request)
ReasoningEngine.process = _compat_reasoning_process
