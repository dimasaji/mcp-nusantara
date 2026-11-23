from pathlib import Path
import sys
import hashlib
import tempfile
import ast

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


class ValidationError(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def validate_preconditions(
    plan,
    target,
    expected_sha256,
):
    if not plan.approved:
        raise ValidationError(
            "ExecutionPlan belum approved"
        )

    if not target.is_file():
        raise ValidationError(
            "target tidak ditemukan"
        )

    actual = sha256(target)

    if actual != expected_sha256:
        raise ValidationError(
            "SHA-256 BEFORE tidak sesuai"
        )


def validate_postconditions(
    target,
    expected_content,
    expected_sha256,
):
    if not target.is_file():
        raise ValidationError(
            "target hilang setelah patch"
        )

    content = target.read_bytes()

    if content != expected_content:
        raise ValidationError(
            "isi target tidak sesuai expected change"
        )

    actual = sha256(target)

    if actual != expected_sha256:
        raise ValidationError(
            "SHA-256 AFTER tidak sesuai"
        )

    try:
        ast.parse(
            content.decode("utf-8")
        )
    except Exception as exc:
        raise ValidationError(
            "syntax Python tidak valid"
        ) from exc


def main():
    print("=" * 72)
    print("NUSANTARA GATE 16.6")
    print("PRE / POST VALIDATION")
    print("=" * 72)

    with tempfile.TemporaryDirectory(
        prefix="nusantara_gate16_6_"
    ) as temp:

        root = Path(temp)

        target = (
            root
            / "app"
            / "developer_core"
            / "gate16_test.py"
        )

        untouched = (
            root
            / "app"
            / "developer_core"
            / "untouched.py"
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        original = (
            b"def nusantara_test():\n"
            b"    return 'original'\n"
        )

        patched = (
            b"def nusantara_test():\n"
            b"    return 'patched'\n"
        )

        untouched_content = (
            b"UNCHANGED = True\n"
        )

        target.write_bytes(original)
        untouched.write_bytes(untouched_content)

        plan = ExecutionPlan(
            execution_id="exec-gate16-006",
            change_id="change-gate16-006",
            operation="modify_existing_file",
            target_files=(
                "app/developer_core/gate16_test.py",
            ),
            target_modules=(
                "app.developer_core",
            ),
            expected_change="controlled pre/post validation",
            preconditions=(
                "target exists",
                "sha256 matches",
            ),
            validation_steps=(
                "post content validation",
                "post sha256 validation",
                "python syntax validation",
            ),
            rollback_boundary="only approved target_files",
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        executor = ControlledPatchExecutor(root)

        before_hash = sha256(target)

        # --------------------------------------------------------------
        # PRE VALIDATION
        # --------------------------------------------------------------

        validate_preconditions(
            plan,
            target,
            before_hash,
        )

        print("[PASS] 16.6.1 Precondition validation")

        # --------------------------------------------------------------
        # PATCH
        # --------------------------------------------------------------

        result = executor.apply(
            plan,
            "app/developer_core/gate16_test.py",
            patched,
            expected_sha256=before_hash,
        )

        print("[PASS] 16.6.2 Controlled patch executed")

        # --------------------------------------------------------------
        # POST VALIDATION
        # --------------------------------------------------------------

        after_hash = hashlib.sha256(
            patched
        ).hexdigest()

        validate_postconditions(
            target,
            patched,
            after_hash,
        )

        print("[PASS] 16.6.3 Postcondition validation")

        assert result.sha256_before == before_hash
        print("[PASS] 16.6.4 BEFORE hash preserved")

        assert result.sha256_after == after_hash
        print("[PASS] 16.6.5 AFTER hash verified")

        assert untouched.read_bytes() == untouched_content
        print("[PASS] 16.6.6 Unexpected target unchanged")

        # --------------------------------------------------------------
        # INVALID SYNTAX TEST
        # --------------------------------------------------------------

        invalid = (
            b"def broken(:\n"
            b"    return True\n"
        )

        target.write_bytes(original)

        bad_before = sha256(target)

        executor.apply(
            plan,
            "app/developer_core/gate16_test.py",
            invalid,
            expected_sha256=bad_before,
        )

        try:
            validate_postconditions(
                target,
                invalid,
                hashlib.sha256(
                    invalid
                ).hexdigest(),
            )
            raise AssertionError(
                "invalid Python syntax diterima"
            )
        except ValidationError:
            pass

        print("[PASS] 16.6.7 Invalid syntax detected")

        # --------------------------------------------------------------
        # PRE HASH MISMATCH TEST
        # --------------------------------------------------------------

        target.write_bytes(original)

        try:
            validate_preconditions(
                plan,
                target,
                "0" * 64,
            )
            raise AssertionError(
                "SHA mismatch tidak diblokir"
            )
        except ValidationError:
            pass

        print("[PASS] 16.6.8 Precondition SHA mismatch blocked")

        # --------------------------------------------------------------
        # UNAPPROVED TEST
        # --------------------------------------------------------------

        unapproved = ExecutionPlan(
            execution_id="exec-gate16-006-bad",
            change_id="change-gate16-006-bad",
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
                "validation",
            ),
            rollback_boundary="only approved target_files",
            approved=False,
            status=BOUNDARY_VALIDATED,
        )

        try:
            validate_preconditions(
                unapproved,
                target,
                sha256(target),
            )
            raise AssertionError(
                "unapproved plan diterima"
            )
        except ValidationError:
            pass

        print("[PASS] 16.6.9 Unapproved plan blocked")

    print("-" * 72)
    print("VALIDATION CHECKS : 9")
    print("PASS              : 9")
    print("FAIL              : 0")
    print("-" * 72)
    print("GATE 16.6 FINAL   : PASS")
    print("EXECUTION         : CONTROLLED")
    print("=" * 72)


if __name__ == "__main__":
    main()
