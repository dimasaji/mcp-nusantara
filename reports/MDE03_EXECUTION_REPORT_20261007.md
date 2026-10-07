# MDE-03 Provider Registry execution report

2026-10-07. Task MDE-03-20261007. Command located at docs/commands/MDE-03 Provider Registry.md; requested docs-root name is not present. Start branch codex/fullroot-control-20261007, HEAD fa4cd8f, continuing .dev/MDE02_CHECKPOINT.json.

**Status: DONE_SCOPED_KEEP_WITH_OPEN_LIMITATIONS.** Required provider discovery, matrix, selection/registration contract and decision are complete. This is not universal identity enforcement or live provider certification. No application/test/dependency source changed and no ProviderRegistry class was created. Stop after MDE-03; MDE-04 not started.

## Findings and decision

ModelRouter._providers already owns the local instance registry. Provider names are dictionary keys; explicit register stores objects, duplicate IDs replace prior entries, and first registration order affects generic fallback. Hermes registers its injected/default provider. ModelGateway delegates selection and sync/async generation to this router without default discovery, identity reconciliation, health gating or failover.

Concrete LLM providers: Ollama, OpenAI-compatible and Mock. Compatibility modules re-export existing classes. ProviderConfig/Pydantic schemas and a structural protocol are declarations/interfaces, not provider factories. Existing router ModelSelection and separately exported schema ModelSelection differ. Generation callbacks in V2 and DevCore are injected by callers. Separate embedding/service/factory and legacy LLMReranker abstractions are recorded without activating them or changing the index. Current source navigation covers 19 relevant app modules, plus app/tests/scripts/root registration searches; five test-only provider classes were recorded and no dedicated TestProvider class found.

The 12-column provider matrix, dependency graph and per-branch selection contract are in docs/MDE-03_PROVIDER_REGISTRY_DESIGN.md. CONFIGURED, REGISTERED and RUNTIME VERIFIED are distinct. Settings.llm_provider is not an active factory switch; default API explicitly constructs Ollama. No real OpenAI/Anthropic/cloud availability claim follows from an adapter class or model label.

**Universal routing/response identity consistency is false/not enforced.** Counterexamples are recorded rather than hidden:

- Aliased MockProvider selection reports openai/cloud-fixture but generates hardcoded mock/mock-model metadata.
- Mutable identity can diverge from captured dictionary keys or a prior ModelSelection.
- HTTP adapters emit configured self.model rather than validate upstream model identity; returned metadata does not prove server execution identity.
- Gateway accepts a text-bearing response reporting a different model.

Stable native/mock fixture paths retain FULLROOT's provider.model repair, coding/reasoning registered fallback and sync/async gateway compatibility. Native openai_compatible differs from the router's preferred openai ID. Selecting a registered alternative is different from trying another provider after generation failure: the latter is not implemented. V2 degraded fallback is response degradation and did not invoke the backup fixture provider. Inherited capability metadata and assumed JSON-schema support are not empirical capability selection. Mock structured/health/sync signatures differ from the async/base TypedDict contract.

KEEP is sufficient for this discovery/contract task and avoids a second registry or silently changed duplicate/identity/preference behavior. Known limits remain open. There is no PATCH/REFACTOR/MIGRATION/REPLACEMENT/REBUILD and no Level C action needing approval in this scope.

## Verification executed

| Evidence | Result |
| --- | --- |
| Prior MDE-02 checkpoint verification before changes | 273 source/database/evidence hashes matched; source build unchanged |
| Provider/router/gateway baseline and focused existing tests | 38 passed; 0 failure/error/skip; 0.96s |
| Additional isolated assertions | 22 asserted observations passed, including identity counterexamples, duplicate/mutable ID, unavailable fixture selection, native compatible preference, eight Ollama payload branches, compatible payload/health fixtures, no generation failover, V2 degradation, sync/async and protocol variance |
| Actual service/cloud/model health | NOT_RUN; only MockTransport/synthetic fixture health |
| Runtime/test/control source integrity | 249 hashes unchanged; no new app/test source |
| Production database file byte integrity | 9 hashes unchanged; no migration/schema/index writes |
| Full regression | Reused verified MDE-02 evidence: 380 passed, 28 passing subtests, 1 known Windows skip. Not rerun in MDE-03 because source did not change; command requires full rerun on source change. |
| Git diff | Only task-owned design/report/evidence/state/checkpoint selected; whitespace review passed; inherited working tree retained |

Observations used explicit isolated Settings stubbing, synthetic credentials and in-process MockTransport. No repository dotenv was read by that probe, no live provider contacted, no real failover, worker start, dependency install, restart or deployment performed. Current health evidence is fixture-scoped. The 38 existing tests include config handoff and existing gateway/executor boundaries; previous public behavior remains protected by unchanged byte hashes and the MDE-02 full regression.

Source build remains sha256:920ad1d01be7c574ea0e5198fd306d27383c9490bb9ef40c7a821ddbcb9be976. No graph rebuild is needed: no implementation/test code changed; the existing graph was queried for discovery and current source was inspected directly. Documentation changes are not presented as regenerated semantic graph knowledge.

## State, remaining issues and rollback

PROJECT_STATE, TASKS and DECISIONS record the scoped KEEP decision and the open identity/capability limits. Required checkpoint .dev/MDE03_CHECKPOINT.json contains Git identity, source/evidence hashes, matrix/design references, tests, regression reuse, compatibility findings and rollback location.

Open: universal provider/response identity enforcement, immutable registration semantics, native compatible preference naming, capability negotiation, live provider/worker/index verification, default gateway/executor/snapshot adoption, existing oracle/symlink/compliance/deployment gates. Configuration Architecture remains NOT_COMPLETE; global V1 remains FAIL/HOLD. These are not silently completed by the registry documentation.

Rollback restores only prior state/task/decision files from .dev/checkpoints/mde03-20261007/ and removes new task-owned design/report/evidence/checkpoint selectively. No application/index rollback is needed; do not reset or clean inherited changes. Resume by checking MDE03 hashes; do not repeat completed MDE-02/MDE-03 discovery merely because execution continues. Do not start MDE-04 without a new instruction.
