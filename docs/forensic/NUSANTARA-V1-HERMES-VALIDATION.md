# NUSANTARA V1 HERMES VALIDATION

**Contract:** NUS-V1-MASTER-CONTRACT-001
**Date:** 2026-11-17

---

## 1. Hermes Architecture

- **Location:** app/hermes/agent.py
- **Class:** HermesAgent
- **Entry:** execute_v1(request, knowledge, gates, trust, grounding, ...)
- **Provider:** Ollama (gemma3n:e2b) or OpenRouter (if configured)

## 2. Execution Flow

```
User Input → Language Engine → Problem Engine → Knowledge Engine → Deterministic Safety → Hermes → Ollama → Response
```

## 3. Validation Results

### Desktop Execution
- Provider: Ollama (gemma3n:e2b-it-q4_K_M)
- Health check: available
- Generation: works (but answers don't pass grounding)
- Status: PARTIAL

### Browser Execution
- Not tested (no browser automation available)
- Frontend connects to backend via HTTP
- Status: NOT TESTED

### Windows Host
- Backend runs on Windows (port 8000)
- Status: PASS (running)

### Linux/Docker
- Not tested (no VPS available)
- Status: NOT TESTED

## 4. Known Issues

1. Hermes chat abstains on all queries (LLM too small)
2. evidence_fast_path works for some queries (requirements, duration)
3. Source self-validation fixed (prevents dumping source text)
4. Grounding guard correctly rejects ungrounded answers

## 5. Test Results

- test_hermes_v1_conversation: PASS
- test_hermes_v1_arithmetic: PASS
- test_hermes_acp_connection: PASS

---

**Status: PARTIAL (desktop works, browser/Linux/Docker not tested)**
