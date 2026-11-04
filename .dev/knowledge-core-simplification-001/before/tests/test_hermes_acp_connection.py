from app.developer_core.hermes_acp_connection import _classify_stderr
from app.developer_core.hermes_acp_connection import _exchange
from pathlib import Path
import sys
import pytest


def test_install_state_permission_failure_is_safe_and_actionable():
    detail = (
        r"hermes: install state is not writable by this user "
        r"(C:\Users\operator\AppData\Local\hermes\installs\private\pm-runtime\.prepare.lock); "
        r"run as the install owner or grant write access"
    )

    assert _classify_stderr(detail) == "HERMES_INSTALL_STATE_NOT_WRITABLE"


def test_missing_hermes_dependency_has_a_distinct_safe_code():
    assert _classify_stderr("ModuleNotFoundError: No module named 'acp'") == "HERMES_DEPENDENCY_UNAVAILABLE"


def test_unrecognized_stderr_does_not_escape_into_public_status():
    assert _classify_stderr("private output and credentials") == "ACP_CONNECTION_CLOSED"


def test_closed_acp_process_maps_known_stderr_without_exposing_its_path():
    child = [
        sys.executable,
        "-c",
        "import sys; sys.stdin.readline(); print(r'install state is not writable by this user (C:\\private\\.prepare.lock)', file=sys.stderr)",
    ]

    with pytest.raises(ValueError, match="HERMES_INSTALL_STATE_NOT_WRITABLE"):
        _exchange(child, Path.cwd(), timeout=3)


def test_initialize_handshake_accepts_only_hermes_agent_identity():
    response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": 1,
            "agentInfo": {"name": "hermes-agent", "version": "test-version"},
            "authMethods": [],
        },
    }
    child = [
        sys.executable,
        "-c",
        "import json,sys; sys.stdin.readline(); print(json.dumps(" + repr(response) + "))",
    ]

    observed = _exchange(child, Path.cwd(), timeout=3)

    assert observed["agent_name"] == "hermes-agent"
    assert observed["protocol_version"] == 1
    assert observed["agent_version"] == "test-version"
