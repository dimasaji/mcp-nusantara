# V1 architecture gaps

Updated 2026-10-07. Configuration DoD NOT_COMPLETE; V1 FAIL/HOLD.

| Gap | Evidence / next work |
| --- | --- |
| Composition root/default startup | Snapshot opt-in; design Settings/ENV/explicit/request precedence before API wiring. Preserve public constructors and CC01 projection. |
| Provider capabilities | Ollama implementation and OpenAI-compatible adapter source exist; actual cloud capability/credentials/health NOT_PROVEN. No OpenAI/Anthropic availability claim. |
| Gateway/executor runtime activation | Optional adapters exist and integrate in isolated V2 fixtures; default API wiring unchanged. |
| Four paths | Local tests cover generation, retrieval, tool execution/denial and degraded fallback separately. Unified deployed FAST/KNOWLEDGE/TOOL/OFFLINE behavior NOT_PROVEN. |
| RAG weights/threshold/reranker | Canonical/production semantics differ; cutoff and named fallback reranker not fully configuration-driven. Behavioral migration contract required. |
| Embedding/index | Fixed IndoBERT base-p1/768 profile; stored index metadata compatibility NOT_PROVEN. No production DB opened for audit. |
| Runtime controls/features | Schema declarations not actual service effective values/enforcement. |
| Oracle | Two official snapshots require authoritative review; one required evidence remains missing. Do not change expected answers to pass. |
| Windows symlink | Existing mandatory security gate skipped without privilege; owner-controlled eligible runner needed, no OS changes made. |
| Deployment | Production deployment/restart/workload/rollback not executed; target and authorization required. |
| Compliance | Existing CC02–06 gaps remain; contract/acceptance artifacts not edited. |
| Cleanup | Exact duplicates/historical snapshots listed by dry-run. UNKNOWN retained; no bulk archive/deletion. |
| Diagnostics limits | Static validate proves parsing/absolute app imports/installed packages only; no dynamic/circular-import execution or model health certification. |

V1 cannot be marked DONE based solely on static controls or passing unit tests. Relevant source/test baseline and scoped final regression evidence are recorded in .dev/PROJECT_STATE.json and reports/FULLROOT_*.
