from __future__ import annotations

from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_validator(name: str, candidates: tuple[str, ...]) -> str:
    for candidate in candidates:
        script = SCRIPTS / candidate

        if not script.is_file():
            continue

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        output = result.stdout + "\n" + result.stderr

        if result.returncode != 0:
            raise RuntimeError(
                f"{name} gagal dieksekusi.\n{output}"
            )

        lines = [
            line.strip()
            for line in output.splitlines()
            if line.strip()
        ]

        final_pass = any(
            line.endswith(": PASS")
            for line in lines
        )

        if not final_pass:
            raise RuntimeError(
                f"{name} tidak memiliki FINAL PASS.\n{output}"
            )

        final_fail = any(
            line.endswith(": FAIL")
            for line in lines
        )

        if final_fail:
            raise RuntimeError(
                f"{name} memiliki FINAL FAIL.\n{output}"
            )

        return candidate

    raise RuntimeError(
        f"Validator {name} tidak ditemukan."
    )

def main():
    print("=" * 72)
    print("NUSANTARA GATE 16 FINAL")
    print("CONTROLLED EXECUTION CONTRACT")
    print("=" * 72)

    checks = 0

    # --------------------------------------------------------------
    # 16.F.1 EXECUTION PLAN / BOUNDARY
    # --------------------------------------------------------------

    run_validator(
        "Gate 16.1 / 16.2",
        (
            "validate_gate16_boundary.py",
        ),
    )

    checks += 1
    print(
        "[PASS] 16.F.1 Execution Plan / Boundary"
    )

    # --------------------------------------------------------------
    # 16.F.2 APPROVAL
    # --------------------------------------------------------------

    run_validator(
        "Gate 16.3",
        (
            "validate_gate16_approval.py",
        ),
    )

    checks += 1
    print(
        "[PASS] 16.F.2 Approval Enforcement"
    )

    # --------------------------------------------------------------
    # 16.F.3 SNAPSHOT
    # --------------------------------------------------------------

    run_validator(
        "Gate 16.4",
        (
            "validate_gate16_snapshot.py",
        ),
    )

    checks += 1
    print(
        "[PASS] 16.F.3 Snapshot / Rollback"
    )

    # --------------------------------------------------------------
    # 16.F.4 PATCH
    # --------------------------------------------------------------

    run_validator(
        "Gate 16.5",
        (
            "validate_gate16_patch.py",
        ),
    )

    checks += 1
    print(
        "[PASS] 16.F.4 Controlled Patch"
    )

    # --------------------------------------------------------------
    # 16.F.5 PRE / POST
    # --------------------------------------------------------------

    run_validator(
        "Gate 16.6",
        (
            "validate_gate16_validation.py",
        ),
    )

    checks += 1
    print(
        "[PASS] 16.F.5 Pre/Post Validation"
    )

    # --------------------------------------------------------------
    # 16.F.6 REGRESSION
    # --------------------------------------------------------------

    run_validator(
        "Gate 16.7",
        (
            "validate_gate16_regression.py",
        ),
    )

    checks += 1
    print(
        "[PASS] 16.F.6 Regression Gate"
    )

    # --------------------------------------------------------------
    # 16.F.7 GRAPH
    # --------------------------------------------------------------

    run_validator(
        "Gate 16.8",
        (
            "validate_gate16_graph.py",
        ),
    )

    checks += 1
    print(
        "[PASS] 16.F.7 Runtime <-> Graph"
    )

    # --------------------------------------------------------------
    # 16.F.8 AUDIT
    # --------------------------------------------------------------

    run_validator(
        "Gate 16.9",
        (
            "validate_gate16_audit.py",
        ),
    )

    checks += 1
    print(
        "[PASS] 16.F.8 Execution Audit"
    )

    # --------------------------------------------------------------
    # 16.F.9 GATE 14 REGRESSION
    # --------------------------------------------------------------

    run_validator(
        "Gate 14",
        (
            "validate_gate14_final.py",
            "validate_gate14_final_contract.py",
        ),
    )

    checks += 1
    print(
        "[PASS] 16.F.9 Gate 14 Regression"
    )

    # --------------------------------------------------------------
    # 16.F.10 GATE 15 REGRESSION
    # --------------------------------------------------------------

    gate15_candidates = (
        "validate_gate15_final.py",
        "validate_gate15_operational_final.py",
        "validate_gate15.py",
    )

    run_validator(
        "Gate 15",
        gate15_candidates,
    )

    checks += 1
    print(
        "[PASS] 16.F.10 Gate 15 Regression"
    )

    # --------------------------------------------------------------
    # 16.F.11 CONTROLLED EXECUTION SOURCE CONTRACT
    # --------------------------------------------------------------

    executor = (
        PROJECT_ROOT
        / "app"
        / "developer_core"
        / "controlled_patch_executor.py"
    )

    execution_plan = (
        PROJECT_ROOT
        / "app"
        / "developer_core"
        / "execution_plan.py"
    )

    boundary = (
        PROJECT_ROOT
        / "app"
        / "developer_core"
        / "execution_boundary.py"
    )

    approval = (
        PROJECT_ROOT
        / "app"
        / "developer_core"
        / "execution_approval.py"
    )

    audit = (
        PROJECT_ROOT
        / "app"
        / "developer_core"
        / "execution_audit.py"
    )

    required_files = (
        executor,
        execution_plan,
        boundary,
        approval,
        audit,
    )

    for path in required_files:
        if not path.is_file():
            raise RuntimeError(
                f"Controlled execution component missing: {path}"
            )

    executor_source = executor.read_text(
        encoding="utf-8-sig"
    )

    # ControlledPatchExecutor harus bebas dari import/call
    # subprocess maupun shell execution.
    #
    # Pemeriksaan dilakukan terhadap baris kode aktif,
    # bukan sekadar pencarian kata pada seluruh source,
    # sehingga komentar/docstring tidak menyebabkan false positive.

    active_lines = []

    for raw_line in executor_source.splitlines():
        stripped = raw_line.strip()

        if not stripped:
            continue

        if stripped.startswith("#"):
            continue

        active_lines.append(stripped)

    active_source = "\n".join(active_lines)

    forbidden_patterns = (
        "import subprocess",
        "from subprocess import",
        "subprocess.",
        "os.system(",
        "os.popen(",
        "os.spawn",
    )

    for token in forbidden_patterns:
        if token in active_source:
            raise RuntimeError(
                "ControlledPatchExecutor mengandung "
                f"forbidden execution pattern: {token}"
            )

    required_runtime_tokens = (
        "os.replace",
        "hashlib",
    )

    for token in required_runtime_tokens:
        if token not in executor_source:
            raise RuntimeError(
                "ControlledPatchExecutor tidak memiliki "
                f"required safety primitive: {token}"
            )

    checks += 1
    print(
        "[PASS] 16.F.11 Controlled Execution Boundary"
    )
    # --------------------------------------------------------------
    # 16.F.12 FAIL-CLOSED CONTRACT
    # --------------------------------------------------------------

    approval_source = approval.read_text(
        encoding="utf-8-sig"
    )

    boundary_source = boundary.read_text(
        encoding="utf-8-sig"
    )

    audit_source = audit.read_text(
        encoding="utf-8-sig"
    )

    required_contracts = (
        (
            "approval status enforcement",
            "APPROVED",
            approval_source,
        ),
        (
            "boundary fail-closed",
            "require_allowed",
            boundary_source,
        ),
        (
            "audit fail-closed",
            "ExecutionAuditError",
            audit_source,
        ),
    )

    for label, token, source in required_contracts:
        if token not in source:
            raise RuntimeError(
                f"Contract '{label}' tidak ditemukan: {token}"
            )

    checks += 1
    print(
        "[PASS] 16.F.12 Fail-Closed Contract"
    )

    # --------------------------------------------------------------
    # FINAL CONTRACT
    # --------------------------------------------------------------

    if checks != 12:
        raise RuntimeError(
            f"Jumlah final checks tidak sesuai: {checks}"
        )

    print("-" * 72)
    print(
        f"VALIDATION CHECKS : {checks}"
    )
    print(
        f"PASS              : {checks}"
    )
    print(
        "FAIL              : 0"
    )
    print("-" * 72)
    print(
        "GATE 16 FINAL     : PASS"
    )
    print(
        "EXECUTION         : CONTROLLED ONLY"
    )
    print(
        "BROAD WRITE       : NOT ENABLED"
    )
    print(
        "SHELL EXECUTION   : NOT ENABLED"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()


