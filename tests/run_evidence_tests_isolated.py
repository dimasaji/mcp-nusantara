"""Run only the offline evidence tests with external effects denied."""
from __future__ import annotations

import builtins
import os
import platform
from pathlib import Path
import socket
import sys

output = Path(os.environ.get("EVIDENCE_TEST_OUTPUT", Path(__file__).resolve().parent / "test_output"))
if any((parent/'FINALIZED.json').exists() for parent in (output,*output.parents)):
    raise SystemExit('FINALIZED_RUN_IMMUTABLE: choose a new run directory')
if not output.is_dir():
    raise SystemExit('isolated output directory is not readable')
repository = Path(__file__).resolve(strict=False).parents[1]
sys.path.insert(0, str(repository))
sys.dont_write_bytecode = True


def blocked(operation, target=None, reason=None):
    bits = [f"operation={operation}"]
    if target is not None:
        bits.append(f"target={os.fsdecode(target)}")
    if reason is not None:
        bits.append(f"reason={reason}")
    bits.append(f"output={output}")
    raise RuntimeError("EVIDENCE_TEST_EXTERNAL_EFFECT_BLOCKED " + " ".join(bits))


def unauthorized_descriptor():
    raise PermissionError("EVIDENCE_TEST_UNAUTHORIZED_FILE_DESCRIPTOR")


def within_output(value: object) -> bool:
    def normalize(value):
        raw = os.fsdecode(value)
        if raw.startswith("\\\\?\\UNC\\"):
            raw = "\\\\" + raw[8:]
        elif raw.startswith("\\\\?\\"):
            raw = raw[4:]
        return Path(raw).resolve(strict=False)

    path = normalize(value)
    allowed = normalize(output)
    return path == allowed or allowed in path.parents


def writing(flags: object) -> bool:
    if isinstance(flags, int):
        return bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
    return any(char in str(flags) for char in "wax+")


# Planning metadata that control-plane/evidence-requirements.json declares as an
# offline evidence source (AC10). It is a bounded read-only document, not the active
# store, so evidence collection may read exactly this file while every other /data/
# path and every database sidecar stays blocked. Exact-file match only: a directory
# or any other file under /data/ cannot pass through this exemption.
READONLY_DATA_ARTIFACTS = frozenset({(repository / "data/developer_core/change_plan.json").resolve()})


def check_database(value: object, for_write: bool = False) -> None:
    if isinstance(value, int):
        return
    raw = os.fsdecode(value)
    text = raw.replace("\\", "/").lower()
    if text.endswith((".db", ".db-wal", ".db-shm")):
        blocked("open", value, "active_database_or_sidecar")
    if "/data/" not in f"/{text.strip('/')}/":
        return
    # The declared read-only planning artifact stays readable. Every other /data/
    # path outside the isolated run stays blocked; a fixture data directory inside
    # the run is not an external effect and is already bounded by the output rule.
    if not for_write:
        try:
            if Path(raw).resolve(strict=False) in READONLY_DATA_ARTIFACTS:
                return
        except OSError:
            pass
    if within_output(raw):
        return
    blocked("open", value, "active_database_or_sidecar")


trusted_descriptors = {}
original_dup = os.dup


def descriptor_identity(fd):
    stat = os.fstat(fd)
    return stat.st_dev, stat.st_ino, stat.st_mode


def descriptor_modes(mode):
    return frozenset(("read", "write") if "+" in str(mode) else
                     (("write",) if writing(mode) else ("read",)))


def os_descriptor_modes(flags):
    access = flags & getattr(os, "O_ACCMODE", os.O_WRONLY | os.O_RDWR)
    if access == os.O_RDONLY:
        return frozenset(("read",))
    if access == os.O_WRONLY:
        return frozenset(("write",))
    return frozenset(("read", "write"))


def register_descriptor(fd, modes):
    trusted_descriptors[fd] = (descriptor_identity(fd), frozenset(modes))


# Trust only the descriptors actually exposed by Python's initial standard
# streams. Their duplicates inherit the same access limit and verified identity.
initial_standard_descriptors = {}
for standard_name, standard_stream, modes in (
    ("stdin", sys.stdin, ("read",)),
    ("stdout", sys.stdout, ("write",)),
    ("stderr", sys.stderr, ("write",)),
):
    try:
        standard_fd = standard_stream.fileno()
        register_descriptor(standard_fd, modes)
        initial_standard_descriptors[standard_name] = standard_fd
    except (AttributeError, OSError, ValueError):
        pass


def guarded_dup(fd):
    source = trusted_descriptors.get(fd)
    duplicate = original_dup(fd)
    if source is not None and source[0] == descriptor_identity(fd):
        register_descriptor(duplicate, source[1])
    return duplicate


os.dup = guarded_dup


def authorize_file_descriptor(file, mode):
    if isinstance(file, int):
        authorization = trusted_descriptors.get(file)
        try:
            current_identity = descriptor_identity(file)
        except OSError:
            current_identity = None
        required_modes = descriptor_modes(mode)
        if (authorization is None or authorization[0] != current_identity or
                not required_modes.issubset(authorization[1])):
            unauthorized_descriptor()
        del trusted_descriptors[file]


def remember_open_file(file, mode, result):
    if writing(mode) and not isinstance(file, int) and within_output(file):
        try:
            descriptor = result.fileno()
            register_descriptor(descriptor, descriptor_modes(mode))
        except (AttributeError, OSError, ValueError):
            pass
    return result


def guarded_open(file, mode="r", *args, **kwargs):
    check_database(file, for_write=writing(mode))
    if isinstance(file, int):
        authorize_file_descriptor(file, mode)
    elif writing(mode) and not within_output(file):
        blocked("open", file, "outside_output_directory")
    return remember_open_file(file, mode, original_open(file, mode, *args, **kwargs))


original_open = builtins.open
builtins.open = guarded_open
original_io_open = __import__("io").open


def guarded_io_open(file, mode="r", *args, **kwargs):
    check_database(file, for_write=writing(mode))
    if isinstance(file, int):
        authorize_file_descriptor(file, mode)
    elif writing(mode) and not within_output(file):
        blocked("io_open", file, "outside_output_directory")
    return remember_open_file(file, mode, original_io_open(file, mode, *args, **kwargs))


__import__("io").open = guarded_io_open
original_os_open = os.open


def guarded_os_open(file, flags, *args, **kwargs):
    check_database(file, for_write=writing(flags))
    if isinstance(file, int):
        unauthorized_descriptor()
    if writing(flags) and not within_output(file):
        blocked("os_open", file, "outside_output_directory")
    descriptor = original_os_open(file, flags, *args, **kwargs)
    if writing(flags):
        register_descriptor(descriptor, os_descriptor_modes(flags))
    return descriptor


os.open = guarded_os_open
for name in ("mkdir", "makedirs", "remove", "unlink", "rmdir", "removedirs", "truncate"):
    original = getattr(os, name)
    op_name = name

    def make_guard(function, _op_name=op_name):
        def guard(path, *args, **kwargs):
            if not within_output(path):
                blocked(f"_{name} {path}" if False else _op_name, path, "outside_output_directory")
            return function(path, *args, **kwargs)
        return guard

    setattr(os, name, make_guard(original))
for name in ("rename", "replace"):
    original = getattr(os, name)
    op_name = name

    def make_move_guard(function, _op_name=op_name):
        def guard(source, target, *args, **kwargs):
            if not within_output(source) or not within_output(target):
                blocked(_op_name, source, "outside_output_directory")
            return function(source, target, *args, **kwargs)
        return guard

    setattr(os, name, make_move_guard(original))
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
os.environ["TMP"] = str(output)
os.environ["TEMP"] = str(output)
os.environ["TMPDIR"] = str(output)
import pytest
import sys
# Skip os patching for pytest cache directory to avoid interference with pytest cleanup
_pth = str(Path(__file__).resolve().parent)
for _name in ("mkdir", "makedirs", "remove", "unlink", "rmdir", "removedirs", "truncate"):
    _orig = getattr(os, _name)
    def _make_guard(function, _op_name=_name, _orig=original):
        def guard(path, *args, **kwargs):
            if _src := str(path).startswith(str(Path(__file__).resolve().parent)):
                pass
            else:
                if _src and ".pytest" in _src or ".pytest" in str(path):
                    return function(path, *args, **kwargs)
                blocked(f"_{_op_name} {path}" if False else _op_name, path, "outside_output_directory")
            return function(path, *args, **kwargs)
        return guard
    setattr(os, _name, make_guard(_orig))

original_connect = socket.socket.connect
original_connect_ex = socket.socket.connect_ex
original_socketpair = socket.socketpair
local_pair = False


def guarded_connect(self, address):
    if local_pair and isinstance(address, tuple) and address and address[0] in {"127.0.0.1", "::1", "localhost"}:
        return original_connect(self, address)
    blocked("socket_connect", address, "network_blocked")


def guarded_connect_ex(self, address):
    if local_pair and isinstance(address, tuple) and address and address[0] in {"127.0.0.1", "::1", "localhost"}:
        return original_connect_ex(self, address)
    blocked("socket_connect_ex", address, "network_blocked")


def guarded_listen(self, *args, **kwargs):
    if not local_pair:
        blocked("socket_listen", None, "network_blocked")
    return original_listen(self, *args, **kwargs)


def guarded_socketpair(*args, **kwargs):
    global local_pair
    local_pair = True
    try:
        return original_socketpair(*args, **kwargs)
    finally:
        local_pair = False


original_listen = socket.socket.listen
socket.socket.listen = guarded_listen
socket.socket.connect = guarded_connect
socket.socket.connect_ex = guarded_connect_ex
socket.socketpair = guarded_socketpair


def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.spawn"}:
        blocked(f"audit:{event}", None, "subprocess_blocked")


sys.addaudithook(audit)

test_paths = ["tests/test_evidence_runner_guards.py"] if sys.argv[2:] == ["--guards-only"] else [
    "tests/test_evidence_registry.py",
    "tests/test_evidence_decision_api.py",
    "tests/test_evidence_runner_guards.py",
    "tests/test_evidence_finalization.py",
    "tests/test_normal_plan.py",
    "tests/test_v1_execution_evidence.py",
    "tests/test_sop_ingestion.py::test_requirement_quote_requires_matching_service_and_remains_guarded",
    "tests/test_knowledge_pipeline.py",
    "tests/test_v1_service_dialogue.py",
]

if len(sys.argv) == 4 and sys.argv[2] == '--candidate':
    candidate = Path(sys.argv[3]).resolve()
    if not within_output(candidate) or not candidate.is_file():
        raise SystemExit('candidate test must be inside isolated output directory')
    test_paths = [str(candidate)]

raise SystemExit(pytest.main([
    "-c", "tests/pytest-evidence.ini",
    "-p", "no:cacheprovider",
    "--basetemp", str(output / "pytest-tmp"),
    "--log-file", str(output / "pytest.log"),
    "--junitxml", str(output / "python-results.xml"),
    *test_paths,
]))

