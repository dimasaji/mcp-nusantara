"""Exact bounded outcome and preservation; synthetic no-dispatch receipts only."""
import pytest
import app.api.runtime_verification as owner
from test_b2_integration import boundary, store


@pytest.mark.parametrize('observed',[{},None],ids=['empty_mapping','none'])
def test_incomplete_observer_is_bounded_without_mutating_receipt(boundary,monkeypatch,observed):
    controller,_,calls=boundary
    store(controller)
    receipt=controller.receipt
    observation=controller._receipt_observation
    monkeypatch.setattr(owner,'_process_identity',lambda:observed)
    assert controller.receipt_assessment()=={
        'status':'NOT_VERIFIED','correlation_valid':False,
        'reason':'CURRENT_CONTEXT_UNAVAILABLE',
        'application_response_sent':False,'external_client_observed':False,
    }
    assert controller.receipt is receipt
    assert controller._receipt_observation is observation
    assert controller.authorization.state=='DISARMED'
    assert controller.authorization.dispatch_count==0
    assert calls==[]
