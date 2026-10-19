from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.control_plane import router
from app.models.cost_ledger import CostLedger


def test_readonly_existing_ledger_survives_process_without_runtime_attachment(tmp_path, monkeypatch):
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'isolated-cost-summary')
    root = tmp_path / 'repository'
    path = root / 'data/openrouter_cost_v1.db'
    ledger = CostLedger(path, budget_usd='1.00', per_request_cap_usd='0.05')
    ledger.reserve('unknown-result', '0.05')
    ledger.mark_unknown('unknown-result')
    before = path.read_bytes()
    app = FastAPI()
    app.state.configuration_owner = type('Owner', (), {'configuration_snapshot': lambda self:
        (type('Configuration', (), {'paths': type('Paths', (), {'project_root': str(root)})()})(), 0)})()
    app.include_router(router)
    response = TestClient(app).get('/v1/control-plane/cost-summary', headers={'X-Admin-Token': 'isolated-cost-summary'})
    assert response.json()['status'] == 'AVAILABLE'
    assert response.json()['reserved_usd'] == '0.05'
    assert response.json()['remaining_budget_usd'] == '0.95'
    assert path.read_bytes() == before


def test_cost_summary_requires_auth_and_reads_existing_ledger(tmp_path, monkeypatch):
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'isolated-cost-summary')
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    path = '/v1/control-plane/cost-summary'
    assert client.get(path).status_code == 403
    headers = {'X-Admin-Token':'isolated-cost-summary'}
    assert client.get(path, headers=headers).json()['status'] == 'UNAVAILABLE'
    ledger = CostLedger(tmp_path/'cost.db', budget_usd='1.00', per_request_cap_usd='0.10')
    ledger.reserve('isolated-request', '0.10')
    app.state.cost_ledger = ledger
    response = client.get(path, headers=headers)
    assert response.status_code == 200
    assert response.json()['remaining_budget_usd'] == '0.90'
    assert response.json()['provider_balance_usd'] is None
