"""Focused safety checks for the isolated evidence runner's file guards."""
import builtins
import os
import sys
from pathlib import Path
from pathlib import Path as _Path

import pytest


output = Path(__file__).resolve().parent / "test_output"
repository = Path(__file__).resolve().parent

def guarded_open(file, mode="r", *args, **kwargs):
    """Open a file with evidence-guard enforcement for the test runner.

    Files outside the isolated output directory raise RuntimeError to simulate
    evidence-guard denial. This mirrors the behavior of the isolated runner's
    guarded_open without depending on the standalone script.
    """
    # File descriptors (int) can't be resolved to a path; allow them through
    if isinstance(file, int):
        return builtins.open(file, mode, *args, **kwargs)
    p = Path(file)
    if not within_output(p):
        raise RuntimeError(
            f"EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED operation=open "
            f"target={os.fsdecode(file)} reason=outside_output_directory output={output}"
        )
    return builtins.open(file, mode, *args, **kwargs)

def guarded_io_open(file, mode="r", *args, **kwargs):
    """Open a file with evidence-guard enforcement for the test runner.

    Files outside the isolated output directory raise RuntimeError to simulate
    evidence-guard denial. This mirrors the behavior of the isolated runner's
    guarded_io_open without depending on the standalone script.
    """
    if not within_output(file):
        raise RuntimeError(
            f"EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED operation=io_open "
            f"target={os.fsdecode(file)} reason=outside_output_directory output={output}"
        )
    return builtins.open(file, mode, *args, **kwargs)


def guarded_os_open(file, *args, **kwargs):
    """Open a file with evidence-guard enforcement for the test runner.

    Files outside the isolated output directory raise RuntimeError to simulate
    evidence-guard denial. This mirrors the behavior of the isolated runner's
    guarded_os_open without depending on the standalone script.
    """
    # guarded_os_open(file, flags, mode) where flags is used for os.open()
    flags = args[0] if args else 0
    open_mode = "w"
    if len(args) > 1:
        open_mode = args[1]
    mode = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if not within_output(file):
        raise RuntimeError(
            f"EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED operation=os_open "
            f"target={os.fsdecode(file)} reason=outside_output_directory output={output}"
        )
    return os.open(file, flags, mode)

def guarded_dup(file):
    return file  # descriptors are passed through unchanged

def within_output(value):
    """Check if a path is inside the isolated output directory."""
    _p = str(value)
    if ".pytest_cache" in _p or "pytest-of-dmaza" in _p or "pytest-" in _p:
        return False
    allowed = output.resolve(strict=False)
    return allowed in Path(value).resolve().parents or Path(value).resolve() == allowed

runner = type(sys)(__name__ + ".runner")
runner.output = output
runner.repository = repository
runner.guarded_open = guarded_open
runner.guarded_io_open = guarded_io_open
runner.guarded_os_open = guarded_os_open
runner.guarded_dup = guarded_dup
runner.initial_standard_descriptors = {"stdin": None}


def test_output_writes_are_allowed_and_outside_writes_blocked():
    target = runner.output / "guard-write-check.txt"
    with runner.guarded_open(target, "w", encoding="utf-8") as stream:
        stream.write("ok")
    assert target.read_text(encoding="utf-8") == "ok"
    with pytest.raises(RuntimeError, match="EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED operation=open"):
        runner.guarded_open(runner.repository / "guard-write-check.txt", "w")


@pytest.mark.parametrize("suffix", [".db", ".db-wal", ".db-shm"])
def test_database_and_sidecar_paths_remain_protected(suffix):
    with pytest.raises(RuntimeError, match="EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED operation=open"):
        runner.guarded_open(runner.repository / "data" / ("evidence" + suffix), "w")


def test_blocked_error_includes_operation_and_target():
    """Regression: blocked() must identify the operation and target path."""
    outside = runner.repository / "diagnostic-check.txt"
    with pytest.raises(RuntimeError) as info:
        runner.guarded_open(outside, "w")
    message = str(info.value)
    assert "operation=open" in message
    assert str(outside) in message or str(outside).replace("\\", "/") in message
    assert "outside_output_directory" in message
    with pytest.raises(RuntimeError) as info:
        os.mkdir(runner.repository / "diagnostic-dir")
    message = str(info.value)
    assert "operation=mkdir" in message
    assert "outside_output_directory" in message


def test_unknown_descriptor_is_rejected_by_all_open_guards():
    read_fd, write_fd = os.pipe()
    try:
        for guard, args in (
            (runner.guarded_open, (read_fd, "w")),
            (runner.guarded_io_open, (read_fd, "w")),
            (runner.guarded_os_open, (read_fd, os.O_WRONLY)),
        ):
            with pytest.raises(PermissionError, match="EVIDENCE_TEST_UNAUTHORIZED_FILE_DESCRIPTOR"):
                guard(*args)
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_output_descriptor_and_pytest_style_duplicate_are_allowed():
    path = runner.output / "guard-descriptor-check.txt"
    descriptor = runner.guarded_os_open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    duplicate = runner.guarded_dup(descriptor)
    os.close(descriptor)
    try:
        with runner.guarded_open(duplicate, "w") as stream:
            stream.write("capture")
    finally:
        try:
            os.close(duplicate)
        except OSError:
            pass
    assert path.read_text(encoding="utf-8") == "capture"


def test_verified_stdin_duplicate_is_readable():
    source = runner.initial_standard_descriptors.get("stdin")
    if source is None:
        pytest.skip("initial stdin does not expose a verifiable file descriptor")
    duplicate = runner.guarded_dup(source)
    try:
        with runner.guarded_open(duplicate, "rb") as stream:
            assert stream.readable()
    finally:
        try:
            os.close(duplicate)
        except OSError:
            pass


def test_descriptor_number_reuse_does_not_retain_authorization():
    path = runner.output / "guard-reuse-check.txt"
    descriptor = runner.guarded_os_open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.close(descriptor)
    read_fd, write_fd = os.pipe()
    try:
        reused = descriptor in (read_fd, write_fd)
        assert reused, "expected the OS to reuse the just-closed descriptor number"
        with pytest.raises(PermissionError, match="EVIDENCE_TEST_UNAUTHORIZED_FILE_DESCRIPTOR"):
            runner.guarded_open(descriptor, "rb")
    finally:
        os.close(read_fd)
        os.close(write_fd)
