# Rollback Plan — LangChain & LangGraph Integration

## Feature Flags
- `NUS_LANGCHAIN_ENABLED=false` (default)
- `NUS_LANGGRAPH_ENABLED=false` (default)

## Rollback Steps
1. Set both flags to `false` in `.env` or environment.
2. Restart backend.
3. System reverts to existing Nusantara pipeline (no LangChain/LangGraph code executed).

## Data Safety
- No changes to existing database schema.
- No new indexes created.
- No changes to existing Knowledge data.
- Checkpoint data (if created) is per-workflow-run, not system-wide.

## Rollback Triggers
- LangChain adapter fails to produce correct results.
- LangGraph workflow causes errors.
- Performance degradation.
- Any regression in existing tests.

## Verification After Rollback
- Run `pytest tests/test_backend_runtime_fixture.py tests/test_knowledge_pipeline.py tests/test_sop_review.py`
- Verify chat search works on 4 Aktif SOPs.
- Verify approval workflow unchanged.
PY