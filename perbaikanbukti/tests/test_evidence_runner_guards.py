"""Focused safety checks for the isolated evidence runner's file guards."""
import os
import sys

import pytest


runner = sys.modules["__main__"]


def test_output_writes_are_allowed_and_outside_writes_blocked(tmp_path):
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
