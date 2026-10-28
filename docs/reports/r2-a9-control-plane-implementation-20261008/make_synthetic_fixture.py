"""Test data only; never calls application projections or reads protected files."""
import json
from pathlib import Path
root = Path(__file__).parent
state = dict(schema_version=1, timestamp='2026-10-08T00:00:00Z', status='NOT_VERIFIED',system='SYNTHETIC TEST ONLY',
    current_phase='R3',phases=[dict(id='R4',name='Synthetic proposal',status='NOT_VERIFIED',evidence=['r3'],kind='PROPOSED')],
    contract=dict(id='synthetic',status='NOT_VERIFIED',evidence=['r3']),
    gates=[dict(id=f'R3.{i}',status='PASS',evidence=['r3']) for i in range(1,15)],
    evidence=[dict(id='r3',reference='synthetic fixture only',sha256='0'*64,status='VERIFIED_ARTIFACT')],
    verification=[],runtime=dict(configured_model='fixture',effective_model='fixture',selected_provider='fixture',actual_model='fixture',
        build_id='fixture',process_id=123,identity_status='FIXTURE_EVIDENCE',scope='HISTORICAL_CONTROLLED_RUNTIME',current_status='NOT_VERIFIED',evidence=['r3']),
    rag=dict(status='FIXTURE_EVIDENCE',evidence=['r3'],profile=dict(profile_id='fixture',profile_version=1,invocation_id='fixture',
        timestamp='fixture',consumer='fixture',correlation=dict(request_id='fixture',session_id='fixture',execution_id='fixture'),
        retrieval_strategy='fixture',effective_values=dict(top_k=1,candidate_count=1,semantic_weight=0.5,lexical_weight=0.5,
            rerank_requested=False,rerank_enabled=False,actual_reranker='fixture',embedding_identity={},knowledge_source={}),
        thresholds={},reranker_identity={},provenance={},execution_outcome={})),
    worktree=dict(status='UNKNOWN',files=[]),protected_assets=[dict(path=f'synthetic-{i}',status='UNCHANGED',evidence=[]) for i in range(2)],
    warnings=['Synthetic test data; not engineering evidence.'],blockers=['NOT_VERIFIED'],
    governance=dict(read_only=True,commit='NOT_AUTHORIZED',push='NOT_AUTHORIZED',acceptance=dict(R2='NOT_VERIFIED',R3='NOT_VERIFIED'),
        scope='SYNTHETIC TEST ONLY',rollback='No deployment',r3_integrity={},evidence=['r3']))
(root/'SYNTHETIC_NORMAL.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
