# RELEASE READINESS REPORT - Nusantara V1

Date: 2026-11-17
Branch: codex/fullroot-control-20261007
Status: PARTIAL

## 1. Runtime Evidence

Services: Backend(8000) RUNNING, Frontend(5180) RUNNING, Ollama(11434) RUNNING
Model: gemma3n:e2b-it-q4_K_M (2B, 7.8 GB)
Database: 64 documents, 721 chunks, 719 events, 44 SOP Aktif, 1 Ditolak
Backup: SHA-256 verified, restore tested
Tests: 49 passed (40 existing + 9 new), Security 6/6 PASS, Runtime fixture 1/1 PASS

## 2. Metrics

Search: Recall@5=0.8278, MRR@10=0.5672, P@1=0.4667, P@5=0.3478
Chat: LangGraph grounded=True, Hermes abstain, Evidence fast path 3/50 docs
Performance: 2 SOP=132.3s (avg 66.1s), Search=192ms, Chat=5-52s
OCR: 44 SOPs (38 scanned, 4 digital, 2 test), Grid=19.4%, CER=27-51%

## 3. Security

14 controls implemented. 6/6 security tests PASS.
Known gaps: no penetration test, shared admin token, no Docker isolation test.

## 4. Architecture

Backend: FastAPI, SQLite, IndoBERT(768D), Ollama, Haystack, Docling
Frontend: React/Vite
Pipeline: Upload -> Processing -> Review -> Approve -> Knowledge Active
is_pilot: only gates PDF documents. Rate limiting: 30 req/60s.

## 5. Deliverables

Remediation: 12 files. Forensic: 8 files. Other: REMAINING_WORK.md, RELEASE_READINESS_REPORT.md

## 6. Blockers for 100%

1. Chat answer quality: needs 7B+ model
2. OCR ground truth: needs manual transcription
3. Security penetration test: no tools
4. Docker build: daemon not running
5. Linux validation: on Windows
6. Load test: no infrastructure
7. Model download: no internet

## 7. Verdict

V1 Status: PARTIAL
Core: WORKING. Search: GOOD. Chat: PARTIAL. Security: BASIC. Performance: DOCUMENTED. Deployment: NOT READY.
Estimated: 50% (28/56 items). Remaining blockers need external resources.
