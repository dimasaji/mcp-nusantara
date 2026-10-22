"""Behavior behind the authorized main-handler baseline update."""
import asyncio
from pathlib import Path
import pytest
from fastapi import HTTPException
from starlette.requests import Request
from app import main

@pytest.mark.parametrize('profile', ['NORMAL','ATTESTATION','EVIDENCE_ONLY'])
def test_dashboard_profile_contract(tmp_path,monkeypatch,profile):
    monkeypatch.setattr(main,'_READ_ONLY_EVIDENCE',profile=='EVIDENCE_ONLY')
    monkeypatch.setattr(main,'_ATTESTATION',profile=='ATTESTATION')
    monkeypatch.setattr(main,'CONTROL_PLANE_BUNDLE',tmp_path)
    request=Request({'type':'http','scheme':'http','server':('testserver',80),
                     'path':'/dashboard','headers':[],'query_string':b'tab=tasks'})
    if profile=='EVIDENCE_ONLY':
        with pytest.raises(HTTPException) as error:asyncio.run(main.dashboard(request))
        assert error.value.status_code==404
    elif profile=='ATTESTATION':
        assert Path(asyncio.run(main.dashboard(request)).path)==main.UI_FILE
    else:
        response=asyncio.run(main.dashboard(request))
        assert response.status_code==307
        host=main._LOCAL_SERVICES.get('host','127.0.0.1')
        port=main._LOCAL_SERVICES['frontendPort']
        assert response.headers['location']==f'http://{host}:{port}/dashboard?tab=tasks'
