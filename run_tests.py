"""Nusantara Core + Hermes verification runner for Phases 0-18."""
from __future__ import annotations
import importlib, json
from pathlib import Path
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parent
PASS=[]; FAIL=[]

def check(name, fn):
    try:
        fn(); PASS.append(name); print(f'PASS  {name}')
    except Exception as exc:
        FAIL.append((name,str(exc))); print(f'FAIL  {name}: {exc}')

def main():
    check('Phase 0 documentation', lambda: [(_ for _ in ()).throw(AssertionError(f'missing {p}')) for p in ['architecture.md','development-principles.md','roadmap.md','architecture-decisions.md'] if not (ROOT/'docs'/p).exists()])
    modules=['app.main','app.core.config','app.models.base','app.models.ollama_provider','app.models.mock_provider','app.models.router','app.language.engine','app.context.engine','app.problem.engine','app.knowledge.rag','app.reasoning.engine','app.workflow.engine','app.policy.policy_engine','app.trust.engine','app.memory.memory','app.tools.base','app.mcp.mcp','app.handoff.engine','app.api.routes','app.hermes.agent']
    check('Phase 1-15 imports', lambda: [importlib.import_module(m) for m in modules])
    from app.models.mock_provider import MockProvider
    from app.models.router import ModelRouter
    check('Phase 2 Ollama-compatible provider abstraction', lambda: (_ for _ in ()).throw(AssertionError('router failed')) if ModelRouter().register(MockProvider()).route().provider.name!='mock' else None)
    from app.language.normalizer import normalize_text
    from app.language.intent import verify_examples
    from app.language.entity import extract_entities
    check('Phase 3 language engine', lambda: (assert_true(normalize_text('ktp blm jadi').normalized), assert_true(verify_examples()['total']>=30), assert_true(len(extract_entities('NIK 1234567890123456').entities)>0)))
    from app.context.context_builder import ContextBuilder
    check('Phase 4 context', lambda: assert_true(ContextBuilder().build('s1','Halo',[('user','Halo')]).session_id=='s1'))
    from app.problem.engine import ProblemEngine
    check('Phase 5 problem', lambda: assert_true(ProblemEngine().analyze('KTP saya hilang').has_problem))
    from app.knowledge.rag import create_rag
    check('Phase 6 RAG engine imports', lambda: assert_true(create_rag() is not None))
    from app.reasoning.engine import ReasoningEngine
    def verify_reasoning():
        engine = ReasoningEngine()
        assert_true(engine.analyze('KTP hilang').status == 'insufficient_evidence')
        grounded = engine.analyze('KTP hilang', evidence=[{
            'document_id': 'fixture-smoke', 'chunk': 'Synthetic verification evidence.', 'score': 0.9,
        }], intent_confidence=0.9)
        assert_true(grounded.status == 'grounded' and grounded.facts and grounded.inferences)
    check('Phase 7 reasoning', verify_reasoning)
    from app.workflow.engine import WorkflowEngine
    check('Phase 8 workflow', lambda: assert_true(WorkflowEngine().complete(WorkflowEngine().create_workflow({'name':'x'}),True).status=='completed'))
    from app.policy.policy_engine import PolicyEngine
    check('Phase 9 policy', lambda: assert_true(PolicyEngine().evaluate(action='query',data_sensitivity='public',risk_level='low').decision.value=='ALLOW'))
    from app.trust.engine import TrustEngine
    check('Phase 10 trust', lambda: assert_true(TrustEngine().evaluate([], 'claim').supports_claim is False))
    from app.memory.memory import MemoryStore
    check('Phase 11 memory', lambda: (lambda m:(m.save('x',{'a':1}), assert_true(m.get('x')['a']==1)))(MemoryStore('test')))
    from app.tools.base import calculator
    check('Phase 12 tools', lambda: assert_true(calculator({'operation':'add','a':2,'b':3})['result']==5))
    from app.mcp.mcp import MCPServer
    check('Phase 13 MCP', lambda: (lambda s:(s.register_tool(name='x',description='x',input_schema={},handler=lambda x:{'ok':True}), assert_true(len(s.list_tools())==1)))(MCPServer()))
    from app.handoff.engine import HandoffEngine
    check('Phase 14 handoff', lambda: assert_true(HandoffEngine().create_request('test').status=='pending'))
    check('Phase 15 API gateway', lambda: assert_true(TestClient(importlib.import_module('app.main').app).get('/v1/health').status_code==200))
    check('Phase 16 UI', lambda: assert_true((ROOT/'app/ui/index.html').exists()))
    scenarios=json.loads((ROOT/'tests/evaluation/scenarios.json').read_text())
    check('Phase 17 evaluation scaffold >=100', lambda: assert_true(len(scenarios)>=100))
    check('Phase 18 Docker hardening files', lambda: [assert_true((ROOT/p).exists()) for p in ['Dockerfile','docker-compose.yml','.dockerignore','scripts/start.sh','scripts/healthcheck.sh','scripts/test.sh']])
    print(f'\nRESULT: {len(PASS)} passed, {len(FAIL)} failed')
    if FAIL:
        for n,e in FAIL: print(f' - {n}: {e}')
        return 1
    return 0

def assert_true(value):
    if not value: raise AssertionError('condition is false')
    return True

if __name__=='__main__': raise SystemExit(main())
