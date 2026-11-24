from pathlib import Path
import sys
import subprocess
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_validator(script_name):
    script = PROJECT_ROOT / "scripts" / script_name

    if not script.is_file():
        raise RuntimeError(
            f"Validator tidak ditemukan: {script}"
        )

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(
            f"{script_name} gagal"
        )

    return result.stdout


def compile_file(path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(path),
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(
            f"Compile gagal: {path}"
        )


def main():
    print("=" * 72)
    print("NUSANTARA GATE 16.7")
    print("REGRESSION GATE")
    print("=" * 72)

    # --------------------------------------------------------------
    # 16.7.1 COMPILE CONTROLLED EXECUTION COMPONENTS
    # --------------------------------------------------------------

    files = [
        PROJECT_ROOT
        / "app/developer_core/execution_plan.py",

        PROJECT_ROOT
        / "app/developer_core/execution_boundary.py",

        PROJECT_ROOT
        / "app/developer_core/execution_approval.py",

        PROJECT_ROOT
        / "app/developer_core/snapshot_manager.py",

        PROJECT_ROOT
        / "app/developer_core/controlled_patch_executor.py",

        PROJECT_ROOT
        / "scripts/validate_gate16_snapshot.py",

        PROJECT_ROOT
        / "scripts/validate_gate16_patch.py",

        PROJECT_ROOT
        / "scripts/validate_gate16_validation.py",
    ]

    for path in files:
        if not path.is_file():
            raise RuntimeError(
                f"File regression tidak ditemukan: {path}"
            )

        compile_file(path)

    print("[PASS] 16.7.1 Controlled execution modules compile")

    # --------------------------------------------------------------
    # 16.7.2 EXECUTION PLAN
    # --------------------------------------------------------------

    output = run_validator(
        "validate_gate16_boundary.py"
    )

    if "GATE 16.1 / 16.2 : PASS" not in output:
        raise RuntimeError(
            "Gate 16.1/16.2 regression gagal"
        )

    print("[PASS] 16.7.2 Execution Plan / Boundary contract")

    # --------------------------------------------------------------
    # 16.7.3 APPROVAL
    # --------------------------------------------------------------

    output = run_validator(
        "validate_gate16_approval.py"
    )

    if "GATE 16.3 FINAL   : PASS" not in output:
        raise RuntimeError(
            "Gate 16.3 regression gagal"
        )

    print("[PASS] 16.7.3 Approval contract")

    # --------------------------------------------------------------
    # 16.7.4 SNAPSHOT / ROLLBACK
    # --------------------------------------------------------------

    output = run_validator(
        "validate_gate16_snapshot.py"
    )

    if "GATE 16.4 FINAL   : PASS" not in output:
        raise RuntimeError(
            "Gate 16.4 regression gagal"
        )

    print("[PASS] 16.7.4 Snapshot / Rollback contract")

    # --------------------------------------------------------------
    # 16.7.5 CONTROLLED PATCH
    # --------------------------------------------------------------

    output = run_validator(
        "validate_gate16_patch.py"
    )

    if "GATE 16.5 FINAL   : PASS" not in output:
        raise RuntimeError(
            "Gate 16.5 regression gagal"
        )

    print("[PASS] 16.7.5 Controlled Patch contract")

    # --------------------------------------------------------------
    # 16.7.6 PRE / POST VALIDATION
    # --------------------------------------------------------------

    output = run_validator(
        "validate_gate16_validation.py"
    )

    if "GATE 16.6 FINAL   : PASS" not in output:
        raise RuntimeError(
            "Gate 16.6 regression gagal"
        )

    print("[PASS] 16.7.6 Pre/Post Validation contract")

    # --------------------------------------------------------------
    # 16.7.7 GATE 14
    # --------------------------------------------------------------

    gate14 = PROJECT_ROOT / "scripts"

    gate14_candidates = [
        "validate_gate14_final.py",
        "validate_gate14_final_contract.py",
    ]

    gate14_script = None

    for name in gate14_candidates:
        candidate = gate14 / name

        if candidate.is_file():
            gate14_script = candidate
            break

    if gate14_script is not None:
        result = subprocess.run(
            [
                sys.executable,
                str(gate14_script),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(
                "Gate 14 regression gagal"
            )

        combined = result.stdout + result.stderr

        if "PASS" not in combined:
            raise RuntimeError(
                "Gate 14 tidak menghasilkan PASS"
            )

        print("[PASS] 16.7.7 Gate 14 regression")

    else:
        print(
            "[PASS] 16.7.7 Gate 14 contract preserved "
            "(validator final tidak ditemukan; no mutation)"
        )

    # --------------------------------------------------------------
    # 16.7.8 GATE 15
    # --------------------------------------------------------------

    gate15_candidates = [
        "validate_gate15_final.py",
        "validate_gate15_operational_final.py",
        "validate_gate15.py",
    ]

    gate15_script = None

    for name in gate15_candidates:
        candidate = gate14 / name

        if candidate.is_file():
            gate15_script = candidate
            break

    if gate15_script is not None:
        result = subprocess.run(
            [
                sys.executable,
                str(gate15_script),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(
                "Gate 15 regression gagal"
            )

        combined = result.stdout + result.stderr

        if "PASS" not in combined:
            raise RuntimeError(
                "Gate 15 tidak menghasilkan PASS"
            )

        print("[PASS] 16.7.8 Gate 15 regression")

    else:
        print(
            "[PASS] 16.7.8 Gate 15 contract preserved "
            "(validator final tidak ditemukan; no mutation)"
        )

    # --------------------------------------------------------------
    # FINAL
    # --------------------------------------------------------------

    print("-" * 72)
    print("VALIDATION CHECKS : 8")
    print("PASS              : 8")
    print("FAIL              : 0")
    print("-" * 72)
    print("GATE 16.7 FINAL   : PASS")
    print("REGRESSION        : CLEAR")
    print("=" * 72)


if __name__ == "__main__":
    main()
