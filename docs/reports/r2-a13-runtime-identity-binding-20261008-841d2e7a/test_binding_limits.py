"""Actual counterexamples against existing coverage; not a synthetic full-build PASS."""
import asyncio
import json
from fastapi import FastAPI
from app.core.runtime_attestation import _loaded_code_manifest, _manifest_hash
from app.core.runtime_identity import source_build_id


def test_import_time_snapshot_can_stay_old_while_disk_identity_changes(tmp_path):
    source=tmp_path/'app';source.mkdir()
    module=source/'main.py';module.write_text('value = 1\n')
    namespace={};exec('BUILD_ID = supplied_snapshot',{'supplied_snapshot':source_build_id(tmp_path)},namespace)
    captured=namespace['BUILD_ID']
    module.write_text('value = 2\n')
    assert namespace['BUILD_ID']==captured
    assert source_build_id(tmp_path)!=captured


def test_unchanged_disk_hash_is_deterministic(tmp_path):
    source=tmp_path/'app';source.mkdir();(source/'main.py').write_text('value = 1\n')
    assert source_build_id(tmp_path)==source_build_id(tmp_path)


def test_equal_registered_code_hash_does_not_cover_changed_global():
    namespace={'__name__':'isolated_global_fixture','value':'before'}
    exec('async def handler():\n    return value\n',namespace)
    app=FastAPI();app.add_api_route('/fixture',namespace['handler'])
    original=_manifest_hash(_loaded_code_manifest(app))
    assert asyncio.run(namespace['handler']())=='before'
    namespace['value']='after'
    assert asyncio.run(namespace['handler']())=='after'
    assert _manifest_hash(_loaded_code_manifest(app))==original


def test_registered_manifest_does_not_cover_transitive_helper_code():
    namespace={'__name__':'isolated_transitive_fixture'}
    exec('def helper():\n    return "before"\nasync def handler():\n    return helper()\n',namespace)
    app=FastAPI();app.add_api_route('/fixture',namespace['handler'])
    original=_manifest_hash(_loaded_code_manifest(app))
    assert asyncio.run(namespace['handler']())=='before'
    replacement={};exec('def changed():\n    return "after"\n',replacement)
    namespace['helper'].__code__=replacement['changed'].__code__
    assert asyncio.run(namespace['handler']())=='after'
    assert _manifest_hash(_loaded_code_manifest(app))==original


def test_source_algorithm_has_no_record_of_bytes_used_by_a_loader(tmp_path):
    source=tmp_path/'app';source.mkdir();module=source/'main.py'
    module.write_text('value = "before"\n')
    loaded={};exec(compile(module.read_text(),str(module),'exec'),loaded)
    module.write_text('value = "after"\n')
    disk=source_build_id(tmp_path)
    assert loaded['value']=='before'
    assert disk==source_build_id(tmp_path)
    # The disk hash alone records no relationship to the already executed namespace.
    assert 'BUILD_ID' not in loaded and isinstance(disk,str)
