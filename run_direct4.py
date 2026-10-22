import sys
sys.path.insert(0, '.')
import asyncio
from app.hermes.agent import HermesAgent
from app.models.ollama import OllamaProvider
from app.knowledge.engine import KnowledgeEngine
from app.core.gate_integration import GateIntegration
from app.trust.engine import TrustEngine
from app.api.routes import _run_sync_v1
from app.policy.policy_engine import PolicyEngine
from app.handoff.engine import HandoffEngine
from app.mcp.mcp import create_server

# Create Ollama provider
provider = OllamaProvider(nusantara_config=None)
agent = HermesAgent(provider=provider, language_engine=None)

class MockReq:
    session_id = 't1'
    user_input = 'Apa itu Nusantara?'
    model = 'gemma4:e2b-it-q4_K_M'
    headers = {}
    document_ids = []

req = MockReq()

# Import real helpers from routes
from app.api.routes import (_extract_understanding_data, _extract_intent,
                              _reconcile_problem_with_intent, _extract_entities,
                              _get_problem_value, _build_evidence_text,
                              _deterministic_response, _arithmetic_response,
                              _build_system_prompt, _build_user_prompt, _model_dump)

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
    try:
        result = await agent.execute_v1(
            req,
            knowledge=KnowledgeEngine(),
            gates=GateIntegration(),
            trust=TrustEngine(),
            grounding=None,
            developer_core=None,
            run_sync=_run_sync_v1,
            policy=PolicyEngine(),
            handoff=HandoffEngine(),
            mcp=create_server(),
            helpers=helpers
        )
        print('SUCCESS!')
        print('Response:', result.response[:200])
        print('Status:', result.status)
    except Exception as e:
        print('ERROR:', type(e).__name__, str(e))
        import traceback
        traceback.print_exc()

asyncio.run(call_agent())
