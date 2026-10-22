"""Cooperative controls inherited by Python subprocess verification fixtures."""

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import url2pathname

READ_ONLY_SOURCE_FIXTURES = (
    "data/developer_core/change_plan.json",
    "data/knowledge/official_sources/ktp_el/manifest.json",
    *(f"data/knowledge/official_sources/ktp_el/tng-ktpel-{number:03d}.md" for number in range(1, 5)),
)


def install(output, repository, bootstrap):
    output, repository, bootstrap = map(Path, (output, repository, bootstrap))
    sys.dont_write_bytecode = True
    import dotenv
    from pydantic_settings.sources.providers.dotenv import DotEnvSettingsSource

    original_values = dotenv.dotenv_values
    original_files = DotEnvSettingsSource._read_env_files

    def values(path=None, *args, **kwargs):
        if path is not None and Path(path).resolve() == repository / ".env":
            return {}
        return original_values(path, *args, **kwargs)

    def files(source):
        if source.env_file == ".env" and Path.cwd() == repository:
            return {}
        return original_files(source)

    dotenv.dotenv_values = values
    DotEnvSettingsSource._read_env_files = files
    original_popen = subprocess.Popen

    class FixturePopen(original_popen):
        def __init__(self, *args, **kwargs):
            environment = dict(os.environ if kwargs.get("env") is None else kwargs["env"])
            environment["PYTHONPATH"] = str(bootstrap) + os.pathsep + environment.get("PYTHONPATH", "")
            environment["NUSANTARA_VERIFICATION_OUTPUT"] = str(output)
            environment["NUSANTARA_VERIFICATION_REPOSITORY"] = str(repository)
            kwargs["env"] = environment
            super().__init__(*args, **kwargs)

    subprocess.Popen = FixturePopen

    def inside(value):
        path = Path(os.path.realpath(os.fsdecode(value)))
        return path == output or output in path.parents

    def deny(reason):
        raise RuntimeError("INTEGRATION_ISOLATION_BLOCKED: " + reason)

    def audit(event, args):
        if event == "sqlite3.connect" and str(args[0]) != ":memory:":
            database = args[0]
            if str(database).startswith("file:"):
                uri = urlsplit(str(database))
                if uri.netloc not in {"", "localhost"}:
                    deny("remote_database")
                if uri.path == ":memory:":
                    return
                database = url2pathname(uri.path)
            if not inside(database):
                deny("database_outside_output")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.path.realpath(os.fsdecode(args[0])))
            mode, flags = args[1:3]
            writing = isinstance(mode, str) and any(c in mode for c in "wax+")
            writing |= isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            declared_fixture = not writing and path in {
                repository / relative for relative in READ_ONLY_SOURCE_FIXTURES}
            if (repository / "data" in path.parents and not declared_fixture) or (
                path.name.startswith(".env") and path.name != ".env.example" and not inside(path)
            ):
                deny("production_read")
            raw_device = os.fsdecode(args[0]).replace("/", "\\").lower()
            null_device = os.name == "nt" and (
                path.name.lower() == "nul" or raw_device in {"nul", "\\\\.\\nul", "\\\\?\\nul"})
            if writing and not inside(path) and not null_device:
                deny("write_outside_output:" + os.fsdecode(args[0]))
        if event in {"os.remove", "os.rmdir", "os.mkdir"} and not inside(args[0]):
            if event != "os.mkdir" or not Path(args[0]).is_dir():
                deny("mutation_outside_output")
        if event in {"os.rename", "os.link", "os.symlink"}:
            if any(not inside(value) for value in args[:2]):
                deny("move_outside_output")
        if event in {"socket.connect", "socket.bind"}:
            address = args[1]
            if isinstance(address, tuple):
                if address[0] not in {"127.0.0.1", "::1", "localhost"}:
                    deny("external_network")
                if event == "socket.connect" and address[1] in {11434, 8765, 8000, 5180, 5179}:
                    deny("existing_service_port")
        if event == "socket.getaddrinfo" and args[0] not in {"127.0.0.1", "::1", "localhost", None}:
            deny("external_dns")
        if event == "subprocess.Popen":
            executable, command, cwd, environment = args
            if isinstance(command, str):
                prefix = command.lstrip()
                if prefix.startswith('"'):
                    first, _, remainder = prefix[1:].partition('"')
                else:
                    first, _, remainder = prefix.partition(' ')
                tokens = [first, *remainder.strip().split(maxsplit=6)]
            else:
                tokens = command
            name = Path(executable or tokens[0].strip('"')).name.lower()
            if name in {"git", "git.exe"}:
                target = tokens[tokens.index("-C") + 1].strip('"') if "-C" in tokens else cwd or Path.cwd()
                cursor = 1
                while cursor < len(tokens) and tokens[cursor] in {"-C", "-c"}:
                    cursor += 2
                operation = tokens[cursor:]
                readonly = tuple(operation) in {
                    ("status", "--short"), ("status", "--porcelain"),
                    ("rev-parse", "HEAD"), ("rev-parse", "--show-toplevel"),
                    ("rev-parse", "--abbrev-ref", "HEAD"), ("ls-files",), ("ls-files", "-z"),
                    ("branch", "--show-current"),
                    ("diff", "--name-only"), ("diff", "--stat"),
                }
                if not inside(target) and not readonly:
                    deny("git_outside_fixture")
            elif name == "powershell.exe":
                expected = ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File"]
                script = Path(tokens[-1].strip('"'))
                if (tokens[1:-1] != expected or not inside(script)
                        or script.name != "local-services-contract.ps1"
                        or script.read_bytes() != (repository / "tests/local-services-contract.ps1").read_bytes()):
                    deny("unsupported_powershell_fixture")
            elif name not in {"python", "python.exe", "python3", "python3.exe"}:
                deny("unsupported_subprocess")
            elif any(flag in tokens for flag in ("-I", "-S")):
                deny("python_without_bootstrap")
            elif str(bootstrap) not in (environment or os.environ).get("PYTHONPATH", ""):
                if environment is None:
                    deny("missing_child_guard")
                environment["PYTHONPATH"] = str(bootstrap) + os.pathsep + environment.get("PYTHONPATH", "")
                environment["NUSANTARA_VERIFICATION_OUTPUT"] = str(output)
                environment["NUSANTARA_VERIFICATION_REPOSITORY"] = str(repository)

    sys.addaudithook(audit)
