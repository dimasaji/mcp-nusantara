import sys
sys.path.insert(0, '.')
import asyncio
from app.hermes.agent import HermesAgent
from app.knowledge.engine import KnowledgeEngine
from app.core.gate_integration import GateIntegration
from app.trust.engine import TrustEngine
from app.api.routes import _run_sync_v1

# Import the actual helper functions from routes.py
from app.api.routes import (
    _extract_understanding_data,
    _extract_intent,
    _reconcile_problem_with_intent,
    _extract_entities,
    _get_problem_value,
    _build_evidence_text,
    _deterministic_response,
    _arithmetic_response,
    _build_system_prompt,
    _build_user_prompt,
    _model_dump,
)

agent = HermesAgent()

class MockReq:
    session_id = 't1'
    user_input = 'Apa itu Nusantara?'
    model = 'gemma4:e2b-it-q4_K_M'
    headers = {}
    document_ids = []

req = MockReq()

helpers = {
    '_extract_understanding_data': _extract_understanding_data,
    '_extract_intent': _extract_intent,
    '_reconcile_problem_with_intent': _reconcile_problem_with_intent,
    '_extract_entities': _extract_entities,
    '_get_problem_value': _get_problem_value,
    '_build_evidence_text': _build_evidence_text,
    '_deterministic_response': _deterministic_response,
    '_arithmetic_response': _arithmetic_response,
    '_build_system_prompt': _build_system_prompt,
    '_build_user_prompt': _build_user_prompt,
    '_model_dump': _model_dump,
}

async def call_agent():
    result = await agent.execute_v1(
        req,
        knowledge=KnowledgeEngine(),
        gates=GateIntegration(),
        trust=TrustEngine(),
        grounding=None,
        developer_core=None,
        run_sync=_run_sync_v1,
        policy=None,  # PolicyEngine will be created inside
        handoff=None,  # HandoffEngine will be created inside
        mcp=None,  # create_server will be called inside
        helpers=helpers
    )
    print("SUCCESS!")
    print("Type:", type(result))
    print("Response:", result.response[:300])
    print("\n=== payload keys ===")
    if hasattr(result, 'payload'):
        print(result.payload.keys())
    return result

asyncio.run(call_agent())
