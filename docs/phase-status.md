# Phase Status — Nusantara Core + Hermes

This repository is a repaired starter implementation based on the supplied 18-phase blueprint.

| Phase | Status | Evidence in repository |
|---|---|---|
| 0 | Implemented | `docs/` architecture/development/roadmap/ADR |
| 1 | Implemented | FastAPI app, config, exceptions, packaging |
| 2 | Implemented | provider abstraction, Ollama, OpenAI-compatible, Mock, router |
| 3 | Implemented | language normalization, intent, entity |
| 4 | Implemented | context/session/builder |
| 5 | Implemented | problem detector/classifier/engine |
| 6 | Implemented | RAG, embeddings, retriever, reranker, parser/chunker compatibility |
| 7 | Implemented | reasoning planner/evaluator/structured artifacts |
| 8 | Implemented | workflow state machine and recovery-oriented API |
| 9 | Implemented | ALLOW/CONFIRM/HUMAN/DENY policy decisions |
| 10 | Implemented | evidence/trust validation |
| 11 | Implemented | TTL/isolation-oriented memory |
| 12 | Implemented | calculator/date-time/file-safe tool layer |
| 13 | Implemented | MCP-compatible local server/session/registration |
| 14 | Implemented | human handoff/escalation |
| 15 | Implemented | FastAPI v1 gateway |
| 16 | Implemented | human-first minimal UI |
| 17 | Scaffolded | 100 scenario records + verification runner; broad statistical evaluation is not claimed |
| 18 | Implemented | Dockerfile/Compose/non-root/read-only API container/health scripts |

## Verification

`python run_tests.py` is the authoritative local verification command in this package.
It checks imports, representative behavior for phases 1–16, 100 evaluation records, and phase-18 deployment files.
It does **not** prove production readiness, security completeness, model accuracy, or performance under load.
