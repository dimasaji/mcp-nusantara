"""Finalization is byte-exact, source-bound, write-once and does not approve humans."""
import json
from pathlib import Path
import pytest
from scripts.refresh_v1_evidence import finalize, publish, snapshot, write_once
from app.core.evidence_registry import collect_review_package


def prepared(tmp_path):
    root=tmp_path/'project';root.mkdir()
    (root/'control-plane').mkdir()
    (root/'source.txt').write_text('tested source')
    spec={'schema_version':1,'test_run_manifest':'current.json','criteria':[
        {'id':f'AC{i}','summary':'unit fixture only','sources':['source.txt'],'tests':['test_actual']} for i in range(1,16)]}
    (root/'control-plane/evidence-requirements.json').write_text(json.dumps(spec))
    folder=root/'runs/run-one';(folder/'python').mkdir(parents=True);(folder/'ui').mkdir()
    (folder/'python/python-results.xml').write_text('<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase name="test_actual"/></testsuite>')
    write_once(folder/'ui/vitest-results.json',{'numTotalTests':1,'testResults':[{'assertionResults':[{'title':'ui_actual','status':'passed'}]}]})
    before=snapshot(root,spec)
    write_once(folder/'source-before.json',before)
    write_once(folder/'commands.json',{'commands':['unit-fixture'],'exit_codes':[0]})
    isolation={k:True for k in ('network_blocked','filesystem_writes_scoped','active_data_blocked','subprocess_blocked','cache_isolated')}
    return root,folder,before,isolation


def test_finalized_results_mutation_is_rejected(tmp_path):
    root,folder,before,isolation=prepared(tmp_path)
    manifest=finalize(root,folder,before,['unit-fixture'],[0],isolation)
    package=publish(root,folder,manifest)
    assert package['pass_allowed'] is True
    assert not (root/'data').exists()  # No decision or runtime data is created.
    bundle=folder/'results-bundle.json'
    bundle.write_bytes(bundle.read_bytes()+b' ')  # Still valid JSON; byte integrity must reject it.
    invalid=collect_review_package(root)
    assert invalid['pass_allowed'] is False
    assert invalid['package_id']!=package['package_id']
    assert all(b['reason']=='TEST_RESULTS_HASH_MISMATCH' for b in invalid['blockers'])


def test_finalized_leaf_result_mutation_is_rejected(tmp_path):
    root,folder,before,isolation=prepared(tmp_path)
    manifest=finalize(root,folder,before,['unit-fixture'],[0],isolation)
    publish(root,folder,manifest)
    xml=folder/'python/python-results.xml';xml.write_bytes(xml.read_bytes()+b'\n')
    invalid=collect_review_package(root)
    assert all(b['reason']=='TEST_RESULT_ARTIFACT_HASH_MISMATCH' for b in invalid['blockers'])
    with pytest.raises(ValueError,match='FINALIZED_ARTIFACT_CHANGED'):publish(root,folder,manifest)


def test_finalization_rejects_source_change_and_failed_command(tmp_path):
    root,folder,before,isolation=prepared(tmp_path)
    with pytest.raises(ValueError,match='TEST_RUN_NOT_SUCCESSFUL'):finalize(root,folder,before,['unit-fixture'],[1],isolation)
    (root/'source.txt').write_text('not the tested source')
    with pytest.raises(ValueError,match='SOURCE_CHANGED_DURING_TESTS'):finalize(root,folder,before,['unit-fixture'],[0],isolation)
    assert not (root/'current.json').exists()


def test_finalized_run_cannot_be_replaced_or_reference_itself(tmp_path):
    root,folder,before,isolation=prepared(tmp_path)
    manifest=finalize(root,folder,before,['unit-fixture'],[0],isolation)
    original=manifest.read_bytes()
    with pytest.raises(ValueError,match='RUN_ALREADY_FINALIZED'):finalize(root,folder,before,['unit-fixture'],[0],isolation)
    assert manifest.read_bytes()==original
    bundle=json.loads((folder/'results-bundle.json').read_text())
    assert all(not item['path'].endswith('test-run.json') for item in bundle['artifacts'])
