# HDG-R2-A9-AUTH-001 — Discovery

Date: 2026-10-08. Authorization: DISCOVERY/DESIGN ONLY, from the human decision in this conversation. Documentation is the deliverable; no executable/source/UI/configuration modification is authorized. Parent contract: `docs/commands/NUSANTARA R2-A9.md`. Previous R2-A9 preflight remains BLOCKED.

Repository: C:\Users\dmaza\mcp-starter. Branch: codex/fullroot-control-20261007. HEAD: 8f86bed38aca8e6b5a0bd365f3351ac9c0825eab. Existing dirty worktree retained. GIT_DISCOVERY.txt captures available status; Git could not inventory five inherited reports directories. No cleanup or permission repair attempted.

Graphify query used existing graph (8970 nodes), returned a truncated scoped subgraph; source inspection resolved the relevant paths. No graph rebuild/update was executed.

| Owner | Observed source behavior | Design consequence |
|---|---|---|
| app/security/auth.py | Shared NUSANTARA_ADMIN_TOKEN, constant-time comparison; absent/wrong token fails closed | Proves shared credential possession, not individual operator identity or browser session |
| app/api/v2_routes.py | Decision reviewer comes from body; module owns durable audit and constructs KnowledgeEngine | Do not import as an ATTESTATION audit factory; leave v2 unchanged |
| app/approval/audit_trail.py | Existing hash-chain/redacted audit, memory when path=None, JSONL when path supplied | Reuse class without a second audit implementation or production sink |
| app/approval/queue.py | Payload digest, expiry, snapshots, reviewer/requester inequality, one-use consume | Reuse as approval engine, behind trusted actor and immutable binding adapter |
| app/core/runtime_correlation.py | Process-bound permit; grant once; reserve before await; one transport dispatch | Add a future terminal abort operation; current finish() does not invalidate ARMED |
| app/api/runtime_verification.py | Fixed diagnostic input, existing real Ollama provider, no retries/fallback; injected strict transport | Bridge directly to controller; never pass internal bearer permit through browser or self-HTTP |
| app/core/runtime_attestation.py | Process metadata plus registered/scoped code manifest; no full-build verification | Preserve scope labels and include future governance helper code in scoped coverage |
| app/main.py | NORMAL imports full APIs/audit/KnowledgeEngine; ATTESTATION omits them | Compose new owner only in ATTESTATION, after controller exists and before scoped manifest freezes |
| Control Plane | Session-only decisions, historical projection, GET client | Browser cannot establish reviewer, authorization or runtime proof |
| control-plane/vite.config.ts | 5173 proxies /v1/control-plane to 8000 | 5173 is UI origin only, never runtime target; no proxy/CORS change in this task |

No inspected security/approval path establishes an authenticated individual/session from a browser. Observability session_id is correlation metadata, not authentication. Existing ctypes process metadata use does not establish operator identity. Proposed Windows actor adapter is new integration, not an existing verified capability.

Lifecycle scripts were read as text only; they can start Ollama/service or stop processes, so none was run. Live PID 32796, its current state and loaded code were not probed. No protected runtime files, production audit file, environment secrets or database/sidecars were opened or hashed.
