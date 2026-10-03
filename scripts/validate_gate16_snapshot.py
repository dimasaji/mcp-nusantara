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
from app.developer_core.snapshot_manager import (
    SnapshotManager,
    SnapshotError,
)


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def main():
    print("=" * 72)
    print("NUSANTARA GATE 16.4")
    print("SNAPSHOT / ROLLBACK")
    print("=" * 72)

    with tempfile.TemporaryDirectory(
        prefix="nusantara_gate16_4_"
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

        original = b"ORIGINAL_NUSANTARA_CONTENT\n"
        target.write_bytes(original)

        manager = SnapshotManager(root)

        plan = ExecutionPlan(
            execution_id="exec-gate16-004",
            change_id="change-gate16-004",
            operation="modify_existing_file",
            target_files=(
                "app/developer_core/gate16_test.py",
            ),
            target_modules=(
                "app.developer_core",
            ),
            expected_change="controlled test change",
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

        # ----------------------------------------------------------
        # 16.4.1 SNAPSHOT
        # ----------------------------------------------------------
        manifest = manager.create_snapshot(plan)

        assert manifest.snapshot_id
        assert len(manifest.files) == 1

        print("[PASS] 16.4.1 Snapshot created")

        # ----------------------------------------------------------
        # 16.4.2 SHA-256 BEFORE
        # ----------------------------------------------------------
        assert (
            manifest.files[0].sha256_before
            == sha256(target)
        )

        print("[PASS] 16.4.2 SHA-256 BEFORE recorded")

        # ----------------------------------------------------------
        # 16.4.3 SNAPSHOT INTEGRITY
        # ----------------------------------------------------------
        snapshot_file = (
            Path(manifest.snapshot_root)
            / "app"
            / "developer_core"
            / "gate16_test.py"
        )

        assert snapshot_file.is_file()

        assert (
            sha256(snapshot_file)
            == sha256(target)
        )

        print("[PASS] 16.4.3 Snapshot integrity verified")

        # ----------------------------------------------------------
        # 16.4.4 MODIFY TEST TARGET
        # ----------------------------------------------------------
        target.write_bytes(
            b"MODIFIED_CONTENT\n"
        )

        assert (
            sha256(target)
            != manifest.files[0].sha256_before
        )

        print("[PASS] 16.4.4 Target modification detected")

        # ----------------------------------------------------------
        # 16.4.5 ROLLBACK
        # ----------------------------------------------------------
        restored = manager.rollback(manifest)

        assert restored == (
            "app/developer_core/gate16_test.py",
        )

        assert target.read_bytes() == original

        print("[PASS] 16.4.5 Rollback restored target")

        # ----------------------------------------------------------
        # 16.4.6 ROLLBACK HASH
        # ----------------------------------------------------------
        assert (
            sha256(target)
            == manifest.files[0].sha256_before
        )

        print("[PASS] 16.4.6 Rollback SHA-256 verified")

        # ----------------------------------------------------------
        # 16.4.7 PATH TRAVERSAL
        # ----------------------------------------------------------
        bad_plan = ExecutionPlan(
            execution_id="exec-bad",
            change_id="change-bad",
            operation="modify_existing_file",
            target_files=(
                "../outside.py",
            ),
            target_modules=("test",),
            expected_change="test",
            preconditions=("test",),
            validation_steps=("test",),
            rollback_boundary="test",
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        try:
            manager.create_snapshot(bad_plan)
            raise AssertionError(
                "path traversal tidak diblokir"
            )
        except SnapshotError:
            pass

        print("[PASS] 16.4.7 Path traversal blocked")

        # ----------------------------------------------------------
        # 16.4.8 ABSOLUTE PATH
        # ----------------------------------------------------------
        bad_plan2 = ExecutionPlan(
            execution_id="exec-bad2",
            change_id="change-bad2",
            operation="modify_existing_file",
            target_files=(
                str(target.resolve()),
            ),
            target_modules=("test",),
            expected_change="test",
            preconditions=("test",),
            validation_steps=("test",),
            rollback_boundary="test",
            approved=True,
            status=BOUNDARY_VALIDATED,
        )

        try:
            manager.create_snapshot(bad_plan2)
            raise AssertionError(
                "absolute path tidak diblokir"
            )
        except SnapshotError:
            pass

        print("[PASS] 16.4.8 Absolute path blocked")

        # ----------------------------------------------------------
        # 16.4.9 UNAPPROVED PLAN
        # ----------------------------------------------------------
        unapproved = ExecutionPlan(
            execution_id="exec-unapproved",
            change_id="change-unapproved",
            operation="modify_existing_file",
            target_files=(
                "app/developer_core/gate16_test.py",
            ),
            target_modules=("test",),
            expected_change="test",
            preconditions=("test",),
            validation_steps=("test",),
            rollback_boundary="test",
            approved=False,
            status=BOUNDARY_VALIDATED,
        )

        try:
            manager.create_snapshot(unapproved)
            raise AssertionError(
                "unapproved plan diterima"
            )
        except SnapshotError:
            pass

        print("[PASS] 16.4.9 Unapproved plan blocked")

    print("-" * 72)
    print("VALIDATION CHECKS : 9")
    print("PASS              : 9")
    print("FAIL              : 0")
    print("-" * 72)
    print("GATE 16.4 FINAL   : PASS")
    print("PATCH EXECUTION   : NOT ENABLED")
    print("=" * 72)


if __name__ == "__main__":
    main()

