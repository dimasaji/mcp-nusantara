from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.models.mock_provider import MockProvider
from app.models.router import ModelRouter
from app.policy.policy_engine import PolicyEngine
from app.trust.engine import TrustEngine
from app.memory.memory import MemoryStore
from app.tools.base import calculator
from app.mcp.mcp import MCPServer
from app.handoff.engine import HandoffEngine

def test_api_health():
    r=TestClient(app).get('/health'); assert r.status_code==200

def test_mock_and_router():
    p=MockProvider(); r=ModelRouter().register(p); assert r.route().provider.name=='mock'

def test_policy_trust_memory_tools():
    assert PolicyEngine().evaluate(action='query',data_sensitivity='public',risk_level='low').decision.value=='ALLOW'
    assert TrustEngine().evaluate(evidence=[],claim='x').supports_claim is False
    m=MemoryStore('test'); m.save('x',{'a':1}); assert m.get('x')['a']==1
    assert calculator({'operation':'add','a':2,'b':3})['result']==5

def test_mcp_handoff():
    s=MCPServer(); s.register_tool(name='x',description='x',input_schema={},handler=lambda x:{'ok':True}); assert s.list_tools()[0]['name']=='x'
    assert HandoffEngine().create_request('test').status=='pending'

def test_100_scenarios_exist():
    import json
    data=json.loads(Path('tests/evaluation/scenarios.json').read_text()); assert len(data)>=100
