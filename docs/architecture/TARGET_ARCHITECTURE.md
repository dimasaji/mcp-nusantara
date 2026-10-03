# TARGET_ARCHITECTURE — V2

```
USER → API(/v2) → ORCHESTRATOR → POLICY → MEMORY → UNDERSTAND → RAG/TOOLS(governed) → MODEL → TRUST → VALIDATION → OUTPUT → AUDIT
                                                                                        │
                                             EXPERIENCE → R&D → HUMAN APPROVAL → V2.x  (Phase 10–21, belum dibangun)
```
Prinsip: V2 = V1 + lapisan baru. `/v1` tidak berubah; `/v2` memakai engine V1 lewat adapter (`app/v2/wiring.py`), tanpa engine duplikat.

| Lapisan | Modul V2 | Status |
|---|---|---|
| Hardening | `app/core/hardening/` | EXISTING |
| Observability | `app/observability/` | PARTIAL |
| Approval + audit | `app/approval/` | EXISTING |
| Tool governance + sandbox | `app/governance/` | EXISTING |
| Orchestrator | `app/v2/orchestrator.py` | EXISTING |
| RAG berversi + konflik | `app/rag/` | EXISTING (belum menggantikan `app/knowledge`) |
| MCP terintegrasi | `app/governance/mcp_bridge.py` | PARTIAL |
| Memory governance/episodic/vector | — | PARTIAL / MISSING |
| Experience + Feedback | `app/experience/` | EXISTING |
| Evaluation | `app/evaluation/` | PARTIAL |
| R&D (failure, gap, discovery, experiment, proposal) | `app/research/` | EXISTING (inti) |
| Human approval -> V1.x -> release | `approval/change_request.py`, `app/improvement/` | PARTIAL |
| Security readiness | `app/security/`, `scripts/release_check.py` | PARTIAL |

Alur belajar (tidak ada jalur R&D -> production): events/feedback -> failure analysis -> gap -> discovery (kandidat) -> experiment -> proposal -> **human approval** -> change request -> gate -> tes/evaluasi -> release check -> rilis manual.
