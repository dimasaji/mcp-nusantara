"""Isolated artifact provenance; never full application or live execution proof."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json

import pytest

from app.core.runtime_identity import (BuildDefinition, BuildInput,
    BuildProvenanceOwner, ProcessBinding, assess_untrusted_build_provenance)


@pytest.fixture
def build():
    # Explicit synthetic artifact image; not Nusantara or interpreter evidence.
    content = {'app.py': b'VALUE = 1\n', 'asset.txt': b'asset',
               'dependency.py': b'DEPENDENCY = 1\n', 'interpreter.bin': b'test-only-image'}
    roles = ('APPLICATION_CODE', 'STATIC_ASSET', 'DEPENDENCY', 'INTERPRETER')
    inventory = tuple(zip(content, roles))
    inputs = tuple(BuildInput(name, role, 'sha256:' + hashlib.sha256(content[name]).hexdigest())
                   for name, role in inventory)
    definition = BuildDefinition(inventory, inputs)
    binding = ProcessBinding(1234, '2026-10-08T01:00:00+00:00', 'a' * 32)
    return definition, binding, content


def observed(build):
    definition, binding, content = build
    owner = BuildProvenanceOwner(definition, binding)
    for name, value in content.items():
        owner.observe_consumed_artifact(name, value)
    return owner


def test_matching_consumed_artifacts_do_not_manufacture_complete_execution(build):
    definition, binding, _ = build
    result = observed(build).assess(definition, binding)
    assert result['artifact_binding'] == 'VERIFIED'
    assert result['expected_build_id'] == result['observed_loaded_build_id'] == definition.build_id()
    assert result['status'] == 'NOT_VERIFIED'
    assert result['active_process_build'] == 'NOT_DIRECTLY_VERIFIED'
    assert result['runtime_identity'] == 'NOT_VERIFIED'
    assert result['reason'] == 'EXECUTION_CLOSURE_NOT_OBSERVED'


def test_mismatch_is_fail_closed(build):
    definition, binding, _ = build
    changed = replace(definition, inputs=(replace(definition.inputs[0], digest='sha256:'+'0'*64),
                                          *definition.inputs[1:]))
    result = observed(build).assess(changed, binding)
    assert result['reason'] == 'BUILD_MISMATCH'
    assert result['artifact_binding'] == result['status'] == 'NOT_VERIFIED'


def test_missing_expected(build):
    assert observed(build).assess(None, build[1])['reason'] == 'EXPECTED_BUILD_MISSING'


def test_missing_observed(build):
    definition, binding, _ = build
    assert BuildProvenanceOwner(definition, binding).assess(definition, binding)['reason'] == 'OBSERVED_LOADED_IDENTITY_MISSING'


@pytest.mark.parametrize('change', ['digest', 'role', 'inventory', 'duplicate', 'protected', 'traversal'])
def test_malformed_definition_is_bounded(build, change):
    definition, binding, _ = build
    altered = {
        'digest': replace(definition, inputs=(replace(definition.inputs[0], digest='PRIVATE_SECRET'),)),
        'role': replace(definition, inventory=(('app.py', []),)),
        'inventory': replace(definition, inventory=[('app.py', 'APPLICATION_CODE')]),
        'duplicate': replace(definition, inputs=definition.inputs + (definition.inputs[0],)),
        'protected': replace(definition, inventory=(('knowledge.db', 'APPLICATION_CODE'),)),
        'traversal': replace(definition, inventory=(('../app.py', 'APPLICATION_CODE'),)),
    }[change]
    result = observed(build).assess(altered, binding)
    assert result['status'] == 'NOT_VERIFIED'
    assert result['reason'] == 'MALFORMED_BUILD_DEFINITION'
    assert 'PRIVATE_SECRET' not in json.dumps(result)


def test_incomplete_definition_and_loaded_inventory(build):
    definition, binding, content = build
    incomplete = replace(definition, inputs=definition.inputs[:-1])
    assert observed(build).assess(incomplete, binding)['reason'] == 'INCOMPLETE_BUILD_DEFINITION'
    owner = BuildProvenanceOwner(definition, binding)
    owner.observe_consumed_artifact('app.py', content['app.py'])
    assert owner.assess(definition, binding)['reason'] == 'INCOMPLETE_LOADED_PROVENANCE'


@pytest.mark.parametrize('receipt', [None, {}, {'trusted': True, 'complete': True, 'status': 'VERIFIED'}])
def test_client_or_serialized_provenance_cannot_supply_authority(receipt):
    result = assess_untrusted_build_provenance(receipt)
    assert result['status'] == 'NOT_VERIFIED'
    assert result['reason'] == 'UNTRUSTED_PROVENANCE'


def test_determinism_and_inventory_order(build):
    definition, binding, _ = build
    reverse = replace(definition, inventory=tuple(reversed(definition.inventory)),
                      inputs=tuple(reversed(definition.inputs)))
    owner = observed(build)
    assert definition.build_id() == reverse.build_id()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: owner.assess(definition, binding), range(20)))
    assert all(result == results[0] for result in results)


@pytest.mark.parametrize('field,value,reason', [
    ('pid', 5678, 'PROCESS_IDENTITY_MISMATCH'),
    ('process_start', '2026-10-08T02:00:00+00:00', 'PROCESS_IDENTITY_MISMATCH'),
    ('runtime_instance_id', 'b'*32, 'RUNTIME_INSTANCE_MISMATCH'),
    ('pid', True, 'PROCESS_IDENTITY_MISSING_OR_MALFORMED'),
    ('process_start', 'bad', 'PROCESS_IDENTITY_MISSING_OR_MALFORMED'),
])
def test_process_reuse_and_instance_mismatch(build, field, value, reason):
    result = observed(build).assess(build[0], replace(build[1], **{field: value}))
    assert result['status'] == 'NOT_VERIFIED' and result['reason'] == reason


def test_missing_process_identity(build):
    assert observed(build).assess(build[0], None)['reason'] == 'PROCESS_IDENTITY_MISSING_OR_MALFORMED'


def test_conflicting_record_terminal_and_redaction_safe(build):
    owner = observed(build)
    with pytest.raises(ValueError, match='CONFLICTING'):
        owner.observe_consumed_artifact('app.py', b'PRIVATE_SECRET')
    result = owner.assess(build[0], build[1])
    assert result['reason'] == 'PROVENANCE_TERMINAL'
    assert 'PRIVATE_SECRET' not in json.dumps(result)
    assert 'PRIVATE_SECRET' not in repr(vars(owner))


def test_assessment_and_recording_do_not_open_files_or_network(build, monkeypatch):
    import builtins
    import socket
    import sqlite3
    def prohibited(*args, **kwargs):
        raise AssertionError('PROTECTED_IO')
    monkeypatch.setattr(builtins, 'open', prohibited)
    monkeypatch.setattr(socket.socket, 'connect', prohibited)
    monkeypatch.setattr(sqlite3, 'connect', prohibited)
    result = observed(build).assess(build[0], build[1])
    assert result['status'] == 'NOT_VERIFIED'


def test_helpers_are_in_existing_scoped_manifest():
    from fastapi import FastAPI
    from app.core.runtime_attestation import _loaded_code_manifest
    symbols = {name for name, _ in _loaded_code_manifest(FastAPI())}
    assert 'identity:app.core.runtime_build_provenance.BuildProvenanceOwner.assess' in symbols
    assert 'identity:app.core.runtime_build_provenance.BuildDefinition.validate' in symbols
