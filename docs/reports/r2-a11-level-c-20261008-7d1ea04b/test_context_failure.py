"""Additional fail-closed context tests; reuse unchanged B2 synthetic fixture."""
import json
import pytest
import app.api.runtime_verification as owner
from test_b2_integration import boundary, store


@pytest.mark.parametrize('value',[None,{},object()])
def test_missing_runtime_instance_is_bounded(boundary,monkeypatch,value):
    controller,_,_=boundary
    store(controller)
    monkeypatch.setattr(owner,'current_runtime_instance',lambda:value)
    result=controller.receipt_assessment()
    assert result=={'status':'NOT_VERIFIED','correlation_valid':False,
        'reason':'CURRENT_CONTEXT_UNAVAILABLE','application_response_sent':False,
        'external_client_observed':False}


def test_process_observer_exception_does_not_leak_details(boundary,monkeypatch):
    controller,_,_=boundary
    store(controller)
    def failed(): raise ValueError('PRIVATE_PROCESS_CONTEXT_FAILURE')
    monkeypatch.setattr(owner,'_process_identity',failed)
    result=controller.receipt_assessment()
    assert result['reason']=='CURRENT_CONTEXT_UNAVAILABLE'
    assert result['status']=='NOT_VERIFIED' and not result['correlation_valid']
    assert 'PRIVATE_PROCESS_CONTEXT_FAILURE' not in json.dumps(result)
