"""
Planner - Membuat rencana eksekusi dari problem, context, dan evidence.
"""
from typing import List, Optional, Dict
from app.reasoning.schemas import (
    ReasoningGoal,
    ReasoningAssumption,
    ReasoningPlan,
    PlanStep,
    ReasoningEvidence,
)


class Planner:
    """Planner - merancang rencana eksekusi."""

    def __init__(self, max_default_steps: int = 20):
        self.max_default_steps = max_default_steps

    def create_plan(
        self,
        goal: ReasoningGoal,
        evidence: Optional[List[ReasoningEvidence]] = None,
        context: Optional[Dict] = None,
        max_steps: Optional[int] = None,
    ) -> ReasoningPlan:
        """
        Buat rencana dari goal.
        Return ReasoningPlan dengan langkah-langkah terstruktur.
        """
        steps: List[PlanStep] = []
        step_num = 0

        # Step 1: Pahami goal
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description=f"Memahami goal: {goal.description[:80]}",
            action_type="action",
            expected_output="Goal dipahami dan dianalisis",
            dependencies=[],
            success_criteria=["Goal teridentifikasi dengan jelas"],
        ))

        # Step 2: Review evidence
        if evidence:
            step_num += 1
            steps.append(PlanStep(
                step_id=f"s{step_num:02d}",
                step_number=step_num,
                description=f"Review {len(evidence)} evidence",
                action_type="retrieve",
                expected_output="Evidence tervalidasi",
                dependencies=["s01"],
                success_criteria=["Evidence relevan dan valid"],
            ))

        # Step 3: Identifikasi kebutuhan
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Identifikasi kebutuhan dan constraint",
            action_type="action",
            expected_output="Kebutuhan dan constraint teridentifikasi",
            dependencies=["s01"],
            success_criteria=["Semua constraint dipahami"],
        ))

        # Step 4: Buat alternatif
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Buat 2-3 alternatif pendekatan",
            action_type="action",
            expected_output="List alternatif solusi",
            dependencies=["s03"],
            success_criteria=["Minimal 2 alternatif"],
        ))

        # Step 5: Evaluasi alternatif
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Evaluasi alternatif dan pilih terbaik",
            action_type="action",
            expected_output="Solusi terpilih",
            dependencies=["s04"],
            success_criteria=["Pilihan didukung alasan"],
        ))

        # Step 6: Eksekusi
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Eksekusi solusi terpilih",
            action_type="action",
            expected_output="Solusi tereksekusi",
            dependencies=["s05"],
            success_criteria=["Eksekusi berhasil"],
        ))

        # Step 7: Verifikasi
        step_num += 1
        steps.append(PlanStep(
            step_id=f"s{step_num:02d}",
            step_number=step_num,
            description="Verifikasi hasil eksekusi",
            action_type="verify",
            expected_output="Hasil sesuai expectation",
            dependencies=["s06"],
            success_criteria=["Hasil sesuai goal criteria"],
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

        max_steps = max_steps or self.max_default_steps
        if len(steps) > max_steps:
            steps = steps[:max_steps]

        return ReasoningPlan(
            plan_id=f"PLAN-{step_num:04d}",
            description=goal.description,
            steps=steps,
            total_steps=len(steps),
            estimated_effort="medium" if len(steps) > 5 else "low",
            prerequisites=[],
        )


def create_plan(
    goal: ReasoningGoal,
    evidence: Optional[List[ReasoningEvidence]] = None,
    context: Optional[Dict] = None,
    max_steps: Optional[int] = None,
) -> ReasoningPlan:
    """Shortcut create plan."""
    planner = Planner()
    return planner.create_plan(goal, evidence, context, max_steps)

planner = create_plan
