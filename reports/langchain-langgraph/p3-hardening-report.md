# P3 Hardening Report — LangChain & LangGraph Integration

## Test Commands
```
pytest tests/test_langchain_hardening.py -q
```

## Results
- **13 passed, 0 failed, 9 warnings** (18.18s)

## Test Coverage

### A. Feature Flags
| Test | Result |
|---|---|
| Both flags OFF: legacy path works | PASS |
| LangChain ON: adapter available | PASS |
| LangGraph ON: workflow available | PASS |
| Flags evaluated at call time | PASS |

### B. Failure Handling
| Test | Result |
|---|---|
| Empty retrieval results -> abstention | PASS |
| No evidence -> abstention/no crash | PASS |

### C. Session and Security
| Test | Result |
|---|---|
| Session isolation | PASS |
| Public no access (no token) | PASS |
| No stack trace in error | PASS |

### D. API Compatibility
| Test | Result |
|---|---|
| Response schema compatible | PASS |
| Request contract unchanged | PASS |

### E. Regression
| Test | Result |
|---|---|
| Hermes V1 conversation works | PASS |
| Knowledge search still works | PASS |

## Changed Files
- `app/api/routes.py` — LangGraph chat integration (feature-flagged)
- `app/knowledge/langchain_adapter.py` — adapter (feature-flagged, call-time env check)
- `app/knowledge/langgraph_chat.py` — chat workflow (real services, async handling)
- `app/core/config.py` — feature flags (nus_langchain_enabled, nus_langgraph_enabled)
- `tests/test_langchain_hardening.py` — 13 hardening tests

## Security Observations
- Feature flags default OFF (NUS_LANGCHAIN_ENABLED=false, NUS_LANGGRAPH_ENABLED=false)
- Public access (no token) returns 0 evidence (no leak)
- Error responses don't expose stack traces
- Session isolation maintained
- No unauthorized access possible via LangGraph path

## Before/After Behavior
- Before: Chat uses HermesAgent.execute_v1() (legacy path)
- After (flags OFF): Same legacy path (no change)
- After (flags ON): LangGraph workflow orchestrates retrieval + generation + citations
- Fallback: LangGraph failure → legacy path (logged as warning)

## Rollback Verification
- Set NUS_LANGGRAPH_ENABLED=false → system reverts to legacy path
- Set NUS_LANGCHAIN_ENABLED=false → adapter returns None
- No data loss, no schema changes, no index changes
- Rollback tested: flags OFF → all 13 tests still pass

## Conclusion
P3 hardening tests: 13/13 PASS. No critical security issues. Legacy behavior preserved. Feature flags default OFF. Ready for operator review.
PY