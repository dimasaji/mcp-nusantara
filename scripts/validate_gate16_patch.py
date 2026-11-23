from pathlib import Path
import sys
import hashlib
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.developer_core.execution_plan import (
    ExecutionPlan,
    BOUNDARY_VALIDATED,
)
from app.developer_core.controlled_patch_executor import (
    ControlledPatchExecutor,
    ControlledPatchError,
)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def main():
    print("=" * 72)
    print("NUSANTARA GATE 16.5")
    print("CONTROLLED PATCH EXECUTOR")
    print("=" * 72)

    with tempfile.TemporaryDirectory(
        prefix="nusantara_gate16_5_"
    ) as temp:

        root = Path(temp)

        target = (
            root
            / "app"
            / "developer_core"
            / "gate16_test.py"
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        original = b"ORIGINAL_CONTENT\n"
        patched = b"PATCHED_NUSANTARA_CONTENT\n"

        target.write_bytes(original)

        plan = ExecutionPlan(
            execution_id="exec-gate16-005",
            change_id="change-gate16-005",
            operation="modify_existing_file",
            target_files=(
                "app/developer_core/gate16_test.py",
            ),
            target_modules=(
                "app.developer_core",
            ),
            expected_change="controlled patch test",
            preconditions=(
                "target exists",
            ),
            validation_steps=(
                "sha256 validation",
            ),
            rollback_boundary="only approved target_files",
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        executor = ControlledPatchExecutor(root)

        before_hash = sha256_bytes(original)

        result = executor.apply(
            plan,
            "app/developer_core/gate16_test.py",
            patched,
            expected_sha256=before_hash,
        )

        print("[PASS] 16.5.1 Approved plan accepted")

        assert result.sha256_before == before_hash
        print("[PASS] 16.5.2 SHA-256 BEFORE verified")

        assert target.read_bytes() == patched
        print("[PASS] 16.5.3 Controlled patch applied")

        assert (
            result.sha256_after
            == sha256_bytes(patched)
        )
        print("[PASS] 16.5.4 SHA-256 AFTER verified")

        try:
            executor.apply(
                plan,
                "app/developer_core/other.py",
                patched,
                expected_sha256=result.sha256_after,
            )
            raise AssertionError(
                "target berbeda tidak diblokir"
            )
        except ControlledPatchError:
            pass

        print("[PASS] 16.5.5 Target mismatch blocked")

        target.write_bytes(original)

        try:
            executor.apply(
                plan,
                "app/developer_core/gate16_test.py",
                patched,
                expected_sha256="0" * 64,
            )
            raise AssertionError(
                "SHA salah tidak diblokir"
            )
        except ControlledPatchError:
            pass

        print("[PASS] 16.5.6 SHA mismatch blocked")

        try:
            executor.apply(
                plan,
                "../outside.py",
                patched,
                expected_sha256=before_hash,
            )
            raise AssertionError(
                "path traversal tidak diblokir"
            )
        except ControlledPatchError:
            pass

        print("[PASS] 16.5.7 Path traversal blocked")

        try:
            executor.apply(
                plan,
                str(target.resolve()),
                patched,
                expected_sha256=before_hash,
            )
            raise AssertionError(
                "absolute path tidak diblokir"
            )
        except ControlledPatchError:
            pass

        print("[PASS] 16.5.8 Absolute path blocked")

        unapproved = ExecutionPlan(
            execution_id="exec-gate16-005-bad",
            change_id="change-gate16-005-bad",
            operation="modify_existing_file",
            target_files=(
                "app/developer_core/gate16_test.py",
            ),
            target_modules=(
                "app.developer_core",
            ),
            expected_change="test",
            preconditions=(
                "target exists",
            ),
            validation_steps=(
                "sha256 validation",
            ),
            rollback_boundary="only approved target_files",
            approved=False,
            status=BOUNDARY_VALIDATED,
        )

        try:
            executor.apply(
                unapproved,
                "app/developer_core/gate16_test.py",
                patched,
                expected_sha256=before_hash,
            )
            raise AssertionError(
                "unapproved plan diterima"
            )
        except ControlledPatchError:
            pass

        print("[PASS] 16.5.9 Unapproved plan blocked")

        assert target.read_bytes() == original
        print("[PASS] 16.5.10 Failed patch left target unchanged")

    print("-" * 72)
    print("VALIDATION CHECKS : 10")
    print("PASS              : 10")
    print("FAIL              : 0")
    print("-" * 72)
    print("GATE 16.5 FINAL   : PASS")
    print("PATCH EXECUTION   : CONTROLLED ONLY")
    print("=" * 72)


if __name__ == "__main__":
    main()
