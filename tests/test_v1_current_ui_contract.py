"""Behavior behind the authorized main-handler baseline update."""
import asyncio
from pathlib import Path
import pytest
from fastapi import HTTPException
from app import main

@pytest.mark.parametrize('profile', ['NORMAL','ATTESTATION','EVIDENCE_ONLY'])
def test_dashboard_profile_contract(tmp_path,monkeypatch,profile):
    monkeypatch.setattr(main,'_READ_ONLY_EVIDENCE',profile=='EVIDENCE_ONLY')
    monkeypatch.setattr(main,'_ATTESTATION',profile=='ATTESTATION')
    monkeypatch.setattr(main,'CONTROL_PLANE_BUNDLE',tmp_path)
    if profile=='EVIDENCE_ONLY':
        with pytest.raises(HTTPException) as error:asyncio.run(main.dashboard())
        assert error.value.status_code==404
    elif profile=='ATTESTATION':
        assert Path(asyncio.run(main.dashboard()).path)==main.UI_FILE
    else:
        with pytest.raises(HTTPException) as error:asyncio.run(main.dashboard())
        assert error.value.status_code==503
        (tmp_path/'index.html').write_text('<html>built app</html>')
        assert Path(asyncio.run(main.dashboard()).path)==tmp_path/'index.html'
