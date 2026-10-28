# Nusantara Master Backlog Audit

- Generated: 2026-10-09T20:48:36.4815002+07:00
- Repository: `C:\users\dmaza\mcp-starter`
- Mode: AUDIT ONLY
- V1 acceptance: HOLD pending closure evidence
- V2: DEFERRED

## Git inventory
- Untracked files: 241
- Other reported changes: 42

## Runtime HTTP checks
| Path | Status | HTTP | HTML length |
|---|---|---:|---:|
| /health | HTTP_RESPONSE_RECEIVED | 200 | 118 |
| / | HTTP_RESPONSE_RECEIVED | 200 | 363 |
| /ui | HTTP_RESPONSE_RECEIVED | 200 | 363 |

## Frontend assets
- HTTP_RESPONSE_RECEIVED HTTP 200: http://127.0.0.1:8000/assets/index-DWlaYDof.js (text/javascript; charset=utf-8)
- HTTP_RESPONSE_RECEIVED HTTP 200: http://127.0.0.1:8000/assets/index-CmsA6OFH.css (text/css; charset=utf-8)

## Important file inventory
| File | Exists | Bytes | Last write |
|---|---|---:|---|
| app/main.py | True | 5011 | 2026-10-09 09:37:10 |
| app/api/routes.py | True | 34837 | 2026-10-09 19:00:56 |
| app/ui/index.html | True | 61330 | 2026-10-09 20:35:37 |
| control-plane/src/router.tsx | True | 2373 | 2026-10-09 08:56:14 |
| control-plane/src/api.ts | True | 10239 | 2026-10-09 13:11:32 |
| app/knowledge/web_evidence.py | True | 38261 | 2026-10-09 18:33:40 |
| app/mcp/stdio_server.py | True | 1684 | 2026-10-06 09:40:25 |
| app/models/openrouter.py | True | 8206 | 2026-10-09 18:56:28 |
| app/security/local_operator.py | True | 19255 | 2026-10-08 12:09:02 |
| app/workflow/v1_langgraph.py | True | 6516 | 2026-10-09 20:28:48 |
| docs/contracts/NUSANTARA-RUNTIME-EXECUTION-CONTRACT-V1.md | True | 2306 | 2026-10-06 16:44:29 |
| docs/contracts/NUSANTARA-INTELLIGENCE-MODEL-CONTRACT-V1.md | True | 2231 | 2026-10-06 16:44:29 |
| docs/contracts/NUSANTARA-KNOWLEDGE-RAG-CONTRACT-V1.md | True | 2374 | 2026-10-06 16:44:29 |
| docs/contracts/NUSANTARA-AGENT-ORCHESTRATION-CONTRACT-V1.md | True | 2604 | 2026-10-06 16:44:29 |
| docs/contracts/NUSANTARA-TOOL-MCP-API-CONTRACT-V1.md | True | 2309 | 2026-10-06 16:44:29 |
| docs/contracts/NUSANTARA-TRUST-POLICY-APPROVAL-CONTRACT-V1.md | True | 2573 | 2026-10-06 16:44:29 |
| reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md | True | 9928 | 2026-10-06 16:48:49 |
| reports/NUSANTARA-V1-CONTRACT-COMPLIANCE-2026-10-06.md | True | 19514 | 2026-10-06 17:01:32 |
| reports/V1_RECOVERY_ORACLE_AUDIT_20261009.json | False |  |  |
| tests/test_hermes_v1_conversation.py | True | 8780 | 2026-10-09 20:35:58 |

## Known backlog — not automatically verified
| ID | Priority | Status | Task |
|---|---|---|---|
| UI-001 | HIGH | REPORTED_OPEN | Tambahkan alias frontend /ui ke komponen Asisten yang sama dengan / |
| UI-002 | HIGH | NOT_RUN_REPORTED | Verifikasi render browser dan pengiriman chat nyata ke /v1/chat |
| MEM-001 | MEDIUM | NOT_VERIFIED_REPORTED | Atribusikan penyebab WinError 5 pada kegagalan tes memory historis |
| V1-001 | BLOCKING | OPEN_REPORTED | Tutup gate security yang masih SKIP atau belum diverifikasi |
| V1-002 | BLOCKING | OPEN_REPORTED | Selesaikan kasus oracle REVIEW_REQUIRED dan MISSING |
| V1-003 | BLOCKING | NOT_RUN_REPORTED | Lakukan verifikasi deployment/container yang belum dijalankan |
| CC-01 | HIGH | OPEN_REPORTED | Tinjau kebocoran internal gate_pipeline di respons publik |
| CC-05 | HIGH | OPEN_REPORTED | Tinjau kelengkapan governance memory |
| CC-06 | HIGH | OPEN_REPORTED | Tutup gap knowledge/RAG, oracle, security, dan deployment |
| V1-004 | HIGH | REVIEW_REQUIRED_REPORTED | Tinjau filter knowledge dan perilaku reranking RAG |
| REL-001 | HIGH | NOT_VERIFIED_REPORTED | Verifikasi identitas runtime terhadap source terbaru |

## Safety
This script performs GET requests and read-only inventory checks. It does not run tests, modify source, change databases, restart services, install dependencies, or perform destructive Git operations.

A successful HTTP response does not prove browser rendering, chat success, or V1 acceptance.

Historical backlog statuses must be revalidated before any item is closed.
