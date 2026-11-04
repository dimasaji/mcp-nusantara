"""Shared hardening must protect the active V1 request/response interfaces."""
import pytest
from fastapi import HTTPException
from test_v1_sop_boundary import api as api
from test_v1_sop_boundary import payload, send


@pytest.mark.parametrize('text', ['   ', '\x00\t\n'])
def test_invalid_input_is_rejected_before_provider_or_retrieval(api, text):
    with pytest.raises(HTTPException) as failure:
        send(api, text)
    assert failure.value.status_code == 422
    assert api.calls['construct'] == api.calls['model'] == api.calls['search'] == 0


def test_v1_normalizes_control_characters_before_history_and_generation(api):
    result = send(api, '  Halo\x00  ')
    assert result['response'] == 'Halo'


@pytest.mark.parametrize('response', ['', '   ', 'x' * 50001, None, {'command': 'fixture'}])
def test_invalid_output_is_rejected_without_truncating_or_coercing(api, response):
    with pytest.raises(HTTPException) as failure:
        api.ns['_project_v1_chat_response'](payload(response=response), intent_name='general')
    assert failure.value.status_code == 502
