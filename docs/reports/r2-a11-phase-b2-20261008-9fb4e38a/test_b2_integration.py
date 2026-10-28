"""Synthetic no-dispatch integration; no live provider or authorization proof."""
import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect
import json
import os
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import app.api.runtime_verification as owner
from app.core.nusantara_config import load_nusantara_config
from app.core.runtime_correlation import CorrelationReceipt


@pytest.fixture
def boundary(tmp_path):
    configuration=load_nusantara_config(project_root=tmp_path,environment={},overrides={
        'runtime':{'profile':'ATTESTATION'},'llm':{'model':'synthetic-model'}})
    controller=owner.VerificationController(configuration)
    controller.bind_loaded_code(lambda:'sha256:'+'f'*64)
    calls=[]
    def prohibited(request):
        calls.append(request)
        raise AssertionError('NO_DISPATCH_TEST_BOUNDARY')
    transport=httpx.MockTransport(prohibited)
    yield controller,transport,calls
    assert not calls
    assert controller.authorization.state=='DISARMED'
    assert controller.authorization.dispatch_count==0


def synthetic(controller):
    stamp=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
    instance=owner.current_runtime_instance()
    return CorrelationReceipt('synthetic-request','synthetic-invocation',instance.runtime_instance_id,
        os.getpid(),owner.BUILD_ID,controller._code_hash,'ollama',controller.endpoint,
        'synthetic-model',stamp,stamp,True,False,1,'PROVIDER_RESPONSE_CORRELATED')


def store(controller,*,provenance='PROVIDER_RESPONSE',receipt=None):
    # Explicit synthetic trusted-context seam, never claimed to be genuine evidence.
    receipt=synthetic(controller) if receipt is None else receipt
    controller._store(receipt,process_start=owner._process_identity()['process_start_time'],
                      evidence_class=provenance)
    return receipt


def test_actual_creation_classification_storage_ast_with_mock_is_not_live(boundary):
    controller,transport,calls=boundary
    source=ast.parse(inspect.getsource(owner.VerificationController))
    invoke=next(n for n in source.body[0].body if isinstance(n,ast.AsyncFunctionDef) and n.name=='invoke')
    body=next(n for n in invoke.body if isinstance(n,ast.Try)).body
    selected=[n for n in body if
        (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)
         and n.targets[0].id in {'evidence_class','receipt'}) or
        (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
         and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='_store')]
    assert len(selected)==3
    # Execute only classification, immutable receipt construction and _store.
    # Never execute invoke/reserve/client/provider/dispatch or any await.
    assert not any(isinstance(n,ast.Await) for statement in selected for n in ast.walk(statement))
    generated=ast.Module(body=selected,type_ignores=[])
    namespace=dict(vars(owner))
    namespace.update(self=controller,transport=SimpleNamespace(_transport=transport),
        identity={'actual_model':'synthetic-model','invocation_id':'synthetic-invocation'},
        instance=owner.current_runtime_instance(),request_id='synthetic-request',
        started=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),
        process_start=owner._process_identity()['process_start_time'])
    # Constructor's count is synthetic input; real authorization remains zero.
    class NoDispatchDouble:
        dispatch_count=1
    real_authorization=controller.authorization
    controller.authorization=NoDispatchDouble()
    try:
        exec(compile(generated,owner.__file__,'exec'),namespace)
    finally:
        controller.authorization=real_authorization
    assert controller.receipt is namespace['receipt']
    assert controller._receipt_observation.receipt is controller.receipt
    assert controller._receipt_observation.evidence_class=='TEST_ISOLATED'
    assessment=controller.receipt_assessment()
    assert assessment['status']=='NOT_VERIFIED' and not assessment['correlation_valid']
    assert assessment['reason']=='NO_GENUINE_PROVIDER_OBSERVATION'


def test_synthetic_trusted_context_storage_assessment_stays_not_verified(boundary):
    controller,_,_=boundary
    receipt=store(controller)
    assessment=controller.receipt_assessment()
    assert assessment['correlation_valid'] and assessment['status']=='NOT_VERIFIED'
    assert not assessment['application_response_sent'] and not assessment['external_client_observed']
    assert controller._receipt_observation.receipt is receipt
    assert datetime.fromisoformat(controller._receipt_observation.expires_at)>datetime.now(timezone.utc)


@pytest.mark.parametrize('provenance',['UNVERIFIED','TEST_ISOLATED','UNKNOWN',None])
def test_provenance_fails_closed(boundary,provenance):
    controller,_,_=boundary
    store(controller,provenance=provenance)
    result=controller.receipt_assessment()
    assert not result['correlation_valid'] and result['status']=='NOT_VERIFIED'


def test_missing_receipt_and_conflicting_replacement(boundary):
    controller,_,_=boundary
    assert not controller.receipt_assessment()['correlation_valid']
    first=store(controller)
    observation=controller._receipt_observation
    with pytest.raises(ValueError,match='CONFLICTING_RECEIPT_REPLACEMENT'):
        store(controller,receipt=replace(first,invocation_id='conflicting'))
    assert controller.receipt is first and controller._receipt_observation is observation


@pytest.mark.parametrize('change',['process_start','runtime_instance','source','scoped_code','pid'])
def test_runtime_context_change_fails_closed(boundary,monkeypatch,change):
    controller,_,_=boundary
    store(controller)
    if change=='process_start':
        process=owner._process_identity()
        monkeypatch.setattr(owner,'_process_identity',lambda:{**process,'process_start_time':'2000-01-01T00:00:00+00:00'})
    elif change=='runtime_instance':
        instance=owner.current_runtime_instance()
        monkeypatch.setattr(owner,'current_runtime_instance',lambda:replace(instance,runtime_instance_id='new-instance'))
    elif change=='source': monkeypatch.setattr(owner,'BUILD_ID','sha256:'+'0'*64)
    elif change=='scoped_code': monkeypatch.setattr(controller,'_code_observer',lambda:'sha256:'+'0'*64)
    else:
        with monkeypatch.context() as local:
            local.setattr(owner.os,'getpid',lambda:123)
            result=controller.receipt_assessment()
        assert not result['correlation_valid']
        return
    assert not controller.receipt_assessment()['correlation_valid']


@pytest.mark.parametrize('timestamp',['invalid PRIVATE_TIMESTAMP_VALUE',None,'2026-10-08T00:00:00'])
def test_timestamp_failure_is_bounded(boundary,timestamp):
    controller,_,_=boundary
    store(controller,receipt=replace(synthetic(controller),completed_at=timestamp))
    result=controller.receipt_assessment()
    assert not result['correlation_valid'] and len(result['reason'])<=64
    assert 'PRIVATE_TIMESTAMP_VALUE' not in json.dumps(result)


@pytest.mark.parametrize('result',[{},None,{'process_start_time':None}])
def test_incomplete_process_observer_fails_closed(boundary,monkeypatch,result):
    controller,_,_=boundary
    store(controller)
    monkeypatch.setattr(owner,'_process_identity',lambda:result)
    assessment=controller.receipt_assessment()
    assert assessment['status']=='NOT_VERIFIED' and not assessment['correlation_valid']
    assert len(assessment['reason'])<=64


def test_raising_observer_is_bounded(boundary,monkeypatch):
    controller,_,_=boundary
    store(controller)
    def unavailable(): raise RuntimeError('PRIVATE_OBSERVER_FAILURE')
    monkeypatch.setattr(controller,'_code_observer',unavailable)
    result=controller.receipt_assessment()
    assert result['reason']=='CURRENT_CONTEXT_UNAVAILABLE' and not result['correlation_valid']
    assert 'PRIVATE_OBSERVER_FAILURE' not in json.dumps(result)
