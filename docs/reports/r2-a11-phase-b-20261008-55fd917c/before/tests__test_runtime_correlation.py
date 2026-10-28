"""ATTESTATION profile/permit/transport tests; no real model or listener."""
import asyncio
import dataclasses
from concurrent.futures import ThreadPoolExecutor
import json
import time

import httpx
import pytest

from app.core.nusantara_config import ConfigurationError, load_nusantara_config
from app.core.runtime_correlation import (CorrelationReceipt, EndpointBinding,
    OneDispatchTransport, OneUseAuthorization)


def configuration(tmp_path, **llm):
    return load_nusantara_config(project_root=tmp_path,
        overrides={'runtime': {'profile': 'ATTESTATION'}, **({'llm': llm} if llm else {})})


def test_profile_uses_existing_configuration_precedence_and_normal_default(tmp_path):
    normal = load_nusantara_config(project_root=tmp_path)
    assert normal.runtime.profile == 'NORMAL'
    assert normal.llm.model == 'llama3.2:1b' and normal.llm.provider == 'ollama'
    path = tmp_path/'profile.json'
    path.write_text(json.dumps({'runtime': {'profile': 'ATTESTATION'}}))
    file = load_nusantara_config(project_root=tmp_path, config_file=path)
    assert file.runtime.profile == 'ATTESTATION'
    env = load_nusantara_config(project_root=tmp_path, config_file=path,
                               environment={'NUSANTARA_RUNTIME_PROFILE': 'NORMAL'})
    assert env.runtime.profile == 'NORMAL'
    explicit = load_nusantara_config(project_root=tmp_path,
        environment={'NUSANTARA_RUNTIME_PROFILE': 'NORMAL'}, overrides={'runtime': {'profile': 'ATTESTATION'}})
    assert explicit.runtime.profile == 'ATTESTATION'
    assert next(p.source for p in explicit.provenance if p.field == 'runtime.profile') == 'EXPLICIT'
    assert normal.llm == explicit.llm


@pytest.mark.parametrize('profile', ['attestation', 'UNKNOWN', '', None, True])
def test_unknown_profiles_fail_closed(tmp_path, profile):
    with pytest.raises(ConfigurationError):
        load_nusantara_config(project_root=tmp_path, overrides={'runtime': {'profile': profile}})


@pytest.mark.parametrize('endpoint', ['http://example.com:11434', 'https://localhost:11434',
    'http://127.0.0.1:11434/proxy', 'http://192.0.2.1:11434'])
def test_unbound_endpoint_rejected(tmp_path, endpoint):
    with pytest.raises(ValueError):
        EndpointBinding.from_configuration(configuration(tmp_path, base_url=endpoint))


def test_localhost_is_explicitly_bound_without_configuration_rewrite(tmp_path):
    config = configuration(tmp_path)
    binding = EndpointBinding.from_configuration(config)
    assert binding.origin == config.llm.base_url
    assert binding.connection_origin == 'http://127.0.0.1:11434'
    assert config.llm.base_url == 'http://localhost:11434'


def test_server_grant_is_disarmed_expiring_single_use_and_never_rearmed(monkeypatch):
    grant = OneUseAuthorization()
    assert grant.state == 'DISARMED'
    with pytest.raises(ValueError):
        grant.reserve('not-authorized')
    token = grant.grant(ttl_s=30)
    with pytest.raises(ValueError):
        grant.reserve('wrong')
    grant.reserve(token)
    grant.dispatch()
    grant.finish()
    assert grant.state == 'TERMINAL' and grant.dispatch_count == 1
    with pytest.raises(ValueError):
        grant.reserve(token)
    with pytest.raises(ValueError):
        grant.grant()
    expired = OneUseAuthorization()
    token2 = expired.grant(ttl_s=1)
    future = time.monotonic()+5
    monkeypatch.setattr(time, 'monotonic', lambda: future)
    with pytest.raises(ValueError, match='EXPIRED'):
        expired.reserve(token2)
    assert expired.dispatch_count == 0


def test_concurrent_reservations_have_one_winner():
    grant = OneUseAuthorization()
    token = grant.grant()
    def reserve(_):
        try:
            grant.reserve(token)
            return True
        except ValueError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(reserve, range(16))) == 1
    grant.finish()
    assert grant.dispatch_count == 0  # reservation already consumed even before dispatch


def test_fork_or_instance_replacement_cannot_use_grant(monkeypatch):
    import app.core.runtime_correlation as owner
    grant = OneUseAuthorization()
    token = grant.grant()
    monkeypatch.setattr(owner.os, 'getpid', lambda: -1)
    with pytest.raises(ValueError):
        grant.reserve(token)


def test_receipt_and_nested_endpoint_are_immutable_and_contain_no_content():
    receipt = CorrelationReceipt('req', 'inv', 'instance', 1, 'source', 'scoped', 'ollama',
        EndpointBinding('http://localhost:11434', 'http://127.0.0.1:11434'), 'actual',
        'start', 'complete', True, False, 1, 'PROVIDER_RESPONSE_CORRELATED')
    with pytest.raises(dataclasses.FrozenInstanceError):
        receipt.actual_model = 'other'
    with pytest.raises(dataclasses.FrozenInstanceError):
        receipt.provider_endpoint.origin = 'other'
    assert not {'prompt', 'content', 'response_content', 'authorization'} & dataclasses.asdict(receipt).keys()
    assert receipt.full_application_build_verified is False


@pytest.mark.asyncio
async def test_transport_rejects_health_alternate_paths_and_second_dispatch(monkeypatch):
    seen = []
    monkeypatch.setattr(httpx, 'AsyncHTTPTransport', lambda **kw: httpx.MockTransport(
        lambda req: (seen.append(req), httpx.Response(200, json={'done': True}))[1]))
    grant = OneUseAuthorization()
    grant.reserve(grant.grant())
    endpoint = EndpointBinding('http://localhost:11434', 'http://127.0.0.1:11434')
    transport = OneDispatchTransport(endpoint, grant)
    async with httpx.AsyncClient(transport=transport, follow_redirects=False, trust_env=False) as client:
        for method, url in [('GET', endpoint.origin+'/api/tags'), ('POST', 'http://example.com/api/generate')]:
            with pytest.raises(ValueError):
                await client.request(method, url)
        assert grant.dispatch_count == 0
        await client.post(endpoint.origin+'/api/generate', json={'model': 'fixture'})
        with pytest.raises(ValueError):
            await client.post(endpoint.origin+'/api/generate', json={'model': 'fixture'})
    assert len(seen) == grant.dispatch_count == 1
    assert seen[0].url.host == '127.0.0.1'
    assert seen[0].headers['host'] == 'localhost:11434'
