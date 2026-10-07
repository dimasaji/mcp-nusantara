# MDE-04 Model Registry execution report

2026-10-07. Task MDE-04-20261007. Command found at docs/commands/MDE-04 Model Registry.md. Starting branch codex/fullroot-control-20261007, HEAD d5af020, continuing the verified MDE03 checkpoint.

**Result: DONE_SCOPED_KEEP_WITH_OPEN_LIMITATIONS.** Model identity discovery, canonical interpretation, matrix and path/selection audit are complete. Exactly one decision: KEEP existing structures. No ModelRegistry or implementation change was needed for this discovery/design contract. Runtime identity enforcement and live model verification remain unimplemented/unverified.

## Identity contract and findings

docs/MDE-04_MODEL_REGISTRY_DESIGN.md distinguishes provider ID, provider-scoped model selector, display name, routing model, configured/default model and reported versus actual execution identity. It defines provider_id, model_id, capability, requested_model, selected_model, actual_model and identity_status, with DECLARED/CONFIGURED/SELECTED/EXECUTED/VERIFIED evidence levels. This is an internal evidence design, not new public fields or an implemented receipt/registry class.

Source mapping records 112 model identity sites in actual app Python source and four UI selector/display sites. Names alone are not dataflow/live proof. The UI's llama3.2:1b/qwen3:4b/qwen3:8b options are hardcoded requested selectors, not an installed-model registry. Health badges and response labels are display/configuration observations.

The audit covers FAST, KNOWLEDGE, TOOL, OFFLINE, V2 generation, gateway and router. Important limits:

- V1 local_rule, evidence_fast_path and offline branches report configured provider.model without generation. Current deterministic helper always returns None; the local-rule branch is dormant/test-double coverage, not an active live path.
- V1 generated output also labels model from provider.model rather than reconcile response.model. Raw upstream model labels are ignored by HTTP adapters.
- V2 callbacks return text and public V2 chat response lacks dedicated model identity; identity cannot be reconstructed from response text.
- Tools produce tool receipts, not model receipts. DevCore audit can record configured model_name even when generate=None and analysis uses static facts.
- Actual router ModelSelection differs from the exported schema compatibility class. Selection captures a model label, but provider remains mutable; earlier selection can become stale. Gateway select and a later generate are not an atomic immutable receipt.

The six MDE-03 mismatches are mapped to their existing asserted evidence: alias Mock metadata, mutable identity, registration-key drift, self.model versus server identity, gateway accepting foreign model, and openai_compatible versus preferred openai naming. They remain implementation limits; their interpretation is closed without claiming the runtime defects were repaired. selected_model is never treated as actual_model without corresponding execution evidence. Successful synthetic method execution remains fixture-scoped, not live neural model verification.

Registered-provider fallback selects an already registered provider when preferred entries are absent; it is not invocation failover. No fallback priority, model selector, constructor default/snapshot semantics or public behavior changed. No new registry, gateway startup activation, Core Agent, model install/download, dependency, live provider/cloud call, RAG/index/database/schema or Trust/Policy/Security change.

## Verification

| Evidence | Result |
| --- | --- |
| MDE03 checkpoint preflight | All 268 hashes matched; source build unchanged |
| Fresh existing router/gateway/V1 projection/V2 tests | 71 passed; 0 failure/error/skip; 1.56s |
| New isolated observations | 8 assertions passed: selected without generate, stale selection after mutation, distinct selection types, no base request model selector, extra request model does not switch mock, text callback lacks identity, TOOL/static without LLM, configured DevCore audit label without generation |
| MDE03 identity/fallback evidence reuse | 22 observations retained; evidence hashes verified, not reported as new tests |
| Source/test/control byte integrity | 249 hashes unchanged; no new app/test source |
| Production database byte integrity | 9 files unchanged; no model/index migration |
| Full regression | MDE02 baseline reused: 380 passed, 28 passing subtests, one known Windows skip. Not a fresh MDE04 full run; source-change condition did not trigger. JUnit hash verified. |
| Git review | Exact task-owned files selected; whitespace check passed; inherited source changes retained |

The new isolated observations stub Settings in-process and use temporary workspace/audit files; no repository dotenv or live provider call. Existing focused tests use their supplied fixtures. Current source identity remains sha256:920ad1d01be7c574ea0e5198fd306d27383c9490bb9ef40c7a821ddbcb9be976. Existing TestClient/httpx deprecation warning remains. No test added/changed/weakened. No code edit, therefore no graph rebuild; graph was queried for navigation and source inspected directly, without claiming new docs were semantically indexed.

## Completion, remaining work and rollback

Required design, PROJECT_STATE, TASKS, DECISIONS, execution report and MDE04 checkpoint are updated. Discovery/design closure means the fields/path ambiguities are documented and the KEEP decision verified. It does not close universal identity enforcement, immutable selection receipts, actual server/weights identity, capability verification, default gateway/executor/snapshot adoption or deployed unified four-path behavior.

Configuration Architecture remains NOT_COMPLETE; Nusantara V1 remains FAIL/HOLD due to existing acceptance/compliance/oracle/symlink/deployment gates and the explicit runtime limits. No Level C action was needed/performed for KEEP. Stop after MDE-04; MDE-05 was not started.

Checkpoint: .dev/MDE04_CHECKPOINT.json. Git artifact commit and source/evidence hashes are recorded there. Rollback: restore only previous state/task/decision files from .dev/checkpoints/mde04-20261007/ and selectively remove new MDE04 artifacts. No application/index restore needed; never reset inherited dirty work. Resume by checking this checkpoint and reuse completed discovery evidence without repeating prior tasks.
