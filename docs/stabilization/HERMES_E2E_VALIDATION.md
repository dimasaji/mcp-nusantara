# HERMES E2E VALIDATION

**Contract:** NUS-V1-REMEDIATION-001
**Date:** 2026-11-17

---

## 1. Hermes Architecture

- Location: app/hermes/agent.py
- Class: HermesAgent
- Entry: execute_v1(request, knowledge, gates, trust, grounding, ...)

## 2. Execution Flow

User Input → Language Engine → Problem Engine → Knowledge Engine → Deterministic Safety → Hermes → Ollama → Response

## 3. Validation Results

### Chat with Gemma 2B
- Evidence fast path: grounded=True (requirements, duration)
- LLM path: abstain (grounded=False, possible_unsupported_content)
- Out-of-scope: abstain (correct)
- Provider status: evidence_fast_path / ollama / local_rule

### Chat with LangGraph (flag ON)
- grounded=True, 5 evidence, answer generated
- Provider: evidence_fast_path

### Multi-turn
- Session isolation: PASS
- Context preservation: PASS

## 4. Known Issues

1. Hermes chat abstains on LLM path (model too small)
2. evidence_fast_path only works for 3/50 documents with "Persyaratan X: Y" format
3. No grounded answer from LLM for any query
4. Fallback self-validation fixed (prevents source dumping)

## 5. Test Results

- test_hermes_v1_conversation: PASS
- test_hermes_v1_arithmetic: PASS
- test_hermes_acp_connection: PASS

---

**Status: PARTIAL (fast path works, LLM path abstains)**
