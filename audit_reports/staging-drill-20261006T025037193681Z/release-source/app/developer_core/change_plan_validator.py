"""Nusantara V1 - Gate 15 Operational ChangePlan Validator.

Validator deterministic.
Tidak menggunakan LLM dan tidak melakukan write/patch/execute.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.developer_core.change_plan import (
    ALLOWED_TRANSITIONS,
    APPROVED,
    ChangePlan,
    INVALID,
    READY,
    VALIDATED,
    VALID_RISKS,
    VALID_STATUSES,
)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    checked_rules: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "checked_rules": list(self.checked_rules),
        }


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, (tuple, list)) and len(value) > 0


def validate_change_plan(
    plan: ChangePlan,
    *,
    approval_valid: bool = False,
) -> ValidationResult:
    """Validasi ChangePlan secara deterministic.

    approval_valid hanya boleh True jika caller sudah membuktikan
    approval human yang valid untuk payload ChangePlan yang sama.
    """
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []

    # ------------------------------------------------------------
    # TYPE / REQUIRED
    # ------------------------------------------------------------
    checked.append("change_plan_type")
    if not isinstance(plan, ChangePlan):
        return ValidationResult(
            False,
            ("objek bukan ChangePlan",),
            (),
            tuple(checked),
        )

    checked.append("change_id")
    if not _non_empty_string(plan.change_id):
        errors.append("change_id wajib diisi")

    checked.append("request")
    if not _non_empty_string(plan.request):
        errors.append("request wajib diisi")

    checked.append("scope")
    if not _non_empty_string(plan.scope):
        errors.append("scope wajib diisi")

    # ------------------------------------------------------------
    # AFFECTED SCOPE
    # ------------------------------------------------------------
    checked.append("affected_files")
    if not _non_empty_sequence(plan.affected_files):
        errors.append("affected_files wajib berisi minimal satu file")

    checked.append("affected_modules")
    if not _non_empty_sequence(plan.affected_modules):
        errors.append("affected_modules wajib berisi minimal satu module")

    # ------------------------------------------------------------
    # RISK
    # ------------------------------------------------------------
    checked.append("risk_signals")
    if not _non_empty_sequence(plan.risk_signals):
        errors.append("risk_signals wajib berisi minimal satu signal")

    for risk in plan.risk_signals:
        if not isinstance(risk, str) or not risk.strip():
            errors.append("risk_signals tidak boleh berisi nilai kosong")

    # ------------------------------------------------------------
    # EVIDENCE
    # ------------------------------------------------------------
    checked.append("evidence")
    if not _non_empty_sequence(plan.evidence):
        errors.append("evidence wajib tersedia")

    for item in plan.evidence:
        if not isinstance(item, str) or not item.strip():
            errors.append("evidence tidak boleh berisi nilai kosong")

    # ------------------------------------------------------------
    # VALIDATION PLAN
    # ------------------------------------------------------------
    checked.append("validation_plan")
    if not _non_empty_sequence(plan.validation_plan):
        errors.append("validation_plan wajib tersedia")

    for item in plan.validation_plan:
        if not isinstance(item, str) or not item.strip():
            errors.append("validation_plan tidak boleh berisi nilai kosong")

    # ------------------------------------------------------------
    # ROLLBACK
    # ------------------------------------------------------------
    checked.append("rollback_boundary")
    if not _non_empty_string(plan.rollback_boundary):
        errors.append("rollback_boundary wajib diisi")

    # ------------------------------------------------------------
    # APPROVAL
    # ------------------------------------------------------------
    checked.append("approval_required")
    if plan.approval_required is not True:
        errors.append("approval_required harus True")

    # ------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------
    checked.append("status")
    if plan.status not in VALID_STATUSES:
        errors.append(f"status tidak valid: {plan.status!r}")

    # READY membutuhkan approval yang sudah diverifikasi.
    checked.append("ready_requires_approval")
    if plan.status == READY and not approval_valid:
        errors.append("status READY membutuhkan approval human yang valid")

    # APPROVED juga harus mempunyai approval valid.
    checked.append("approved_requires_approval")
    if plan.status == APPROVED and not approval_valid:
        errors.append("status APPROVED membutuhkan approval human yang valid")

    # ------------------------------------------------------------
    # DIRECTIONAL IMPACT
    # ------------------------------------------------------------
    checked.append("directional_impact")
    if not isinstance(plan.directional_impact, dict):
        errors.append("directional_impact harus berupa dictionary")

    # ------------------------------------------------------------
    # SEQUENCE INTEGRITY
    # ------------------------------------------------------------
    checked.append("transition_contract")
    for status, targets in ALLOWED_TRANSITIONS.items():
        if status not in VALID_STATUSES:
            errors.append(f"transition source invalid: {status}")
        for target in targets:
            if target not in VALID_STATUSES:
                errors.append(
                    f"transition target invalid: {status} -> {target}"
                )

    # ------------------------------------------------------------
    # DETERMINISTIC RESULT
    # ------------------------------------------------------------
    return ValidationResult(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        checked_rules=tuple(checked),
    )


def validate_transition(
    current: ChangePlan,
    new_status: str,
    *,
    approval_valid: bool = False,
) -> ValidationResult:
    """Validasi transisi tanpa melakukan mutasi."""
    errors: list[str] = []
    checked = ["current_status", "target_status", "allowed_transition"]

    if current.status not in VALID_STATUSES:
        errors.append(f"current status tidak valid: {current.status}")

    if new_status not in VALID_STATUSES:
        errors.append(f"target status tidak valid: {new_status}")

    if (
        current.status in VALID_STATUSES
        and new_status in VALID_STATUSES
        and new_status not in ALLOWED_TRANSITIONS[current.status]
    ):
        errors.append(
            f"transisi tidak diizinkan: {current.status} -> {new_status}"
        )

    checked.append("approval_transition_rule")

    if new_status in {APPROVED, READY} and not approval_valid:
        errors.append(
            f"transisi ke {new_status} membutuhkan approval human yang valid"
        )

    if new_status == INVALID:
        checked.append("invalid_terminal_state")

    return ValidationResult(
        valid=not errors,
        errors=tuple(errors),
        warnings=(),
        checked_rules=tuple(checked),
    )


__all__ = [
    "ValidationResult",
    "validate_change_plan",
    "validate_transition",
]
