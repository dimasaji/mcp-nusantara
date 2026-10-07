# Nusantara repository map

Updated 2026-10-07. Existing repository retained; no replacement V1.

| Area | Role / evidence |
| --- | --- |
| developer.py | Local control entrypoint; inspect/inventory/status/health/test/architecture-check/cleanup --dry-run/validate/report |
| app/main.py, app/api/routes.py, app/api/v2_routes.py | Existing API entrypoints and response contracts; no wiring/schema edits in FULLROOT task |
| app/v2/orchestrator.py | Existing policy/trust/context budget/stage failure orchestration; callback injection retained |
| app/context/context_builder.py | Existing bounded context construction; existing tests preserved |
| app/models | Existing providers/router; gateway.py bridges sync/async generation using existing router |
| app/execution | Optional structural tool/agent contracts; native adapter delegates to governed registry |
| app/v2/hermes_adapter.py | Existing optional Hermes adapter; structural protocol test uses injected fixture, not worker |
| app/knowledge, app/rag | Existing canonical/production/experimental RAG implementations; ownership/behavior differences remain documented |
| app/governance, app/policy, app/trust | Existing authoritative governance; no policy edits or generic shell tools added |
| scripts/nusantara_master_engine.py | Existing broader engineering engine preserved; not run in --apply or provider mode |
| scripts/release_check.py | Existing readiness engine; not overwritten by control static validation |
| tests | Existing contracts/behavior plus new control/router/boundary tests |
| .dev | Scoped inventory, test evidence, state/tasks/decisions, recovery checkpoint |
| graphify-out | AST knowledge graph; clustering/wiki/report may be older than current no-cluster graph |
| data, nusantara-models | Persistent data/model assets excluded from control content inspection |
| archive, backup, integration, app_backup_* | Historical/experimental candidates; UNKNOWN retained pending actual dependency/recoverability proof |

.dev/repo_inventory.json contains source/import/hash metadata. KEEP means preserve, not verified runtime authority. Duplicate hashes and filename suffixes do not authorize deletion. Dynamic/external imports and storage assets remain scoped limits. .env contents are never inspected by developer.py.
