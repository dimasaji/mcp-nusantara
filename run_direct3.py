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

# Create Ollama provider like routes.py does
provider = OllamaProvider(nusantara_config=None)

agent = HermesAgent(provider=provider, language_engine=None)
print("Provider:", type(agent.provider))
print("Provider health_check:", agent.provider.health_check)
print("Is async function:", asyncio.iscoroutinefunction(agent.provider.health_check))

async def call_agent():
    req = type('Req', (), {
        'session_id': 't1',
        'user_input': 'Apa itu Nusantara?',
        'model': 'gemma4:e2b-it-q4_K_M',
        'headers': {},
        'document_ids': []
    })()

    helpers = {
        '_extract_understanding_data': None, '_extract_intent': None,
        '_reconcile_problem_with_intent': None, '_extract_entities': None,
        '_get_problem_value': None, '_build_evidence_text': None,
        '_deterministic_response': None, '_arithmetic_response': None,
        '_build_system_prompt': None, '_build_user_prompt': None,
        '_model_dump': None,
    }

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
        print("SUCCESS!")
        print("Response:", result.response[:200])
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e))
        import traceback
        traceback.print_exc()

asyncio.run(call_agent())
