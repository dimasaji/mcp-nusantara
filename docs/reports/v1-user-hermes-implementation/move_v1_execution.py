"""Move the existing V1 pipeline intact into the existing Hermes class."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
path = ROOT / 'app/api/routes.py'
text = path.read_text(encoding='utf-8-sig')
start = text.index('        health = await provider.health_check()', text.index('async def chat('))
end = text.index('    except (HTTPException, ProviderUnavailableError):', start)
body = text[start:end]
a = body.index('        agent = HermesAgent(')
b = body.index('        # --------------------------------------------------------------\n        # KNOWLEDGE ENGINE', a)
body = body[:a] + '''        core = await _run_sync_v1(self.run, request.user_input,
            session_id=request.session_id, context=None)
        understanding = core['understanding']
        problem = core['problem']

''' + body[b:]
body = body.replace('return _project_v1_chat_response({', 'return V1CoreResult(payload={')
assert 'agent.' not in body
helpers = ['_extract_understanding_data', '_extract_intent', '_reconcile_problem_with_intent',
           '_extract_entities', '_get_problem_value', '_build_evidence_text', '_deterministic_response',
           '_build_system_prompt', '_build_user_prompt', '_model_dump']
prefix = '''
    async def execute_v1(self, request, *, knowledge, gates, trust, grounding,
                         developer_core, run_sync, helpers) -> V1CoreResult:
        """Own the existing V1 execution; transport projects its internal result.

        Services are the existing V1 owners, not replacement engines. Legacy run
        remains the language/problem/reasoning entry point for other consumers.
        """
        from app.knowledge.schemas import capture_retrieval
        provider = self.provider
        _knowledge, _gate_integration = knowledge, gates
        _trust_engine, _grounding_guard = trust, grounding
        _developer_core, _run_sync_v1 = developer_core, run_sync
'''
prefix += ''.join(f"        {name} = helpers['{name}']\n" for name in helpers)
agent_path = ROOT / 'app/hermes/agent.py'
agent = agent_path.read_text(encoding='utf-8-sig')
agent = agent.replace('from typing import Any, Dict, Optional', 'from typing import Any, Dict, Optional\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nimport time')
agent = agent.replace('class HermesAgent:', '''@dataclass(frozen=True)
class V1CoreResult:
    """Internal only; never serialize this object directly at the API boundary."""
    payload: dict
    intent_name: str


class HermesAgent:''')
agent += prefix + body
agent_path.write_text(agent, encoding='utf-8')
call = '''        agent = HermesAgent(provider=provider, language_engine=_language)
        core = await agent.execute_v1(request, knowledge=_knowledge, gates=_gate_integration,
            trust=_trust_engine, grounding=_grounding_guard, developer_core=_developer_core,
            run_sync=_run_sync_v1, helpers={
'''
call += ''.join(f"                '{name}': {name},\n" for name in helpers)
call += '''            })
        public = _project_v1_chat_response(core.payload, intent_name=core.intent_name)
        settings.record_v1_execution(revision=revision, model=public['model'],
            provider_status=public['provider_status'], grounded=public['grounding']['grounded'],
            stages=('HERMES_RUN', 'KNOWLEDGE', 'TRUST', 'GATES', 'GROUNDING', 'PUBLIC_PROJECTION'))
        return public

'''
text = text[:start] + call + text[end:]
text = text.replace('''        provider = OllamaProvider(
            nusantara_config=_configuration,
            model=request.model or None,
            model_source='REQUEST_OVERRIDE' if request.model else None,
        )''', '''        configuration, revision = settings.configuration_snapshot()
        if request.model and request.model != configuration.llm.model:
            raise HTTPException(409, 'Model dikendalikan operator; perbarui status model aktif.')
        provider = OllamaProvider(nusantara_config=configuration)''')
text = text.replace('''    try:

        with capture_retrieval('V1_KNOWLEDGE_SEARCH',''', '''    if request.filter:
        raise HTTPException(422, 'KNOWLEDGE_FILTER_NOT_SUPPORTED')

    try:

        with capture_retrieval('V1_KNOWLEDGE_SEARCH',''')
path.write_text(text, encoding='utf-8-sig')
print('Moved existing V1 execution into Hermes; route retains capture, safe errors, projection and cleanup.')
